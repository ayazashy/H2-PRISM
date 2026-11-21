"""Candidate protocol 2.0 components (P2-A..P2-F): opt-in, tested, and inactive in protocol 1.1.

Each component is exercised on the synthetic fixture only. Protocol 1.1 defaults must reproduce the historical
behaviour exactly, and the candidate config must be refused by preflight until it is approved.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from h2prism.distinguishability import DConfig, EmpiricalSupport  # noqa: E402
from h2prism.experiments import primary_protocol as pp  # noqa: E402
from h2prism.experiments.synthetic_protocol_fixture import make_fixture  # noqa: E402
from h2prism.independence import ancestor, independence_groups  # noqa: E402
from h2prism.policy import PolicyConfig, apply_policy  # noqa: E402
from h2prism.protocol2 import development_target  # noqa: E402

CL = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]


# ------------------------------------------------------------------ independence units (P2-C)
def test_independence_groups_merge_families_and_cross_topology_replicas():
    sids = ["CS_CENTER_X_WEAK", "CS_CENTER_X_STRONG", "CS_DOWNSTREAM_X_WEAK", "CS_UPSTREAM_Y"]
    fams = ["F_C_X", "F_C_X", "F_D_XW", "F_U_Y"]
    g = independence_groups(sids, fams)
    assert g["CS_CENTER_X_WEAK"] == g["CS_CENTER_X_STRONG"] == g["CS_DOWNSTREAM_X_WEAK"]  # family + replica links
    assert g["CS_UPSTREAM_Y"] != g["CS_CENTER_X_WEAK"]
    assert ancestor("CS_DOWNSTREAM_X_WEAK") == "X_WEAK"
    with pytest.raises(ValueError):
        ancestor("BADID")


def _support_fixture():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(0, 0.01, (30, 2)), rng.normal(5, 0.01, (30, 2))])
    y = ["LEAK"] * 30 + ["NORMAL"] * 30
    fam = ["FA"] * 15 + ["FB"] * 15 + ["FN1"] * 30  # two LEAK families ...
    scen = ["CS_T1_S"] * 15 + ["CS_T2_S"] * 15 + ["CS_T1_N"] * 30  # ... that are replicas of ONE scenario
    return X, y, fam, scen


def test_support_units_count_replicas_once_and_default_is_unchanged():
    X, y, fam, scen = _support_fixture()
    cfg = DConfig(k=10, min_class_reference=5, min_top_class_families=2, min_distinct_scenarios=1)
    q = np.array([[0.0, 0.0]])
    base = EmpiricalSupport(cfg).fit(X, y, fam, scen, CL).compute(q, query_families=["OTHER"])
    assert "TOP_CLASS_FEW_INDEPENDENT_RUNS" not in base.support_flags.iloc[0]  # protocol 1.1: 2 families pass
    units = pd.Series(scen).map(independence_groups(scen, fam)).to_numpy()
    grp = EmpiricalSupport(cfg).fit(X, y, fam, scen, CL, support_units=units).compute(q, query_families=["OTHER"])
    assert "TOP_CLASS_FEW_INDEPENDENT_RUNS" in grp.support_flags.iloc[0]  # one independence group: blocked
    assert base.D.iloc[0] == grp.D.iloc[0]  # the statistic itself is unchanged; only the support count differs


# ------------------------------------------------------------------ evidence-consistency policy (P2-D)
def _pc(**kw):
    return PolicyConfig(config_id="t", tau_accept=0.0, ambiguity_mass=0.9, max_set_size=2, singleton_handling="unresolved",
                        threshold_source="development", **kw)


def test_evidence_conflict_yields_the_two_competing_hypotheses_not_a_verdict():
    P = np.array([[0.9, 0.05, 0.03, 0.02], [0.9, 0.05, 0.03, 0.02]])
    out = apply_policy(P, [1.0, 1.0], CL, _pc(evidence_conflict="ambiguity_pair"), evidence_top_class=["LEAK", "NORMAL"])
    assert out.policy_outcome.tolist() == ["AMBIGUITY_SET", "SPECIFIC"]
    assert out.ambiguity_set.iloc[0] == "NORMAL|LEAK" and out.reason_code.iloc[0] == "EVIDENCE_CONFLICT:NORMAL|LEAK"
    un = apply_policy(P, [1.0, 1.0], CL, _pc(evidence_conflict="unresolved"), evidence_top_class=["LEAK", "NORMAL"])
    assert un.policy_outcome.tolist() == ["UNRESOLVED", "SPECIFIC"]


def test_policy_default_is_identical_to_protocol_1_1():
    rng = np.random.default_rng(1)
    P = rng.dirichlet(np.ones(4), size=200)
    s = rng.uniform(size=200)
    flags = rng.choice(["", "TOP_CLASS_FEW_INDEPENDENT_RUNS", "OUT_OF_SUPPORT"], size=200).tolist()
    kw = dict(specific_blocking_flags=("TOP_CLASS_FEW_INDEPENDENT_RUNS",))
    a = apply_policy(P, s, CL, _pc(**kw), flags=flags)
    b = apply_policy(P, s, CL, _pc(evidence_conflict=None, **kw), flags=flags, evidence_top_class=["LEAK"] * 200)
    pd.testing.assert_frame_equal(a, b)
    with pytest.raises(ValueError):
        apply_policy(P, s, CL, _pc(evidence_conflict="ambiguity_pair"), flags=flags)  # evidence is mandatory then


def test_available_excludes_conflicts_only_under_the_candidate_policy():
    pol = {"unresolved_flags": ["OUT_OF_SUPPORT"], "specific_blocking_flags": []}
    yh, ev = np.array(["LEAK", "LEAK"], dtype=object), np.array(["LEAK", "NORMAL"], dtype=object)
    assert pp._available(np.zeros(2), ["", ""], pol).tolist() == [True, True]
    assert pp._available(np.zeros(2), ["", ""], {**pol, "evidence_conflict": "ambiguity_pair"}, yh, ev).tolist() == [True, False]


# ------------------------------------------------------------------ development-only target rule (P2-E)
def test_development_target_rule_uses_development_attainability_only():
    assert development_target([0.569])["target"] == 0.5
    assert development_target([0.569, 0.07])["status"] == "NOT_ESTIMABLE_BY_DESIGN"
    assert development_target([0.95])["target"] == 0.9


# ------------------------------------------------------------------ runner options on the synthetic fixture
@pytest.fixture()
def fx(tmp_path):
    return make_fixture(tmp_path / "fx")


def _write(fx, cfg):
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode("utf-8"))


def test_candidate_options_run_end_to_end_on_synthetic_data(fx, tmp_path):
    cfg = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    cfg["features"]["channels"] = ["PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "PS7", "PS8", "PS9", "PS10", "MFS1", "MFS2", "MFS3"]
    cfg["distinguishability"]["support_unit"] = "independence_group"
    cfg["policy_primary"]["evidence_conflict"] = "ambiguity_pair"
    cfg.setdefault("combined_scores", {})["on_undefined"] = "not_estimable"
    _write(fx, cfg)
    res = pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "synthetic")
    assert res["status"] == "COMPLETED"  # includes the runner's own check: matched count == SPECIFIC issued
    m = json.loads((tmp_path / "o" / "run_manifest.json").read_text())
    assert m["features"]["n_features"] == 13 * len(cfg["features"]["statistics"])
    dec = pd.read_parquet(tmp_path / "o" / "decisions.parquet")
    prim = dec[dec.variant == "primary"]
    conflicts = prim[prim.reason_code.fillna("").str.startswith("EVIDENCE_CONFLICT")]
    # every conflict decision is the two-hypothesis set, never a SPECIFIC verdict
    assert (conflicts.policy_outcome == "AMBIGUITY_SET").all() and (conflicts.set_size == 2).all()


def test_unknown_channel_and_topology_column_are_rejected(fx, tmp_path):
    cfg = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    cfg["features"]["channels"] = ["PS1", "NOT_A_SENSOR"]
    _write(fx, cfg)
    with pytest.raises(pp.PreflightError, match="unknown sensors"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "synthetic")
    cfg["features"].pop("channels")
    cfg["dataset"]["topology_column"] = "no_such_column"
    _write(fx, cfg)
    with pytest.raises(pp.PreflightError, match="topology_column"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o2", "synthetic")


def test_meta_model_undefined_is_recorded_not_estimable_only_when_opted_in(fx, tmp_path, monkeypatch):
    real = pp.fit_combined_score

    def degenerate(*a, **k):
        raise ValueError("development data contain a single correctness outcome; meta-model not estimable")

    monkeypatch.setattr(pp, "fit_combined_score", degenerate)
    with pytest.raises(ValueError, match="single correctness outcome"):  # protocol 1.1: the run stops (fail closed)
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "synthetic")
    cfg = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    cfg.setdefault("combined_scores", {})["on_undefined"] = "not_estimable"
    _write(fx, cfg)
    res = pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o2", "synthetic")
    assert res["status"] == "COMPLETED"
    est = pd.read_csv(tmp_path / "o2" / "estimability.csv")
    sc = est[est.method.isin(["s_C", "s_C_minus_D"])]
    assert len(sc) and (sc.status != "ESTIMABLE").all()  # never a fallback score
    assert set(est.method) >= {"confidence", "margin", "neg_entropy", "D_only"}  # other comparators still evaluated
    pred = pd.read_parquet(tmp_path / "o2" / "predictions.parquet")
    assert pred.score_s_C.isna().all() and pred.score_confidence.notna().all()
    monkeypatch.setattr(pp, "fit_combined_score", real)


def test_candidate_protocol_config_is_refused_by_preflight():
    p = ROOT / "06_audit_preparation" / "protocol2" / "CANDIDATE_PROTOCOL_2_0.yaml"
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert cfg["status"] == "CANDIDATE_PROTOCOL_2_0_NOT_APPROVED"
    with pytest.raises(pp.PreflightError, match="config_status"):
        pp.preflight(cfg, ROOT, ROOT / "data" / "raw", "noise_added", pp.REAL_STATUS)


def test_candidate_manifest_v03_is_inactive_and_integrity_checked():
    chk = json.loads((ROOT / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03_CHECKS.json").read_text())
    assert chk["status"].startswith("CANDIDATE_NOT_ACTIVE") and chk["all_checks_passed"] and chk["n_topology_changed"] == 36
    pinned = yaml.safe_load((ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))
    assert "V02" in pinned["dataset"]["manifest"]["file"] and "topology_column" not in pinned["dataset"]
