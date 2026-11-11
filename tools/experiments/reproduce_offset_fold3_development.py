#!/usr/bin/env python3
"""
Development-only reproduction of the offset_invariant_features fold-3 stop (DIAGNOSTIC; no outer-test data used).

The registered run SENSITIVITY_offset_invariant_features (run_key ff9cc78ab2ca) stopped in fold 3 (Upstream held out)
with "development data contain a single correctness outcome; meta-model not estimable". This script mirrors
primary_protocol.development_stage for that fold (offset-invariant statistics only; development = Center + Downstream)
up to the correctness vector that the combined-score meta-model receives, and writes the out-of-fold confusion.

Usage: python tools/experiments/reproduce_offset_fold3_development.py [--out 03_results/diagnostics/forensics]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.baseline import GroupedRunConfig, make_random_forest, select_on_development  # noqa: E402
from h2prism.calibration import calibration_feasibility, fit_calibrator, select_calibration  # noqa: E402
from h2prism.experiments import primary_protocol as pp  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-parent", type=Path, default=REPO / "data" / "raw")
    ap.add_argument("--out", type=Path, default=REPO / "03_results" / "diagnostics" / "forensics")
    a = ap.parse_args(argv)
    base = yaml.safe_load((REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))
    cfg = pp.apply_sensitivity(base, "offset_invariant_features")
    ft, _ = pp.build_features(base, REPO, a.raw_parent.resolve(), "noise_added")  # same windows; columns subset below
    stats = cfg["features"]["statistics"]
    feats = [c for c in pp.model_feature_columns(ft) if c.split("__")[1] in stats]
    dev = ft[ft.topology != "Upstream"].copy()
    classes = list(cfg["dataset"]["classes"])
    topo = dev.topology.to_numpy()
    X, y = dev[feats].to_numpy(float), dev.label_mapped.to_numpy()
    yidx = np.array([classes.index(v) for v in y])
    n_t = len(set(topo))
    rcfg = GroupedRunConfig(classes=classes, param_grid=pp._grid(cfg), inner_n_splits=n_t, seed=int(cfg["seeds"]["global"]),
                            model_name="random_forest_primary", independence_col="topology")
    _, params, P_oof, _ = select_on_development(X, y, topo, make_random_forest, rcfg)
    feas = calibration_feasibility(yidx, topo, len(classes), int(cfg["calibration"]["feasibility_rule"]["min_groups_per_class"]))
    methods = [m for m in cfg["calibration"]["candidates"] if m in feas["allowed_methods"]]
    cal = select_calibration(P_oof, yidx, topo, len(classes), n_splits=n_t, criterion=cfg["calibration"]["criterion"],
                             methods=methods)["selected_method"]
    P_cal = np.zeros_like(P_oof)
    for t in sorted(set(topo)):
        m = topo == t
        P_cal[m] = fit_calibrator(cal, P_oof[~m], yidx[~m], len(classes)).transform(P_oof[m])
    pred = np.array(classes)[P_cal.argmax(1)]
    correct = pred == y
    a.out.mkdir(parents=True, exist_ok=True)
    ct = pd.crosstab([dev.topology, dev.label_mapped], pred).reset_index()
    ct.insert(0, "analysis", f"offset_invariant_features fold 3 development (Center+Downstream), out-of-fold, calibration {cal}")
    ct.to_csv(a.out / "offset_fold3_development_reproduction.csv", index=False, lineterminator="\n")
    res = {"n_features": len(feats), "params": params, "calibration": cal, "n_development": int(len(y)),
           "n_correct": int(correct.sum()), "single_correctness_outcome": bool(len(set(correct.tolist())) < 2)}
    (a.out / "offset_fold3_development_reproduction.json").write_text(json.dumps(res, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(res, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
