#!/usr/bin/env python3
"""Compact cross-run summary of recorded primary-protocol runs (read-only).

For every run directory under 03_results/primary_protocol (PRIMARY, ROBUSTNESS_*, SENSITIVITY_*; not the archive):
run status, classifier accuracy per held-out topology, maximum attainable coverage per fold (primary policy),
the registered pooled RQ1 status at each target and mode, and the pooled descriptive risk at coverage 0.25
(rank matched, primary policy) for s_C, s_C-D and confidence. Incomplete runs are summarised from their completed
folds and labelled. Writes 03_results/diagnostics/CROSS_RUN_SUMMARY.csv.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]


def _preds(d: Path) -> pd.DataFrame:
    if (d / "predictions.parquet").exists():
        return pd.read_parquet(d / "predictions.parquet")
    parts = [pd.read_csv(f / "predictions.csv").assign(fold=int(f.name.split("_")[1]))
             for f in sorted((d / "folds").glob("fold_*")) if (f / "DONE.json").exists()]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def summarize(d: Path) -> dict:
    m = json.loads((d / "run_manifest.json").read_text(encoding="utf-8"))
    p = _preds(d)
    row = {"run_dir": d.name, "analysis": (m.get("sensitivity") or {}).get("name", "clean_realization" if "ROBUSTNESS" in d.name else "primary"),
           "artifact_class": m.get("artifact_class"), "status": m.get("status"), "run_key": str(m.get("run_key"))[:12],
           "n_windows": (m.get("features") or {}).get("n_windows"), "n_features": (m.get("features") or {}).get("n_features"),
           "folds_completed": int(p.fold.nunique()) if len(p) else 0}
    if len(p):
        yh = np.array(CLASSES)[p[[f"p_cal_{c}" for c in CLASSES]].to_numpy(float).argmax(1)]
        for t, g in p.groupby("topology"):
            row[f"accuracy_{t}"] = float((yh[g.index] == g.y_true.to_numpy()).mean())
            row[f"max_attainable_{t}"] = float((g.support_flags.fillna("") == "").mean())  # flag-free share (primary policy blocks every listed flag)
    if (d / "rq1.csv").exists():
        r = pd.read_csv(d / "rq1.csv")
        r = r[(r.variant == "primary") & (r.comparison_b == "s_C_minus_D")]
        for x in r.itertuples():
            row[f"rq1_{x.mode}_{x.target:.2f}"] = x.status
            if x.status == "ESTIMABLE":
                row[f"rq1_{x.mode}_{x.target:.2f}"] += f" diff={x.difference:.3f} [{x.ci_low:.3f},{x.ci_high:.3f}]"
    if (d / "risk_coverage_curve.csv").exists():
        c = pd.read_csv(d / "risk_coverage_curve.csv")
        c = c[(c.scope == "pooled") & (c.variant == "primary") & (c.coverage_requested == 0.25)]
        for x in c.itertuples():
            if x.method in ("s_C", "s_C_minus_D", "confidence"):
                row[f"pooled_risk_0.25_{x.method}"] = x.selective_risk if x.status == "ESTIMABLE" else "NOT_ESTIMABLE"
    return row


def main() -> int:
    runs = REPO / "03_results" / "primary_protocol"
    dirs = [d for d in sorted(runs.iterdir()) if d.is_dir() and (d.name == "PRIMARY" or d.name.startswith(("ROBUSTNESS_", "SENSITIVITY_")))
            and (d / "run_manifest.json").exists() and d.name != "SENSITIVITY_SUMMARY"]
    df = pd.DataFrame([summarize(d) for d in dirs])
    out = REPO / "03_results" / "diagnostics" / "CROSS_RUN_SUMMARY.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, lineterminator="\n", float_format="%.6g")
    print(df.T.to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
