#!/usr/bin/env python3
"""
(1) Regression proof: with protocol 1.1 defaults, the current code reproduces R2's stored D(x) and support flags exactly.
(2) CANDIDATE_IMPACT_ASSESSMENT (descriptive; not used to tune anything): the same R2 neighbourhoods with independent
    support counted by scenario independence groups (P2-C) instead of topology-scoped families.

No model is fitted; only the registered D(x) reference computation is repeated on the recorded feature table.
Outputs: 03_results/diagnostics/protocol2_impact/{regression_check.json, support_unit_impact.csv}
Usage: python tools/experiments/assess_support_unit_impact.py --raw-parent data/raw
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402

CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-parent", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=REPO / "03_results" / "diagnostics" / "protocol2_impact")
    a = ap.parse_args(argv)
    cfg = yaml.safe_load((REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))
    run = REPO / "03_results" / "primary_protocol" / "PRIMARY"
    man = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    ft, fsum = pp.build_features(cfg, REPO, a.raw_parent.resolve(), "noise_added")
    if fsum["feature_table_sha256"] != man["features"]["feature_table_sha256"]:
        raise SystemExit("REFUSED: feature table differs from R2")
    feats = pp.model_feature_columns(ft)
    preds = pd.read_parquet(run / "predictions.parquet").set_index("window_id")
    cand = copy.deepcopy(cfg)
    cand["distinguishability"]["support_unit"] = "independence_group"
    pol = pp._policies(cfg)["primary"]
    regress, rows = [], []
    for held in sorted(ft.topology.unique()):
        dev, test = ft[ft.topology != held], ft[ft.topology == held]
        s11 = pp._support(cfg, dev, test, feats, CLASSES)
        st = preds.loc[test.window_id]
        same_d = bool(np.allclose(s11.D.to_numpy(float), st.D.to_numpy(float), equal_nan=True))
        same_f = bool((s11.support_flags.fillna("").to_numpy() == st.support_flags.fillna("").to_numpy()).all())
        regress.append({"held_out": held, "n": len(test), "D_reproduced": same_d, "flags_reproduced": same_f})
        s2 = pp._support(cand, dev, test, feats, CLASSES)
        yh = np.array(CLASSES)[st[[f"p_cal_{c}" for c in CLASSES]].to_numpy(float).argmax(1)]
        for label, s in (("protocol_1_1_family_units", s11), ("candidate_independence_group_units", s2)):
            av = pp._available(np.zeros(len(s)), s.support_flags.fillna(""), pol)
            for c in CLASSES:
                m = test.label_mapped.to_numpy() == c
                rows.append({"held_out": held, "class": c, "support_unit": label, "n_windows": int(m.sum()),
                             "share_flag_free": float(av[m].mean()) if m.any() else np.nan,
                             "share_top_class_few_independent": float(s.support_flags.fillna("")[m].str.contains("TOP_CLASS_FEW").mean()) if m.any() else np.nan,
                             "flag_free_accuracy": float((yh[m & av] == c).mean()) if (m & av).any() else np.nan,
                             "max_attainable_coverage_fold": float(av.mean()),
                             "mean_D": float(np.nanmean(s.D.to_numpy(float)[m])) if m.any() else np.nan})
    a.out.mkdir(parents=True, exist_ok=True)
    rec = {"status": "REGRESSION_CHECK", "all_reproduced": all(r["D_reproduced"] and r["flags_reproduced"] for r in regress),
           "folds": regress, "source_run_key": man["run_key"]}
    (a.out / "regression_check.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    df = pd.DataFrame(rows)
    df["analysis_status"] = "CANDIDATE_IMPACT_ASSESSMENT_DESCRIPTIVE_NOT_FOR_TUNING"
    df.to_csv(a.out / "support_unit_impact.csv", index=False, lineterminator="\n", float_format="%.6g")
    print(json.dumps(rec, indent=2))
    return 0 if rec["all_reproduced"] else 1


if __name__ == "__main__":
    sys.exit(main())
