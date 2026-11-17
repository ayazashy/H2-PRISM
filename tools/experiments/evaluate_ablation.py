#!/usr/bin/env python3
"""
Acceptance evaluation of the registered development-only ablation arms (criteria fixed in ABLATION_MATRIX.csv before
any arm ran). Reads 03_results/ablation_runs/<ARM>/{DEV_METRICS,DEV_DECISION_METRICS}.csv and folds/*/dev_oof.parquet;
writes 03_results/ablation/{ARM_SUMMARY.csv, ABLATION_ACCEPTANCE.csv}. Every result is EXPLORATORY_DEVELOPMENT.

Fairness rules: decision metrics are compared only at the same development-fixed target; if an arm's target differs
from A's in a fold, that comparison is NOT_MATCHED and its criterion is NOT_EVALUABLE (never forced). Arms that change
the topology attribution (B, G1, G2) re-compose the development sets, so their fold-level values are compared at the
pooled development level only.
Usage: python tools/experiments/evaluate_ablation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "03_results" / "ablation_runs"
OUT = REPO / "03_results" / "ablation"
MATRIX = REPO / "06_audit_preparation" / "protocol2" / "ABLATION_MATRIX.csv"


def _load(arm):
    d = RUNS / arm
    man = json.loads((d / "run_manifest.json").read_text(encoding="utf-8"))
    if man.get("status") != "COMPLETED":
        return None
    m = pd.read_csv(d / "DEV_METRICS.csv")
    dm = pd.read_csv(d / "DEV_DECISION_METRICS.csv")
    for col in ("group_balanced_selective_risk", "selective_risk", "ambiguity_inclusion", "coverage", "target"):
        if col not in dm.columns:  # an arm where nothing is estimable has no decision-metric columns: values are absent, not 0
            dm[col] = np.nan
    oof = pd.concat([pd.read_parquet(f) for f in sorted(d.glob("folds/fold_*/dev_oof.parquet"))], ignore_index=True)
    return man, m, dm, oof


def summary(arm, man, m, dm, oof) -> dict:
    topo_rows = m[m.scope != "DEV_POOLED"]
    pooled = m[m.scope == "DEV_POOLED"]
    err = ~oof.correct.astype(bool)
    s = {"arm_id": arm, "run_key": man["run_key"][:12], "n_features": man["features"]["n_features"],
         "dev_accuracy_mean": pooled.accuracy.mean(), "dev_balanced_accuracy_mean": pooled.balanced_accuracy.mean(),
         "dev_macro_f1_mean": pooled.macro_f1.mean(), "dev_group_balanced_accuracy_mean": pooled.group_balanced_accuracy.mean(),
         "dev_worst_group_accuracy_min": pooled.worst_group_accuracy.min(), "dev_ece_mean": pooled.ece_10.mean(),
         "min_auroc_confidence_over_dev_topologies": topo_rows.auroc_confidence.min(),
         "min_auroc_D_only_over_dev_topologies": topo_rows.auroc_D_only.min(),
         "share_errors_conf_ge_0_9": float((oof.score_confidence[err] >= 0.9).mean()) if err.any() else np.nan,
         "meta_model_undefined_folds": int((pooled.meta_model_status != "FITTED").sum()),
         "share_flag_free_mean": pooled.share_flag_free.mean()}
    if "auroc_E_evidence_margin" in m.columns:
        s["min_auroc_E_over_dev_topologies"] = topo_rows.auroc_E_evidence_margin.min()
        s["share_E_undefined_mean"] = pooled.share_E_undefined.mean()
    for meth in ("s_C", "s_C_minus_D", "confidence"):
        x = dm[(dm.method == meth) & (dm.status == "ESTIMABLE")]
        s[f"{meth}_estimable_dev_topologies"] = int(len(x))
        s[f"{meth}_group_balanced_risk_mean"] = x.group_balanced_selective_risk.mean() if len(x) else np.nan
        s[f"{meth}_selective_risk_mean"] = x.selective_risk.mean() if len(x) else np.nan
    s["s_C_ambiguity_inclusion_mean"] = dm[(dm.method == "s_C") & (dm.status == "ESTIMABLE")].ambiguity_inclusion.mean()
    s["dev_targets_by_fold"] = ";".join(f"{int(r.fold)}:{r.target}" for r in dm.drop_duplicates("fold").itertuples())
    s["auroc_s_C_minus_auroc_s_C_minus_D_mean"] = (pooled.auroc_s_C - pooled.auroc_s_C_minus_D).mean()
    return s


def acceptance(arm, s, a) -> list:
    """The registered criterion of each arm, evaluated literally against A (or NOT_EVALUABLE with the reason)."""
    def v(x):
        return x is not None and not (isinstance(x, float) and np.isnan(x))

    same_targets = s["dev_targets_by_fold"] == a["dev_targets_by_fold"]
    out = []

    def add(crit, ok, detail):
        out.append({"arm_id": arm, "criterion": crit, "result": ok, "detail": detail})

    if arm.startswith("B") or arm.startswith("G"):
        ok = v(s["min_auroc_confidence_over_dev_topologies"]) and s["min_auroc_confidence_over_dev_topologies"] >= 0.5
        add("confidence AUROC >= 0.5 in every development topology", "PASS" if ok else "FAIL",
            f"min {s['min_auroc_confidence_over_dev_topologies']:.3f} (A: {a['min_auroc_confidence_over_dev_topologies']:.3f})")
        ok = s["share_errors_conf_ge_0_9"] < a["share_errors_conf_ge_0_9"]
        add("share of errors with confidence >= 0.9 lower than A", "PASS" if ok else "FAIL",
            f"{s['share_errors_conf_ge_0_9']:.3f} vs A {a['share_errors_conf_ge_0_9']:.3f}")
    if arm.startswith("C") or arm.startswith("G"):
        add("no padded channel among model inputs", "PASS" if s["n_features"] == 104 else "FAIL", f"{s['n_features']} model features")
        ok = s["dev_group_balanced_accuracy_mean"] >= a["dev_group_balanced_accuracy_mean"] - 0.05
        add("dev group-balanced accuracy not lower than A by more than 0.05", "PASS" if ok else "FAIL",
            f"{s['dev_group_balanced_accuracy_mean']:.3f} vs A {a['dev_group_balanced_accuracy_mean']:.3f}")
    if arm.startswith("D") or arm.startswith("E") or arm.startswith("G2"):
        if not same_targets:
            add("group-balanced selective risk vs A at the same target", "NOT_EVALUABLE",
                f"targets differ: {s['dev_targets_by_fold']} vs A {a['dev_targets_by_fold']}")
        elif not (v(s["s_C_group_balanced_risk_mean"]) and v(a["s_C_group_balanced_risk_mean"])):
            add("group-balanced selective risk vs A at the same target", "NOT_EVALUABLE", "not estimable in this arm or in A")
        else:
            strict = arm.startswith("E")
            ok = s["s_C_group_balanced_risk_mean"] < a["s_C_group_balanced_risk_mean"] if strict else \
                s["s_C_group_balanced_risk_mean"] <= a["s_C_group_balanced_risk_mean"]
            floor = (s["s_C_group_balanced_risk_mean"] == 0 and a["s_C_group_balanced_risk_mean"] == 0)
            note = (f"; UNINFORMATIVE: both risks 0 on {int(s['s_C_estimable_dev_topologies'])} estimable development topology(ies)"
                    if floor else "")
            add("group-balanced selective risk " + ("lower than" if strict else "not higher than") + " A", "PASS" if ok else "FAIL",
                f"{s['s_C_group_balanced_risk_mean']:.4f} vs A {a['s_C_group_balanced_risk_mean']:.4f}{note}")
    if arm.startswith("E") or arm.startswith("G2"):
        inc = s["s_C_ambiguity_inclusion_mean"]
        add("ambiguity-set inclusion >= 0.9 where sets are issued", ("PASS" if inc >= 0.9 else "FAIL") if v(inc) else "NOT_EVALUABLE",
            f"{inc}")
    if arm.startswith("F") or arm.startswith("G2"):
        e, d = s.get("min_auroc_E_over_dev_topologies"), a["min_auroc_D_only_over_dev_topologies"]
        add("AUROC(E) > AUROC(D_only of A) by >= 0.05 in every development topology (min over topologies)",
            ("PASS" if e - d >= 0.05 else "FAIL") if v(e) and v(d) else "NOT_EVALUABLE", f"min E {e} vs min D {d}")
        g = s["auroc_s_C_minus_auroc_s_C_minus_D_mean"]
        add("AUROC(s_C) - AUROC(s_C_minus_D) > 0", ("PASS" if g > 0 else "FAIL") if v(g) else "NOT_EVALUABLE", f"{g}")
    return out


def main() -> int:
    mat = pd.read_csv(MATRIX)
    S, A = [], None
    loaded = {}
    for arm in mat.arm_id:
        r = _load(arm) if (RUNS / arm / "run_manifest.json").exists() else None
        if r is None:
            S.append({"arm_id": arm, "status": "NOT_COMPLETED"})
            continue
        loaded[arm] = summary(arm, *r)
        S.append({**loaded[arm], "status": "COMPLETED"})
    A = loaded.get("A_P11_DEV")
    acc = []
    for arm in mat.arm_id:
        if arm == "A_P11_DEV":
            continue
        if A is None or arm not in loaded:
            acc.append({"arm_id": arm, "criterion": "all", "result": "NOT_EVALUABLE", "detail": "arm or reference not completed"})
            continue
        acc += acceptance(arm, loaded[arm], A)
    OUT.mkdir(parents=True, exist_ok=True)
    sm = pd.DataFrame(S).assign(evidence_status="EXPLORATORY_DEVELOPMENT")
    ac = pd.DataFrame(acc).assign(evidence_status="EXPLORATORY_DEVELOPMENT")
    sm.to_csv(OUT / "ARM_SUMMARY.csv", index=False, lineterminator="\n", float_format="%.6g")
    ac.to_csv(OUT / "ABLATION_ACCEPTANCE.csv", index=False, lineterminator="\n")
    pd.set_option("display.width", 250)
    print(ac.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
