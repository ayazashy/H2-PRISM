"""SYNTHETIC sensor-fault and timestamp-jitter stress study on the Center formal D(Y) (H4; not field evidence).

Perturbations are applied to the OBSERVED matched-residual window only; templates, bounds and engine are frozen.
Magnitudes are multiples of the declared observation half-width eps_obs of the channel kind (so they are meaningful
relative to the bounds, not physical sensor specifications):
  bias  +k*eps_obs (k = 0.5, 2, 10)      drift  linear 0 -> k*eps_obs over the window (k = 0.5, 2, 10)
  stuck hold the first sample            noise  Gaussian sigma = k*eps_obs (k = 0.5, 2), seed 20261118
applied to one channel at a time: MFS3 (SID 213 branch meter), PS1 (junction), PS4 (SID 215 branch).
Jitter: each sample replaced by the neighbouring recorded sample with probability p (p = 0.2, 0.5; offsets +/-1 sample
= +/-0.2 s), nominal timestamps kept; 3 seeds. Scenarios S4 and REF; restricted universe; tau = 1 s; 6 queries.
Usage: python dy_stress.py --workspace <Center workspace> [--workers 7]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

V2 = Path(__file__).resolve().parents[2]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "03_results/integrated_validation_v1/advanced_validation/scripts"))
import av_dy_experiments as ax  # noqa: E402
from h2prism import center_enhancement as ce  # noqa: E402
from h2prism.certified_evidence import diagnose  # noqa: E402

SEED = 20261118
NAMES = ("PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "PS7", "PS8", "PS9", "PS10", "MFS1", "MFS2", "MFS3")


def perturb(window, kinds, task, eps_obs):
    w = window.copy()
    if task["fault"] == "jitter":
        rng = np.random.default_rng(task["seed"])
        n = w.shape[0]
        off = rng.choice([-1, 1], size=n) * (rng.random(n) < task["level"])
        idx = np.clip(np.arange(n) + off, 0, n - 1)
        return w[idx]
    c = NAMES.index(task["channel"])
    e = eps_obs[kinds[c]]
    if task["fault"] == "bias":
        w[:, c] += task["level"] * e
    elif task["fault"] == "drift":
        w[:, c] += np.linspace(0, task["level"] * e, w.shape[0])
    elif task["fault"] == "stuck":
        w[:, c] = w[0, c]
    elif task["fault"] == "noise":
        w[:, c] += np.random.default_rng(task["seed"]).normal(scale=task["level"] * e, size=w.shape[0])
    return w


def run(task):
    d = ax._D
    idx = np.arange(13)
    p, f = ax.LADDER[task["scenario"]]
    eps = {"pressure": p, "mass_flow": f}
    eo = {k: v * 0.5 for k, v in eps.items()}
    em = {k: eps[k] - eo[k] for k in eps}
    meas = ax.measurement(d, task["query"], idx, eo, 0)
    if task["fault"] != "none":
        vals, j = d.queries[task["query"]]
        win = perturb(vals[j:j + ce.N].copy(), d.kinds, task, eo)
        chans = tuple(type(c)(c.sensor_id, c.unit, c.timestamps_s, c.timestamp_source, tuple(float(x) for x in win[:, k]),
                              c.absolute_errors) for k, c in enumerate(meas.channels))
        meas = type(meas)(meas.sensors, meas.timestamps_s, chans, meas.run_id + f" [{task['fault']}]", meas.independence_group,
                          meas.source_id, meas.uncertainty_basis + "; SYNTHETIC perturbation", meas.cadence_tolerance_s)
    models = ce.dy_models(d, task["query"], idx, em, 1.0, "restricted")
    dec = diagnose(meas, models)
    truth = ce.DY_TRUE[task["query"]]
    cert = dec.certificate
    if dec.status.value == "SPECIFIC":
        out = "SPECIFIC_CORRECT" if dec.hypothesis == truth else "SPECIFIC_WRONG"
    elif dec.status.value == "AMBIGUOUS":
        out = "AMBIGUOUS_TRUTH_IN" if truth in cert.feasible else "AMBIGUOUS_TRUTH_OUT"
    else:
        out = f"UNRESOLVED_{dec.reason}"
    return {**task, "decision": dec.status.value, "selected": dec.hypothesis or "", "outcome": out,
            "truth_retained": truth in cert.feasible or truth in cert.indeterminate}


def tasks():
    T = []
    for q in ce.DY_QUERIES:
        for s in ("S4", "REF"):
            T.append(dict(query=q, scenario=s, fault="none", channel="", level=0.0, seed=0))
            for ch in ("MFS3", "PS1", "PS4"):
                for fault, levels in (("bias", (0.5, 2, 10)), ("drift", (0.5, 2, 10)), ("stuck", (0,)), ("noise", (0.5, 2))):
                    for lv in levels:
                        T.append(dict(query=q, scenario=s, fault=fault, channel=ch, level=float(lv), seed=SEED))
            for p in (0.2, 0.5):
                for sd in range(3):
                    T.append(dict(query=q, scenario=s, fault="jitter", channel="all", level=p, seed=SEED + sd))
    return T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    ap.add_argument("--workers", type=int, default=7)
    a = ap.parse_args()
    T = tasks()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(a.workers, initializer=ax._init, initargs=(a.workspace,)) as ex:
        rows = list(ex.map(run, T, chunksize=4))
    df = pd.DataFrame(rows)
    out = V2 / "04_results/analysis"
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "s1_dy_synthetic_stress_runs.csv", index=False, lineterminator="\n")
    s = df.groupby(["fault", "channel", "level"]).outcome.value_counts().unstack(fill_value=0).reset_index()
    s.to_csv(out / "s1_dy_synthetic_stress_summary.csv", index=False, lineterminator="\n")
    print(len(df), "decisions", round(time.perf_counter() - t0, 1), "s")
    print(s.to_string())


if __name__ == "__main__":
    main()
