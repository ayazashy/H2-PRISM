"""Development-only ablation mode (protocol 2.0 program): gate, isolation from outer-test data, registered arms."""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.experiments.synthetic_protocol_fixture import make_fixture  # noqa: E402


@pytest.fixture(scope="module")
def dev_run(tmp_path_factory):
    d = tmp_path_factory.mktemp("dev")
    fx = make_fixture(d / "fx")
    cfg = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    cfg["distinguishability"]["statistic"] = "evidence_margin"
    cfg["distinguishability"]["support_unit"] = "independence_group"
    cfg["policy_primary"]["evidence_conflict"] = "ambiguity_pair"
    cfg.setdefault("combined_scores", {})["on_undefined"] = "not_estimable"
    p = d / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg))
    m = pp.run(p, fx["root"], fx["raw"], d / "o", "develop")
    return fx, d, m


def test_develop_mode_never_scores_the_held_out_topology(dev_run):
    fx, d, m = dev_run
    assert m["status"] == "COMPLETED" and "no outer-test scoring" in m["scope_note"]
    folds = pd.read_csv(fx["folds"])
    for k, g in folds.groupby("outer_fold_id"):
        oof = pd.read_parquet(d / "o" / "folds" / f"fold_{k}" / "dev_oof.parquet")
        assert set(oof.Scenario_ID) <= set(g[g.split_role == "train"].Scenario_ID)
        assert not set(oof.Scenario_ID) & set(g[g.split_role == "test"].Scenario_ID)
    assert not (d / "o" / "rq1.csv").exists() and not (d / "o" / "predictions.parquet").exists()


def test_develop_outputs_are_instrumented_for_failure_analysis(dev_run):
    """X14 / C-12: calibrated class probabilities per window and meta-model coefficients are stored; probabilities
    reproduce the stored labels and confidence exactly, so later analyses need no refitting."""
    import numpy as np
    fx, d, _ = dev_run
    cfg = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    classes = list(cfg["dataset"]["classes"])
    for k in pd.read_csv(fx["folds"]).outer_fold_id.unique():
        oof = pd.read_parquet(d / "o" / "folds" / f"fold_{k}" / "dev_oof.parquet")
        P = oof[[f"p_cal_{c}" for c in classes]].to_numpy()
        assert np.allclose(P.sum(1), 1.0, atol=1e-6)
        assert (np.array(classes, dtype=object)[P.argmax(1)] == oof.y_hat.to_numpy()).all()
        assert np.allclose(P.max(1), oof.score_confidence.to_numpy(), atol=1e-9)
        done = json.loads((d / "o" / "folds" / f"fold_{k}" / "DONE.json").read_text(encoding="utf-8"))
        for name, rec in done["meta_models"].items():
            if rec is not None:
                assert len(rec["coef"]) == len(rec["features"]) == len(rec["scaler_mean"])
                assert ("D" in rec["features"]) == (name == "s_C")


def test_develop_metrics_include_prespecified_columns(dev_run):
    _, d, _ = dev_run
    m = pd.read_csv(d / "o" / "DEV_METRICS.csv")
    need = {"accuracy", "balanced_accuracy", "macro_f1", "group_balanced_accuracy", "worst_group_accuracy", "ece_10",
            "auroc_s_C", "auroc_s_C_minus_D", "auroc_confidence", "auroc_E_evidence_margin", "share_E_undefined"}
    assert need <= set(m.columns)
    dm = pd.read_csv(d / "o" / "DEV_DECISION_METRICS.csv")
    assert {"target_rule_status", "status"} <= set(dm.columns)


