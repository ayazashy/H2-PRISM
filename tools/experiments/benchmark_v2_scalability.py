#!/usr/bin/env python3
"""
Computational scalability of Distinguishability v2 on SYNTHETIC data (no real data, no model training).

Varies reference size (windows), number of independent groups, number of hypotheses (classes) and feature dimension;
records fit time, compute time per query and peak traced memory. Purpose: the runtime/memory part of the
generalization and scalability plan (02_methodology/MULTICLASS_SIMULATION_DESIGN.md section 6). Absolute times are
machine-dependent; the fitted exponents (time ~ N_ref^a) are the reported quantity.
Writes 03_results/diagnostics/distinguishability_v2/SCALABILITY_SYNTHETIC.csv.
Usage: python tools/experiments/benchmark_v2_scalability.py
"""

from __future__ import annotations

import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.distinguishability_v2 import DistinguishabilityV2, V2Config  # noqa: E402

OUT = REPO / "03_results" / "diagnostics" / "distinguishability_v2" / "SCALABILITY_SYNTHETIC.csv"


def make(n_groups, windows_per_group, n_classes, p, seed=0):
    rng = np.random.default_rng(seed)
    X, y, g, t = [], [], [], []
    for i in range(n_groups):
        c = i % n_classes
        ctr = rng.normal(c * 3.0, 1.0, p)
        X.append(ctr + rng.normal(0, 0.5, (windows_per_group, p)))
        y += [f"C{c}"] * windows_per_group
        g += [f"G{i}"] * windows_per_group
        t += list(np.arange(windows_per_group) * 30.0)
    return np.vstack(X), np.array(y, object), np.array(g, object), np.array(t), [f"C{c}" for c in range(n_classes)]


def run(n_groups, wpg, n_classes, p, n_query=200):
    X, y, g, t, cls = make(n_groups, wpg, n_classes, p)
    tracemalloc.start()
    t0 = time.perf_counter()
    m = DistinguishabilityV2(V2Config()).fit(X, y, g, t, cls)
    t1 = time.perf_counter()
    Q = X[np.random.default_rng(1).choice(len(X), n_query, replace=False)] + 0.1
    m.compute(Q, ["NEW"] * n_query)
    t2 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"n_groups": n_groups, "windows_per_group": wpg, "n_reference_windows": len(X), "n_classes": n_classes,
            "n_features": p, "n_query": n_query, "fit_s": t1 - t0, "compute_s_per_query": (t2 - t1) / n_query,
            "peak_traced_MB": peak / 2 ** 20}


def main() -> int:
    rows = []
    for n_groups in (12, 24, 48):                      # reference size via independent groups (60 windows each)
        rows.append({**run(n_groups, 60, 4, 96), "axis": "reference_groups"})
    for wpg in (30, 120, 240):                         # reference size via windows per group (24 groups)
        rows.append({**run(24, wpg, 4, 96), "axis": "windows_per_group"})
    for n_classes in (2, 4, 8):                        # number of hypotheses (24 groups)
        rows.append({**run(24, 60, n_classes, 96), "axis": "hypotheses"})
    for p in (24, 96, 384):                            # feature dimension
        rows.append({**run(24, 60, 4, p), "axis": "features"})
    R = pd.DataFrame(rows).assign(evidence_status="SYNTHETIC_BENCHMARK")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT, index=False, lineterminator="\n", float_format="%.5g")
    for ax, gr in R.groupby("axis"):
        x = {"reference_groups": "n_reference_windows", "windows_per_group": "n_reference_windows",
             "hypotheses": "n_classes", "features": "n_features"}[ax]
        a_fit = np.polyfit(np.log(gr[x]), np.log(gr.fit_s), 1)[0]
        a_q = np.polyfit(np.log(gr[x]), np.log(gr.compute_s_per_query), 1)[0]
        print(f"{ax:18s} fit time ~ {x}^{a_fit:.2f}; per-query time ~ {x}^{a_q:.2f}; peak MB {gr.peak_traced_MB.max():.0f}")
    print(R.drop(columns=["evidence_status"]).round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
