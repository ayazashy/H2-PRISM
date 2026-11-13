#!/usr/bin/env python3
"""
B vs G1 high-confidence-error conflict: recompute from the stored development predictions (dev_oof.parquet) only.

Two different quantities are often both called "high-confidence errors":
  share_of_errors_confident   = #(wrong & conf >= 0.9) / #wrong            (denominator: the arm's errors)
  error_rate_among_confident  = #(wrong & conf >= 0.9) / #(conf >= 0.9)    (denominator: the arm's confident calls)
ARM_SUMMARY.csv's `share_errors_conf_ge_0_9` is the first one. Both are reported per fold (each window appears in the
development set of two outer folds, so a pooled count double-counts windows; pooled values are given per unique window
too), with numerators, denominators, the independence groups / scenario stems / runs behind the numerator, and the
class and topology composition. EXPLORATORY_DEVELOPMENT; nothing here is used to choose an arm.

Writes 03_results/diagnostics/high_confidence/{HIGH_CONFIDENCE_ERRORS.csv, HIGH_CONFIDENCE_ERROR_COMPOSITION.csv}.
Usage: python tools/experiments/high_confidence_errors.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.independence import ancestor, independence_groups  # noqa: E402

RUNS = REPO / "03_results" / "ablation_runs"
MAN = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv"
OUT = REPO / "03_results" / "diagnostics" / "high_confidence"
ARMS = ("A_P11_DEV", "B_TOPOLOGY", "C_COMMON_SENSORS", "G1_DATA_CORRECTIONS")
TAU = 0.9


def _rows(arm, scope, o, grp):
    err = ~o.correct.astype(bool)
    conf = o.score_confidence >= TAU
    he = o[err & conf]
    return {"arm_id": arm, "scope": scope, "n_windows": len(o), "n_errors": int(err.sum()), "n_confident": int(conf.sum()),
            "n_confident_errors": len(he),
            "share_of_errors_confident": len(he) / err.sum() if err.sum() else float("nan"),
            "error_rate_among_confident": len(he) / conf.sum() if conf.sum() else float("nan"),
            "overall_error_rate": float(err.mean()),
            "confident_errors_runs": he.Scenario_ID.nunique(),
            "confident_errors_scenario_stems": he.Scenario_ID.map(ancestor).nunique(),
            "confident_errors_independence_groups": he.Scenario_ID.map(grp).nunique(),
            "confident_errors_true_classes": ";".join(f"{k}:{v}" for k, v in he.label_mapped.value_counts().items()),
            "confident_errors_predicted_classes": ";".join(f"{k}:{v}" for k, v in he.y_hat.value_counts().items()),
            "confident_errors_dev_topologies": ";".join(f"{k}:{v}" for k, v in he.topology.value_counts().items()),
            "errors_true_classes": ";".join(f"{k}:{v}" for k, v in o[err].label_mapped.value_counts().items()),
            "errors_dev_topologies": ";".join(f"{k}:{v}" for k, v in o[err].topology.value_counts().items())}


def main() -> int:
    man = pd.read_csv(MAN)
    g = independence_groups(man.Scenario_ID, man.Scenario_Family_ID)
    grp = man.Scenario_ID.map(g)
    grp = dict(zip(man.Scenario_ID, grp))
    R, C = [], []
    for arm in ARMS:
        O = pd.concat([pd.read_parquet(f) for f in sorted((RUNS / arm).glob("folds/fold_*/dev_oof.parquet"))],
                      ignore_index=True)
        for k, o in O.groupby("fold"):
            R.append(_rows(arm, f"fold_{int(k)}", o, grp))
        R.append(_rows(arm, "pooled_window_fold_instances", O, grp))
        he = O[~O.correct.astype(bool) & (O.score_confidence >= TAU)]
        for (k, t, y, yh, sid), n in he.groupby(["fold", "topology", "label_mapped", "y_hat", "Scenario_ID"]).size().items():
            C.append({"arm_id": arm, "fold": int(k), "dev_topology": t, "true_class": y, "predicted_class": yh,
                      "Scenario_ID": sid, "independence_group": grp.get(sid), "n_windows": int(n)})
    OUT.mkdir(parents=True, exist_ok=True)
    R = pd.DataFrame(R).assign(evidence_status="EXPLORATORY_DEVELOPMENT", tau=TAU)
    R.to_csv(OUT / "HIGH_CONFIDENCE_ERRORS.csv", index=False, lineterminator="\n", float_format="%.6g")
    pd.DataFrame(C).assign(evidence_status="EXPLORATORY_DEVELOPMENT").to_csv(
        OUT / "HIGH_CONFIDENCE_ERROR_COMPOSITION.csv", index=False, lineterminator="\n")
    pd.set_option("display.width", 300, "display.max_colwidth", 80)
    print(R.drop(columns=["evidence_status", "tau"]).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
