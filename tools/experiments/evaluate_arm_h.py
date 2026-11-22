#!/usr/bin/env python3
"""
Evaluate development arm H_POSITION_MATCHED against its criterion registered before the run
(06_audit_preparation/protocol2/ABLATION_MATRIX_ADDENDUM_H.csv), with G1 as the comparator:
  1. no unmapped or padded channel among model inputs (structural: 12 canonical channels x 8 statistics, position map
     hash recorded in the run manifest);
  2. dev OUT_OF_SUPPORT share in development topologies of folds that include the down model lower than G1's;
  3. dev group-balanced accuracy not lower than G1's by more than 0.05.
Criteria are applied literally. Everything is EXPLORATORY_DEVELOPMENT.
Writes 03_results/ablation/ARM_H_SUMMARY.csv and ARM_H_ACCEPTANCE.csv.
Usage: python tools/experiments/evaluate_arm_h.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "experiments"))

import evaluate_ablation as ea  # noqa: E402

OUT = REPO / "03_results" / "ablation"
PMAP_SHA = (REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_SENSOR_POSITION_MAP_V01.sha256").read_text().split()[0]


def oos_with_down(oof: pd.DataFrame) -> float:
    """OUT_OF_SUPPORT share over development topologies of folds whose development set contains the down model."""
    folds = oof.groupby("fold").topology.apply(lambda t: "Downstream" in set(t))
    x = oof[oof.fold.isin(folds[folds].index)]
    return float(x.support_flags.fillna("").str.contains("OUT_OF_SUPPORT").mean())


def main() -> int:
    rows, acc = [], []
    loaded = {}
    for arm in ("G1_DATA_CORRECTIONS", "H_POSITION_MATCHED"):
        r = ea._load(arm)
        if r is None:
            print(f"{arm} not completed", file=sys.stderr)
            return 1
        man, m, dm, oof = r
        s = ea.summary(arm, man, m, dm, oof)
        s["oos_share_folds_with_down"] = oos_with_down(oof)
        s["position_map_sha256"] = (man.get("features") or {}).get("position_map", {}).get("sha256")
        loaded[arm] = s
        rows.append({**s, "evidence_status": "EXPLORATORY_DEVELOPMENT"})
    g, h = loaded["G1_DATA_CORRECTIONS"], loaded["H_POSITION_MATCHED"]
    ok1 = h["n_features"] == 96 and h["position_map_sha256"] == PMAP_SHA
    acc.append({"criterion": "no unmapped or padded channel among model inputs", "result": "PASS" if ok1 else "FAIL",
                "detail": f"{h['n_features']} model features; position map sha {str(h['position_map_sha256'])[:12]}"})
    ok2 = h["oos_share_folds_with_down"] < g["oos_share_folds_with_down"]
    acc.append({"criterion": "dev OUT_OF_SUPPORT share (folds with the down model) lower than G1", "result": "PASS" if ok2 else "FAIL",
                "detail": f"{h['oos_share_folds_with_down']:.3f} vs G1 {g['oos_share_folds_with_down']:.3f}"})
    ok3 = h["dev_group_balanced_accuracy_mean"] >= g["dev_group_balanced_accuracy_mean"] - 0.05
    acc.append({"criterion": "dev group-balanced accuracy not lower than G1 by more than 0.05", "result": "PASS" if ok3 else "FAIL",
                "detail": f"{h['dev_group_balanced_accuracy_mean']:.3f} vs G1 {g['dev_group_balanced_accuracy_mean']:.3f}"})
    pd.DataFrame(rows).to_csv(OUT / "ARM_H_SUMMARY.csv", index=False, lineterminator="\n", float_format="%.6g")
    pd.DataFrame(acc).assign(arm_id="H_POSITION_MATCHED", evidence_status="EXPLORATORY_DEVELOPMENT") \
        .to_csv(OUT / "ARM_H_ACCEPTANCE.csv", index=False, lineterminator="\n")
    pd.set_option("display.width", 250)
    print(pd.DataFrame(rows).T.to_string())
    print(pd.DataFrame(acc).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
