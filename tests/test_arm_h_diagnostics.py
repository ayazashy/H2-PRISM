"""Validation of the read-only arm H root-cause diagnostics (no training): inputs unchanged, decision reproduction,
independent-unit accounting, statement verdicts, taxonomy rules, and no private paths in outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
D = REPO / "03_results" / "diagnostics" / "arm_h_failures"
RUN = REPO / "03_results" / "ablation_runs" / "H_POSITION_MATCHED"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def test_h_outputs_rc1_and_authorization_unchanged():
    lst = REPO / "03_results" / "ablation_runs" / "logs" / "H_POSITION_MATCHED_65f05249dd12_OUTPUT_HASHES.sha256"
    for line in lst.read_text(encoding="utf-8").splitlines():
        h, name = line.split(maxsplit=1)
        f = RUN / name.lstrip("*")
        if f.exists():  # git-ignored parquet may be absent in a clean checkout
            assert _sha(f) == h, name
    rc = REPO / "06_audit_preparation" / "protocol2" / "release_candidate"
    assert (rc / "P2_0_RC1.sha256").read_text().split()[0] == _sha(rc / "P2_0_RC1.yaml")
    auth = REPO / "06_audit_preparation" / "protocol2" / "arm_authorizations" / "AUTH_H_POSITION_MATCHED.yaml"
    assert "DEVELOPMENT_EXPERIMENT:H_POSITION_MATCHED" in auth.read_text(encoding="utf-8")


def test_no_model_fitted_and_decisions_reproduced():
    s = json.loads((D / "SUMMARY.json").read_text(encoding="utf-8"))
    assert s["model_fitted"] is False and s["tuned"] is False and s["inputs_verified_against_hash_list"] is True
    d = pd.read_csv(D / "DECISION_REPRODUCTION.csv")
    assert len(d) == 18 and d.reproduced.all()
    assert np.allclose(d.group_balanced_risk, d.stored_group_balanced_risk)
    only_normal = (d.groups_with_any_error == 1) & (d.NORMAL_group_risk >= 0.99)
    assert np.allclose(d[only_normal].group_balanced_risk, 1 / d[only_normal].groups_selected, atol=1e-3)


def test_errors_counted_by_independent_unit():
    s = pd.read_csv(D / "ERROR_INDEPENDENT_SUMMARY.csv").set_index("error_type")
    by = pd.read_csv(D / "ERROR_BY_ANCESTOR.csv")
    for et, g in by.groupby("error_type"):
        assert g.window_fold_instances.sum() == s.loc[et, "window_fold_instances"]
        assert g.independence_group.nunique() == s.loc[et, "independence_groups"]
        assert s.loc[et, "unique_windows"] <= s.loc[et, "window_fold_instances"]  # windows recur across folds
    assert s.loc["NORMAL->LEAK", "independence_groups"] == 1
    assert s.loc["NORMAL->LEAK", "confident_instances"] == 3151  # matches the high-confidence composition of arm H


def test_statements_and_taxonomy_rules():
    st = pd.read_csv(D / "STATEMENT_VERIFICATION.csv")
    assert len(st) == 4 and st.verdict.str.len().gt(0).all()
    assert st.verdict.iloc[1].startswith("REVISED")  # the 10-40x ratio was not reproduced
    tax = pd.read_csv(D / "ERROR_TAXONOMY.csv")
    n = tax[tax.error_type == "NORMAL->LEAK"]
    assert (n.mechanism.str.startswith("PHYSICAL_OVERLAP")).all() and (n.knn_majority_classifier_label > 0.9).all()
    l2n = tax[tax.error_type == "LEAK->NORMAL"]
    assert (l2n.mechanism == "CLASSIFIER_FAILURE").all()
    assert (l2n.event_visibility_sigma >= 2).all() and (l2n.knn_majority_true_class >= 0.9).all()


def test_pre_event_original_and_robust_statistics_both_reported():
    o = pd.read_csv(D / "EVENT_OBSERVABILITY.csv")
    assert {"pre_event_max_abs_z", "pre_event_median_abs_z_top_channel"} <= set(o.columns)
    assert (o.pre_event_median_abs_z_top_channel <= o.pre_event_max_abs_z + 1e-9).all()


def test_outputs_have_no_private_paths():
    for f in D.glob("*"):
        t = f.read_text(encoding="utf-8")
        assert ":\\" not in t and "/Users/" not in t, f.name
