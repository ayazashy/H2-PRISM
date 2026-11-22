#!/usr/bin/env python3
"""
Consolidated comparison from EXISTING outputs only (no training, no new scoring of held-out data).

Rows:
  * the classifier-changing development arms A, B, C, G1 (D/E/F/G2 have identical classifiers to A/G1 and are listed
    only through their decision-layer columns) -- EXPLORATORY_DEVELOPMENT (inner topology-held-out predictions);
  * R2 (registered protocol 1.1 primary, release attribution) recomputed from its stored outer predictions --
    REGISTERED_PRIMARY_P11_DESCRIPTIVE. R2 is a different evaluation set (outer topology) and a different
    attribution, so it is never placed in the same comparison as the development rows; it is a reference only.
Writes 03_results/consolidated/{CONSOLIDATED_COMPARISON.csv, DECISION_LAYER_COMPARISON.csv}.
Usage: python tools/experiments/consolidated_comparison.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.evaluation_metrics import brier, classifier_metrics, decision_metrics, ece, group_level_accuracy  # noqa: E402
from h2prism.independence import independence_groups  # noqa: E402

RUNS = REPO / "03_results" / "ablation_runs"
HC = REPO / "03_results" / "diagnostics" / "high_confidence" / "HIGH_CONFIDENCE_ERRORS.csv"
R2 = REPO / "03_results" / "primary_protocol" / "PRIMARY"
MAN = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv"
OUT = REPO / "03_results" / "consolidated"
CLS = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
CLASSIFIER_ARMS = {"A_P11_DEV": "A protocol 1.1", "B_TOPOLOGY": "B source-model topology (v0.3)",
                   "C_COMMON_SENSORS": "C 13 name-matched sensors", "G1_DATA_CORRECTIONS": "G1 = B + C",
                   "H_POSITION_MATCHED": "H = B + 12 position-matched sensors (map v0.1)"}
ALL_ARMS = list(CLASSIFIER_ARMS) + ["D_GROUP_SUPPORT", "E_EVIDENCE_CONFLICT", "F_EVIDENCE_MARGIN", "G2_FULL_CANDIDATE"]


def dev_row(arm):
    m = pd.read_csv(RUNS / arm / "DEV_METRICS.csv")
    pooled, topo = m[m.scope == "DEV_POOLED"], m[m.scope != "DEV_POOLED"]
    hc = pd.read_csv(HC).set_index(["arm_id", "scope"]).loc[(arm, "pooled_window_fold_instances")]
    wt = topo.loc[topo.accuracy.idxmin()]
    return {"row": CLASSIFIER_ARMS[arm], "arm_id": arm, "evidence_status": "EXPLORATORY_DEVELOPMENT",
            "evaluation_set": "inner topology-held-out (development), 3 folds x 2 topologies",
            "accuracy": pooled.accuracy.mean(), "macro_f1": pooled.macro_f1.mean(),
            "balanced_accuracy": pooled.balanced_accuracy.mean(),
            "scenario_group_balanced_accuracy": pooled.group_balanced_accuracy.mean(),
            "min_recall_NORMAL_over_folds": pooled.recall_NORMAL.min(),
            "worst_topology": f"fold {int(wt.fold)} {wt.scope.replace('DEV_', '')}", "worst_topology_accuracy": wt.accuracy,
            "worst_scenario_group_accuracy": pooled.worst_group_accuracy.min(),
            "ece_10": pooled.ece_10.mean(), "brier": pooled.brier.mean(),
            "share_of_errors_conf_ge_0_9": hc.share_of_errors_confident,
            "error_rate_among_conf_ge_0_9": hc.error_rate_among_confident,
            "n_conf_ge_0_9": int(hc.n_confident), "confident_error_independence_groups": int(hc.confident_errors_independence_groups),
            "share_flag_free": pooled.share_flag_free.mean(),
            "meta_model_fitted_folds": int((pooled.meta_model_status == "FITTED").sum())}


def r2_row(groups):
    p = pd.read_parquet(R2 / "predictions.parquet")
    P = p[[f"p_cal_{c}" for c in CLS]].to_numpy(float)
    yhat = np.array(CLS, dtype=object)[P.argmax(1)]
    yi = p.y_true.map({c: i for i, c in enumerate(CLS)}).to_numpy()
    cm = classifier_metrics(p.y_true, yhat, CLS)
    ok = yhat == p.y_true.to_numpy()
    g = group_level_accuracy(ok, p.Scenario_ID.map(groups))
    by_t = pd.Series(ok).groupby(p.topology.to_numpy()).mean()
    conf = P.max(1) >= 0.9
    err = ~ok
    flags = p.support_flags.fillna("")
    return {"row": "R2 registered primary (protocol 1.1, release attribution)", "arm_id": "R2_a10530f1fcf2",
            "evidence_status": "REGISTERED_PRIMARY_P11_DESCRIPTIVE",
            "evaluation_set": "outer held-out topology (already inspected; not comparable to development rows)",
            "accuracy": cm["accuracy"], "macro_f1": cm["macro_f1"], "balanced_accuracy": cm["balanced_accuracy"],
            "scenario_group_balanced_accuracy": g["group_balanced_accuracy"], "min_recall_NORMAL_over_folds": cm["recall_NORMAL"],
            "worst_topology": f"{by_t.idxmin()} (outer)", "worst_topology_accuracy": by_t.min(),
            "worst_scenario_group_accuracy": g["worst_group_accuracy"], "ece_10": ece(P, yi), "brier": brier(P, yi),
            "share_of_errors_conf_ge_0_9": float((conf & err).sum() / err.sum()),
            "error_rate_among_conf_ge_0_9": float((conf & err).sum() / conf.sum()) if conf.any() else np.nan,
            "n_conf_ge_0_9": int(conf.sum()),
            "confident_error_independence_groups": int(p.Scenario_ID[conf & err].map(groups).nunique()),
            "share_flag_free": float((flags == "").mean()), "meta_model_fitted_folds": np.nan}


def decision_rows():
    out = []
    for arm in ALL_ARMS:
        d = pd.read_csv(RUNS / arm / "DEV_DECISION_METRICS.csv")
        for col in ("coverage", "selective_risk", "group_balanced_selective_risk", "n_wrong_specific", "ambiguity_inclusion",
                    "target", "dev_topology"):
            if col not in d.columns:
                d[col] = np.nan
        for meth in ("s_C", "s_C_minus_D", "confidence"):
            x = d[d.method == meth]
            est = x[x.status == "ESTIMABLE"]
            out.append({"arm_id": arm, "method": meth, "evidence_status": "EXPLORATORY_DEVELOPMENT",
                        "development_targets": ";".join(sorted({f"fold{int(r.fold)}:{r.target}" for r in x.itertuples()
                                                                if pd.notna(r.target)})) or "none",
                        "estimable_fold_topologies": len(est), "not_estimable_rows": int((x.status != "ESTIMABLE").sum()),
                        "not_estimable_reasons": ";".join(sorted(set(x.status[x.status != "ESTIMABLE"].astype(str)))),
                        "coverage_mean": est.coverage.mean() if len(est) else np.nan,
                        "selective_risk_mean": est.selective_risk.mean() if len(est) else np.nan,
                        "group_balanced_selective_risk_mean": est.group_balanced_selective_risk.mean() if len(est) else np.nan,
                        "n_wrong_specific_total": est.n_wrong_specific.sum() if len(est) else np.nan,
                        "ambiguity_inclusion_mean": est.ambiguity_inclusion.mean() if len(est) else np.nan})
    D = pd.DataFrame(out)
    inc = []
    for arm, g in D.groupby("arm_id"):
        a = g.set_index("method")
        v = a.loc["s_C", "group_balanced_selective_risk_mean"] - a.loc["s_C_minus_D", "group_balanced_selective_risk_mean"]
        inc.append({"arm_id": arm, "Dx_increment_group_balanced_risk_s_C_minus_s_C_minus_D": v,
                    "Dx_increment_status": "ESTIMABLE" if np.isfinite(v) else "NOT_ESTIMABLE"})
    return D.merge(pd.DataFrame(inc), on="arm_id")


def main() -> int:
    man = pd.read_csv(MAN)
    groups = dict(zip(man.Scenario_ID, man.Scenario_ID.map(independence_groups(man.Scenario_ID, man.Scenario_Family_ID))))
    rows = [dev_row(a) for a in CLASSIFIER_ARMS] + [r2_row(groups)]
    OUT.mkdir(parents=True, exist_ok=True)
    C = pd.DataFrame(rows)
    C.to_csv(OUT / "CONSOLIDATED_COMPARISON.csv", index=False, lineterminator="\n", float_format="%.4g")
    D = decision_rows()
    D.to_csv(OUT / "DECISION_LAYER_COMPARISON.csv", index=False, lineterminator="\n", float_format="%.4g")
    pd.set_option("display.width", 300, "display.max_columns", 40)
    print(C.drop(columns=["evaluation_set", "row"]).T.to_string())
    print(D.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