def test_real_develop_mode_requires_registered_arm_and_scoped_authorization(tmp_path):
    arm = ROOT / "06_audit_preparation" / "protocol2" / "arms" / "A_P11_DEV.yaml"
    with pytest.raises(pp.AuthorizationError, match="authorization"):
        pp.run(arm, ROOT, ROOT / "data" / "raw", tmp_path / "o", "develop", authorization=None)
    cfg = yaml.safe_load(arm.read_text(encoding="utf-8"))
    sha = pp.sha256_file(arm)
    wrong = tmp_path / "auth.yaml"
    wrong.write_text(yaml.safe_dump({"authorized": True, "scope": "DEVELOPMENT_EXPERIMENT:OTHER_ARM", "config_sha256": sha,
                                     "authorized_by": "x", "date": "2026-11-12",
                                     "governance_clearance": {k: "WAIVED" for k in pp.REQUIRED_CLEARANCES}}))
    with pytest.raises(pp.AuthorizationError, match="scope"):
        pp.run(arm, ROOT, ROOT / "data" / "raw", tmp_path / "o2", "develop", authorization=wrong)
    cand = yaml.safe_load((ROOT / "06_audit_preparation" / "protocol2" / "CANDIDATE_PROTOCOL_2_0.yaml").read_text(encoding="utf-8"))
    cp = tmp_path / "cand.yaml"
    cp.write_text(yaml.safe_dump(cand))
    with pytest.raises(pp.AuthorizationError, match="registered arm"):
        pp.run(cp, ROOT, ROOT / "data" / "raw", tmp_path / "o3", "develop")
    assert cfg["status"] == pp.DEV_ARM_STATUS


def test_registered_matrix_is_complete_and_bounded():
    m = pd.read_csv(ROOT / "06_audit_preparation" / "protocol2" / "ABLATION_MATRIX.csv")
    assert len(m) == 8 and m.arm_id.is_unique and set(m.evidence_status.str.startswith("EXPLORATORY")) == {True}
    for r in m.itertuples():
        p = ROOT / r.config_file
        assert pp.sha256_file(p) == r.config_sha256
        c = yaml.safe_load(p.read_text(encoding="utf-8"))
        assert c["status"] == pp.DEV_ARM_STATUS and c["arm_id"] == r.arm_id
    one = m[m.one_factor == "yes"]
    assert set(one.arm_id) == {"A_P11_DEV", "B_TOPOLOGY", "C_COMMON_SENSORS", "D_GROUP_SUPPORT", "E_EVIDENCE_CONFLICT", "F_EVIDENCE_MARGIN"}


def test_outer_stage_refuses_evidence_margin_meta_model():
    cfg = {"dataset": {"classes": ["A", "B"]}, "distinguishability": {"statistic": "evidence_margin"}}
    with pytest.raises(NotImplementedError):
        pp.outer_stage(cfg, None, None, [], {})


def _summ(**kw):
    base = {"min_auroc_confidence_over_dev_topologies": 0.3, "share_errors_conf_ge_0_9": 0.5, "n_features": 128,
            "dev_group_balanced_accuracy_mean": 0.6, "s_C_group_balanced_risk_mean": 0.10, "s_C_ambiguity_inclusion_mean": float("nan"),
            "min_auroc_D_only_over_dev_topologies": 0.4, "min_auroc_E_over_dev_topologies": float("nan"),
            "auroc_s_C_minus_auroc_s_C_minus_D_mean": float("nan"), "dev_targets_by_fold": "1:0.5;2:None;3:None"}
    base.update(kw)
    return base


def test_acceptance_is_literal_and_never_forces_unmatched_comparisons():
    sys.path.insert(0, str(ROOT / "tools" / "experiments"))
    import evaluate_ablation as ea
    a = _summ()
    e_same = ea.acceptance("E_EVIDENCE_CONFLICT", _summ(s_C_group_balanced_risk_mean=0.05, s_C_ambiguity_inclusion_mean=0.95), a)
    assert {r["result"] for r in e_same} == {"PASS"}
    e_diff = ea.acceptance("E_EVIDENCE_CONFLICT", _summ(s_C_group_balanced_risk_mean=0.05, dev_targets_by_fold="1:0.4;2:None;3:None"), a)
    assert e_diff[0]["result"] == "NOT_EVALUABLE"  # different operating points are never compared
    b = ea.acceptance("B_TOPOLOGY", _summ(min_auroc_confidence_over_dev_topologies=0.49, share_errors_conf_ge_0_9=0.1), a)
    assert [r["result"] for r in b] == ["FAIL", "PASS"]  # 0.49 < 0.5 fails even though the other criterion passes
    f = ea.acceptance("F_EVIDENCE_MARGIN", _summ(min_auroc_E_over_dev_topologies=0.44, auroc_s_C_minus_auroc_s_C_minus_D_mean=0.01), a)
    assert [r["result"] for r in f] == ["FAIL", "PASS"]  # +0.04 is below the registered +0.05 margin
