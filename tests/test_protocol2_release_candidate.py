"""Focused tests: D2 sensor correspondence, position map (fail-closed), release candidate RC1 blocking, arm H
registration, B-vs-G1 high-confidence metric definitions, consolidated comparison labels, R2 immutability."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from h2prism.experiments import primary_protocol as pp
from h2prism.position_map import PositionMapError, apply_position_map, canonical_channels, load_position_map

REPO = Path(__file__).resolve().parents[1]
P2 = REPO / "06_audit_preparation" / "protocol2"
CORR = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "SENSOR_CORRESPONDENCE.csv"
PMAP = P2 / "CANDIDATE_SENSOR_POSITION_MAP_V01.csv"
RC = P2 / "release_candidate" / "P2_0_RC1.yaml"
ARM_H = P2 / "arms" / "H_POSITION_MATCHED.yaml"
HC = REPO / "03_results" / "diagnostics" / "high_confidence" / "HIGH_CONFIDENCE_ERRORS.csv"
CONS = REPO / "03_results" / "consolidated" / "CONSOLIDATED_COMPARISON.csv"


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


# ---------------------------------------------------------------- D2 sensor evidence
def test_correspondence_verdicts_from_diagram():
    c = pd.read_csv(CORR)
    v = c.drop_duplicates("sensor_id").set_index("sensor_id").verdict
    for s in ("PS1", "PS2", "PS3", "MFS1", "MFS2", "MFS3"):
        assert v[s] == "VERIFIED_SAME_BLOCK_SAME_NODE"
    assert v["PS4"] == "SAME_BLOCK_DIFFERENT_JUNCTION"
    for s in ("PS5", "PS6", "PS7", "PS8", "PS9", "PS10"):
        assert v[s] == "DIFFERENT_PHYSICAL_SENSOR_IN_DOWN"
    for s in ("PS11", "PS12", "MFS4"):
        assert v[s] == "DOWN_ONLY_SENSOR"
    # the down model logs center/up PS5 (block 187) under PS6
    d = c[(c.model == "down") & (c.sensor_id == "PS6")].iloc[0]
    assert int(d.sensor_block_sid) == 187 and "center:PS5" in d.same_block_logged_elsewhere_as
    assert (c[c.logged.astype(bool)].verification_status == "VERIFIED_FROM_DIAGRAM").all()


def test_correspondence_has_no_absolute_paths():
    text = CORR.read_text(encoding="utf-8")
    assert ":\\" not in text and "/Users/" not in text


# ---------------------------------------------------------------- position map
def test_position_map_content_and_hash():
    m = load_position_map(PMAP)
    assert canonical_channels(m) == ["MFS1", "MFS2", "MFS3", "PS1", "PS2", "PS3", "PS4", "PS5", "PS6", "PS7", "PS9", "PS10"]
    ren = m[m.renamed.astype(bool)]
    assert set(ren.topology) == {"Downstream"}
    assert dict(zip(ren.canonical_channel, ren.source_channel)) == {"PS5": "PS6", "PS6": "PS7", "PS7": "PS8",
                                                                     "PS9": "PS11", "PS10": "PS12"}
    pinned = (P2 / "CANDIDATE_SENSOR_POSITION_MAP_V01.sha256").read_text().split()[0]
    assert pinned == _sha(PMAP)
    load_position_map(PMAP, pinned)
    with pytest.raises(PositionMapError):
        load_position_map(PMAP, "0" * 64)


def _toy():
    ft = pd.DataFrame({"window_id": ["a", "b"], "topology": ["Center", "Downstream"],
                       "PS5__mean": [1.0, 9.0], "PS6__mean": [2.0, 1.5]})
    pm = pd.DataFrame({"canonical_channel": ["PS5", "PS5"], "topology": ["Center", "Downstream"],
                       "source_channel": ["PS5", "PS6"]})
    return ft, pm


def test_apply_position_map_reads_each_rows_own_column():
    ft, pm = _toy()
    out = apply_position_map(ft, pm, ["mean"])
    assert out["PS5__mean"].tolist() == [1.0, 1.5]
    assert "PS6__mean" not in out.columns  # unmapped channels never survive


def test_apply_position_map_fails_closed(tmp_path):
    ft, pm = _toy()
    with pytest.raises(PositionMapError):
        apply_position_map(ft.assign(topology=["Center", "Upstream"]), pm, ["mean"])  # unmapped topology
    with pytest.raises(PositionMapError):
        apply_position_map(ft, pm.iloc[:1], ["mean"])  # rows of a topology the map does not cover
    extra = pd.concat([pm, pd.DataFrame({"canonical_channel": ["PS1"], "topology": ["Center"], "source_channel": ["PS1"]})])
    with pytest.raises(PositionMapError, match="not mapped"):
        apply_position_map(ft, extra, ["mean"])  # canonical channel missing for one topology
    with pytest.raises(PositionMapError):
        apply_position_map(ft, pm, ["std"])  # missing source column
    p = tmp_path / "dup.csv"
    pd.concat([pm, pm.iloc[:1]]).to_csv(p, index=False)
    with pytest.raises(PositionMapError):
        load_position_map(p)


# ---------------------------------------------------------------- release candidate + arm H
def test_rc1_is_pinned_blocked_and_component_decisions():
    rc = yaml.safe_load(RC.read_text(encoding="utf-8"))
    assert rc["status"] == "RELEASE_CANDIDATE_P2_0_RC1_NOT_APPROVED"
    assert (P2 / "release_candidate" / "P2_0_RC1.sha256").read_text().split()[0] == _sha(RC)
    assert rc["execution"]["confirmatory"] == "BLOCKED"
    assert set(rc["owner_signoffs"].values()) == {"NOT_RECORDED"}
    comp = {k: v["decision"] for k, v in rc["components"].items()}
    assert comp["C"] == "EXCLUDED" and comp["F"] == "EXCLUDED" and comp["E"] == "OPTIONAL_DEFAULT_OFF"
    assert comp["B"] == "INCLUDED_CONDITIONAL" and comp["C_prime"] == "INCLUDED_CONDITIONAL"
    assert "evidence_conflict" not in rc["policy_primary"]
    assert rc["distinguishability"].get("statistic", "D") == "D"
    assert rc["distinguishability"]["support_unit"] == "independence_group"
    assert rc["evaluation"]["uncertainty"]["unit"] == "independence_group"
    assert rc["evaluation"]["primary_comparison"] == "s_C_vs_s_C_minus_D"
    assert rc["combined_scores"]["on_undefined"] == "not_estimable"
    assert rc["features"]["position_map"]["sha256"] == _sha(PMAP)
    assert rc["features"]["channels"] == canonical_channels(load_position_map(PMAP))
    assert rc["dataset"]["topology_column"] == "topology_source_model"
    assert "NOT physical distinguishability" in rc["distinguishability"]["semantics"]


def test_rc1_refused_for_execution_even_with_well_formed_authorization(tmp_path):
    auth = tmp_path / "auth.yaml"
    auth.write_text(yaml.safe_dump({"authorized": True, "scope": "PRIMARY_EXPERIMENT", "config_sha256": _sha(RC),
                                    "authorized_by": "unit-test fixture (not a real authorization)", "date": "2026-11-13",
                                    "governance_clearance": {k: "ATTESTED unit test" for k in pp.REQUIRED_CLEARANCES}}))
    with pytest.raises(pp.PreflightError, match="config_status"):
        pp.run(RC, REPO, tmp_path, tmp_path / "out", "execute", artifact_class="PRIMARY_EXPERIMENT", authorization=auth)
    with pytest.raises(pp.AuthorizationError):
        pp.run(RC, REPO, tmp_path, tmp_path / "out2", "develop")
    with pytest.raises(pp.AuthorizationError):
        pp.run(RC, REPO, tmp_path, tmp_path / "out3", "execute", artifact_class="PRIMARY_EXPERIMENT")


def test_arm_h_registered_and_authorization_bound_to_config(tmp_path):
    h = yaml.safe_load(ARM_H.read_text(encoding="utf-8"))
    assert h["status"] == pp.DEV_ARM_STATUS and h["arm_id"] == "H_POSITION_MATCHED"
    assert h["features"]["position_map"]["sha256"] == _sha(PMAP)
    add = pd.read_csv(P2 / "ABLATION_MATRIX_ADDENDUM_H.csv").iloc[0]
    assert add.config_sha256 == _sha(ARM_H)  # registered config is the one that was authorized and run
    auth = yaml.safe_load((P2 / "arm_authorizations" / "AUTH_H_POSITION_MATCHED.yaml").read_text(encoding="utf-8"))
    assert auth["scope"] == "DEVELOPMENT_EXPERIMENT:H_POSITION_MATCHED" and auth["config_sha256"] == _sha(ARM_H)
    assert "confirmatory" in auth["not_covered"] and "RC1 freeze" in auth["not_covered"]
    with pytest.raises(pp.AuthorizationError):  # no authorization given -> refused
        pp.run(ARM_H, REPO, tmp_path, tmp_path / "o", "develop")
    with pytest.raises(pp.AuthorizationError):  # the arm-H grant does not authorize RC1 or any outer-test execution
        pp.run(RC, REPO, tmp_path, tmp_path / "o2", "execute", artifact_class="PRIMARY_EXPERIMENT",
               authorization=P2 / "arm_authorizations" / "AUTH_H_POSITION_MATCHED.yaml")


# ---------------------------------------------------------------- high-confidence calculation
def test_high_confidence_definitions_are_consistent():
    h = pd.read_csv(HC)
    for r in h.itertuples():
        if r.n_errors:
            assert np.isclose(r.share_of_errors_confident, r.n_confident_errors / r.n_errors)
        if r.n_confident:
            assert np.isclose(r.error_rate_among_confident, r.n_confident_errors / r.n_confident)
    pooled = h[h.scope == "pooled_window_fold_instances"].set_index("arm_id")
    # the stored ARM_SUMMARY metric is the share of ERRORS (denominator = errors), not an error rate
    arm = pd.read_csv(REPO / "03_results" / "ablation" / "ARM_SUMMARY.csv").set_index("arm_id")
    for a in ("A_P11_DEV", "B_TOPOLOGY", "C_COMMON_SENSORS", "G1_DATA_CORRECTIONS"):
        assert np.isclose(arm.loc[a, "share_errors_conf_ge_0_9"], pooled.loc[a, "share_of_errors_confident"], atol=1e-5)
    assert pooled.loc["G1_DATA_CORRECTIONS", "confident_errors_independence_groups"] == 1
    b = h[(h.arm_id == "B_TOPOLOGY") & h.scope.isin(["fold_1", "fold_3"])]
    assert (b.n_confident < 100).all()  # B's 0.000 rests on almost no confident predictions outside fold 2


def test_consolidated_rows_are_labelled():
    c = pd.read_csv(CONS)
    assert set(c.evidence_status) == {"EXPLORATORY_DEVELOPMENT", "REGISTERED_PRIMARY_P11_DESCRIPTIVE"}
    assert (c[c.arm_id.str.startswith("R2")].evaluation_set.str.contains("not comparable")).all()


# ---------------------------------------------------------------- R2 immutability
def test_r2_outputs_match_frozen_hash_list():
    lst = REPO / "03_results" / "primary_protocol" / "logs" / "PRIMARY_a10530f1fcf2_OUTPUT_HASHES.sha256"
    base = REPO / "03_results" / "primary_protocol" / "PRIMARY"
    n = 0
    for line in lst.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        h, name = line.split(maxsplit=1)
        f = base / name.lstrip("*")
        if f.exists():  # git-ignored large files may be absent in a clean checkout
            assert _sha(f) == h, name
            n += 1
    assert n > 0


# ---------------------------------------------------------------- arm H results
def test_arm_h_outputs_match_hash_list_and_criteria():
    run = REPO / "03_results" / "ablation_runs" / "H_POSITION_MATCHED"
    import json
    man = json.loads((run / "run_manifest.json").read_text(encoding="utf-8"))
    assert man["status"] == "COMPLETED" and man["config_sha256"] == _sha(ARM_H)
    assert man["features"]["n_features"] == 96 and man["features"]["position_map"]["sha256"] == _sha(PMAP)
    lst = REPO / "03_results" / "ablation_runs" / "logs" / f"H_POSITION_MATCHED_{man['run_key'][:12]}_OUTPUT_HASHES.sha256"
    for line in lst.read_text(encoding="utf-8").splitlines():
        h, name = line.split(maxsplit=1)
        f = run / name.lstrip("*")
        if f.exists():
            assert _sha(f) == h, name
    acc = pd.read_csv(REPO / "03_results" / "ablation" / "ARM_H_ACCEPTANCE.csv")
    assert len(acc) == 3 and set(acc.evidence_status) == {"EXPLORATORY_DEVELOPMENT"}
    s = pd.read_csv(REPO / "03_results" / "ablation" / "ARM_H_SUMMARY.csv").set_index("arm_id")
    h_, g_ = s.loc["H_POSITION_MATCHED"], s.loc["G1_DATA_CORRECTIONS"]
    expect = [h_.n_features == 96, h_.oos_share_folds_with_down < g_.oos_share_folds_with_down,
              h_.dev_group_balanced_accuracy_mean >= g_.dev_group_balanced_accuracy_mean - 0.05]
    assert acc.result.tolist() == ["PASS" if e else "FAIL" for e in expect]
