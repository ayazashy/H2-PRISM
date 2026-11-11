"""
End-to-end and edge-case tests of the REAL runner (h2prism.experiments.primary_protocol and
tools/experiments/run_primary_protocol.py) on the SYNTHETIC protocol fixture. No real data.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from h2prism.experiments import primary_protocol as pp
from h2prism.experiments.synthetic_protocol_fixture import make_fixture

ROOT = Path(__file__).resolve().parents[1]


def _rehash(fx):
    cfg = yaml.safe_load(fx["config"].read_text(encoding="utf-8"))
    cfg["dataset"]["manifest"]["sha256"] = hashlib.sha256(fx["manifest"].read_bytes()).hexdigest()
    cfg["splits"]["outer"]["sha256"] = hashlib.sha256(fx["folds"].read_bytes()).hexdigest()
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode("utf-8"))
    return cfg


def _run(fx, out, **kw):
    return pp.run(fx["config"], fx["root"], fx["raw"], out, kw.pop("mode", "synthetic"), **kw)


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    d = tmp_path_factory.mktemp("proto")
    fx = make_fixture(d / "fx")
    res = _run(fx, d / "out")
    return fx, d, res


# 1, 10, 11, 16 -------------------------------------------------------------
def test_valid_config_end_to_end(base):
    fx, d, res = base
    assert res["status"] == "COMPLETED" and res["artifact_class"] == "SYNTHETIC_TEST"
    for f in ("run_manifest.json", "coverage_risk.csv", "estimability.csv", "rq1.csv", "rq2.csv", "calibration_records.json"):
        assert (d / "out" / f).exists()
    for f in ("coverage_risk.csv", "estimability.csv", "rq1.csv", "rq2.csv"):
        assert set(pd.read_csv(d / "out" / f).artifact_class) == {"SYNTHETIC_TEST"}
    cr = res["coverage_risk"]
    assert ((cr.n_specific + cr.n_ambiguity + cr.n_unresolved) == cr.n_eligible).all()


def test_sparse_support_flag_and_unattainable_primary_target(base):
    fx, d, res = base
    th = pd.concat([pd.read_csv(d / "out" / "folds" / f"fold_{k}" / "thresholds.csv") for k in (1, 2, 3)])
    prim = th[(th.variant == "primary") & (th.target == 0.8)]
    assert (prim.dev_status == "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL").all()
    assert (prim.dev_max_attainable_coverage < 0.8).all()
    import json
    cal = json.loads((d / "out" / "calibration_records.json").read_text())
    assert all(any("TOP_CLASS_FEW_INDEPENDENT_RUNS" in k for k in c["dev_support_flags"]) for c in cal)
    rq1 = res["rq1"]
    assert (rq1[(rq1.variant == "primary") & (rq1.target == 0.8)].status == "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL").all()
    assert {"realized_coverage_a", "realized_coverage_b"} <= set(rq1.columns)


def test_synthetic_output_refused_inside_results_dir(base):
    fx, d, res = base
    with pytest.raises(pp.PreflightError, match="03_results"):
        _run(fx, ROOT / "03_results" / "should_not_exist")
    assert not (ROOT / "03_results" / "should_not_exist").exists()


# 2, 3, 4, 5, 7, 8 -----------------------------------------------------------
@pytest.fixture
def fx(tmp_path):
    return make_fixture(tmp_path / "fx")


def test_missing_manifest(fx, tmp_path):
    fx["manifest"].unlink()
    with pytest.raises(pp.PreflightError, match="manifest.csv"):
        _run(fx, tmp_path / "o")


def test_hash_mismatch(fx, tmp_path):
    fx["folds"].write_bytes(fx["folds"].read_bytes() + b"\n")
    with pytest.raises(pp.PreflightError, match="hash:folds.csv"):
        _run(fx, tmp_path / "o")


def test_duplicate_family_across_topologies(fx, tmp_path):
    m = pd.read_csv(fx["manifest"])
    m.loc[m.Scenario_ID == "SYN_TB_NORMAL_0", "Scenario_Family_ID"] = "SYN_FAM_TA_N"
    fx["manifest"].write_bytes(m.to_csv(index=False, lineterminator="\n").encode())
    _rehash(fx)
    with pytest.raises(pp.PreflightError, match="families_nest_in_topology|fold_family_isolation"):
        _run(fx, tmp_path / "o")


def test_topology_leakage_in_folds(fx, tmp_path):
    f = pd.read_csv(fx["folds"])
    f.loc[(f.outer_fold_id == 1) & (f.Scenario_ID == "SYN_TA_LEAK_1"), "split_role"] = "train"
    fx["folds"].write_bytes(f.to_csv(index=False, lineterminator="\n").encode())
    _rehash(fx)
    with pytest.raises(pp.PreflightError, match="fold_topology_isolation|fold_family_isolation"):
        _run(fx, tmp_path / "o")


def test_invalid_event_label(fx, tmp_path):
    m = pd.read_csv(fx["manifest"])
    m.loc[m.Scenario_ID == "SYN_TA_NORMAL_0", "label_mapped"] = "LEAKY"
    fx["manifest"].write_bytes(m.to_csv(index=False, lineterminator="\n").encode())
    _rehash(fx)
    with pytest.raises(pp.PreflightError, match="classes"):
        _run(fx, tmp_path / "o")


def test_insufficient_class_support_in_training(fx, tmp_path):
    m = pd.read_csv(fx["manifest"])
    drop = m.label_mapped.eq("COMPRESSOR_DELAY") & ~m.topology.eq("TA")
    m.loc[drop, ["eligible_primary", "exclusion_reason"]] = [False, "test: removed"]
    fx["manifest"].write_bytes(m.to_csv(index=False, lineterminator="\n").encode())
    f = pd.read_csv(fx["folds"])
    f = f[f.Scenario_ID.isin(m[m.eligible_primary].Scenario_ID)]
    fx["folds"].write_bytes(f.to_csv(index=False, lineterminator="\n").encode())
    cfg = _rehash(fx)
    cfg["dataset"]["eligible_runs"] = int(m.eligible_primary.sum())
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode())
    with pytest.raises(pp.PreflightError, match="MISSING_TRAIN_CLASS"):
        _run(fx, tmp_path / "o")


# 6, 9, 12, 13 ---------------------------------------------------------------
def test_outer_test_labels_do_not_influence_decisions(base):
    fx, d, _ = base
    cfg = yaml.safe_load(fx["config"].read_text())
    ft, _ = pp.build_features(cfg, fx["root"], fx["raw"], "noise_added")
    feats = [c for c in ft.columns if "__" in c]
    dev, test = ft[ft.topology != "TA"], ft[ft.topology == "TA"]
    devres = pp.development_stage(cfg, dev, feats)
    a, ra, ta, ca = pp.outer_stage(cfg, dev, test, feats, devres)
    test2 = test.copy()
    test2["label_mapped"] = np.random.default_rng(0).permutation(test2.label_mapped.to_numpy())
    b, rb, tb, cb = pp.outer_stage(cfg, dev, test2, feats, devres)
    for x, y in zip(ra, rb):
        assert x["status"] == y["status"]
        if x["status"] == "ESTIMABLE":
            pd.testing.assert_frame_equal(x["decisions"], y["decisions"])
    # tie-sensitivity selections are label-free too (only the error counts may differ)
    pd.testing.assert_series_equal(ta.n_selected, tb.n_selected)
    pd.testing.assert_series_equal(ca.n_selected, cb.n_selected)  # curve selections are label-free


def test_calibration_fallback_recorded(fx, tmp_path):
    cfg = yaml.safe_load(fx["config"].read_text())
    cfg["calibration"]["feasibility_rule"]["min_groups_per_class"] = 3  # only 2 topologies in development
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode())
    res = _run(fx, tmp_path / "o")
    import json
    cal = json.loads((tmp_path / "o" / "calibration_records.json").read_text())
    assert {c["method"] for c in cal} == {"none"} and all(c["feasibility"]["allowed_methods"] == ["none"] for c in cal)


def _rows(outcome, sets, ypred):
    return pd.DataFrame({"policy_outcome": outcome, "y_pred_specific": ypred, "ambiguity_set": sets,
                         "set_size": [len(s.split("|")) if s else 0 for s in sets], "reason_code": "x",
                         "policy_config_id": "t", "window_id": ["w0", "w1"]})


def _preds():
    return pd.DataFrame({"window_id": ["w0", "w1"], "y_true": ["LEAK", "NORMAL"], "Scenario_Family_ID": ["f0", "f1"],
                         "topology": ["TA", "TA"], "fold": [1, 1]})


def test_empty_specific_reports_undefined_risk():
    cfg = {"dataset": {"classes": ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]}}
    rows = [{"fold": 1, "variant": "primary", "method": m, "target": 0.8, "mode": "threshold_transfer", "status": "ESTIMABLE",
             "test_max_attainable_coverage": 0.0, "decisions": _rows(["UNRESOLVED", "UNRESOLVED"], ["", ""], [None, None])}
            for m in ("s_C", "s_C_minus_D")]
    agg = pp.aggregate(cfg, _preds(), rows, "SYNTHETIC_TEST")
    r = agg["coverage_risk"].iloc[0]
    assert r.coverage == 0 and np.isnan(r.selective_risk) and not r.selective_risk_defined


def test_invalid_ambiguity_set_rejected():
    cfg = {"dataset": {"classes": ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]}}
    rows = [{"fold": 1, "variant": "primary", "method": "s_C", "target": 0.8, "mode": "threshold_transfer", "status": "ESTIMABLE",
             "test_max_attainable_coverage": 0.0, "decisions": _rows(["AMBIGUITY_SET", "UNRESOLVED"], ["LEAK", ""], [None, None])}]
    with pytest.raises(AssertionError, match="invalid ambiguity sets"):
        pp.aggregate(cfg, _preds(), rows, "SYNTHETIC_TEST")


# 14, 15 ---------------------------------------------------------------------
def test_deterministic_and_resumable(base, tmp_path):
    fx, d, _ = base
    with pytest.raises(InterruptedError):
        _run(fx, tmp_path / "o", stop_after_fold=1)
    assert (tmp_path / "o" / "folds" / "fold_1" / "DONE.json").exists() and not (tmp_path / "o" / "rq1.csv").exists()
    _run(fx, tmp_path / "o")  # resumes: fold 1 reloaded, folds 2-3 computed
    for f in ("coverage_risk.csv", "estimability.csv", "rq1.csv", "rq2.csv"):
        assert (tmp_path / "o" / f).read_bytes() == (d / "out" / f).read_bytes(), f


# 17 + CLI -------------------------------------------------------------------
def test_outer_test_disabled_without_authorization(fx, tmp_path):
    with pytest.raises(pp.AuthorizationError):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "execute", artifact_class="PRIMARY_EXPERIMENT")
    auth = tmp_path / "auth.yaml"
    auth.write_text(yaml.safe_dump({"authorized": True, "scope": "PRIMARY_EXPERIMENT", "config_sha256": "0" * 64,
                                    "authorized_by": "x", "date": "2026-01-01"}))
    with pytest.raises(pp.AuthorizationError, match="config_sha256"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "execute", artifact_class="PRIMARY_EXPERIMENT", authorization=auth)
    assert not (tmp_path / "o" / "folds").exists()


def test_cli_dry_run_never_fits_or_enters_outer_stage(fx, tmp_path):
    r = subprocess.run([sys.executable, str(ROOT / "tools/experiments/run_primary_protocol.py"), "--config", str(fx["config"]),
                        "--root", str(fx["root"]), "--raw-parent", str(fx["raw"]), "--out", str(tmp_path / "o")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    import json
    man = json.loads((tmp_path / "o" / "run_manifest.json").read_text())
    assert man["artifact_class"] == "PREFLIGHT_ONLY" and man["status"] == "PREFLIGHT_PASSED"
    assert not (tmp_path / "o" / "folds").exists()
    r2 = subprocess.run([sys.executable, str(ROOT / "tools/experiments/run_primary_protocol.py"), "--config", str(fx["config"]),
                         "--root", str(fx["root"]), "--raw-parent", str(fx["raw"]), "--out", str(tmp_path / "o2"),
                         "--execute-primary"], capture_output=True, text=True)
    assert r2.returncode == 2 and "AuthorizationError" in r2.stderr


# Phase 9: PA-1 matched coverage, resume safety, adversarial inputs, reordering -----------------
def test_rank_matched_coverage_is_exactly_matched(base):
    fx, d, res = base
    rq1 = res["rq1"]
    rm = rq1[(rq1["mode"] == "rank_matched") & (rq1.status == "ESTIMABLE")]
    assert len(rm) > 0
    assert (rm.realized_coverage_a == rm.realized_coverage_b).all() and (rm.coverage_gap_a_minus_b == 0).all()
    est = res["estimability"]
    e = est[(est["mode"] == "rank_matched") & (est.status == "ESTIMABLE")]
    assert (e.requested_count == e.realized_count).all()
    ne = est[(est["mode"] == "rank_matched") & (est.status != "ESTIMABLE")]
    assert ne.realized_count.isna().all()  # unattainable targets are never forced
    ts = pd.read_csv(d / "out" / "tie_sensitivity.csv")
    assert len(ts) and set(ts.role) == {"TIE_ORDER_SENSITIVITY_SECONDARY"} and set(ts.artifact_class) == {"SYNTHETIC_TEST"}


def test_rq2_reporting_labels_come_from_config(base):
    fx, d, res = base
    rq2 = res["rq2"]
    assert set(rq2[rq2["class"] == "LEAK"].reporting) == {"restricted"}
    assert set(rq2[rq2["class"] != "LEAK"].reporting) <= {"descriptive_only"}


def test_missing_tie_rule_fails_closed(fx, tmp_path):
    cfg = yaml.safe_load(fx["config"].read_text())
    del cfg["thresholds"]["matched_coverage"]
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode())
    with pytest.raises(pp.PreflightError, match="matched_coverage_rule_prespecified"):
        _run(fx, tmp_path / "o")


def test_output_dir_of_a_different_run_is_refused(base, tmp_path):
    fx, d, _ = base
    out = tmp_path / "o"
    out.mkdir()
    (out / "run_manifest.json").write_text('{"run_key": "deadbeef", "status": "COMPLETED"}')
    with pytest.raises(pp.PreflightError, match="different run"):
        _run(fx, out)
    assert not (out / "folds").exists()


def test_missing_raw_file(fx, tmp_path):
    m = pd.read_csv(fx["manifest"])
    (fx["raw"] / m.file_noise_added.iloc[0]).unlink()
    with pytest.raises(pp.PreflightError, match="raw_files_present_and_unmodified"):
        _run(fx, tmp_path / "o")


def test_modified_raw_file(fx, tmp_path):
    m = pd.read_csv(fx["manifest"])
    f = fx["raw"] / m.file_noise_added.iloc[0]
    f.write_bytes(f.read_bytes() + b"x")
    with pytest.raises(pp.PreflightError, match="raw_files_present_and_unmodified"):
        _run(fx, tmp_path / "o")


def test_wrong_manifest_schema(fx, tmp_path):
    m = pd.read_csv(fx["manifest"]).drop(columns=["Scenario_Family_ID"])
    fx["manifest"].write_bytes(m.to_csv(index=False, lineterminator="\n").encode())
    _rehash(fx)
    with pytest.raises(pp.PreflightError, match="manifest_columns"):
        _run(fx, tmp_path / "o")


def test_inconsistent_fold_ids(fx, tmp_path):
    f = pd.read_csv(fx["folds"])
    f.loc[f.index[0], "Scenario_ID"] = "SYN_UNKNOWN_RUN"
    fx["folds"].write_bytes(f.to_csv(index=False, lineterminator="\n").encode())
    _rehash(fx)
    with pytest.raises(pp.PreflightError, match="folds_cover_eligible_runs_exactly"):
        _run(fx, tmp_path / "o")


def test_reordered_inputs_give_identical_results(base, tmp_path):
    fx0, d, _ = base
    fx = make_fixture(tmp_path / "fx")
    m = pd.read_csv(fx["manifest"]).iloc[::-1]
    fx["manifest"].write_bytes(m.to_csv(index=False, lineterminator="\n").encode())
    f = pd.read_csv(fx["folds"]).sample(frac=1.0, random_state=3)
    fx["folds"].write_bytes(f.to_csv(index=False, lineterminator="\n").encode())
    _rehash(fx)
    _run(fx, tmp_path / "o")
    for name in ("coverage_risk.csv", "estimability.csv", "rq1.csv", "rq2.csv", "tie_sensitivity.csv"):
        assert (tmp_path / "o" / name).read_bytes() == (d / "out" / name).read_bytes(), name


def test_rq1_reports_every_registered_comparison_without_omission(base):
    fx, d, res = base
    rq1 = res["rq1"]
    combos = rq1.groupby(["comparison_b", "variant", "target", "mode"]).size()
    assert (combos == 1).all() and len(combos) == 5 * 2 * 3 * 2
    assert set(rq1.comparison_b) == {"s_C_minus_D", "confidence", "margin", "neg_entropy", "D_only"}
    assert set(rq1[rq1.comparison_b == "s_C_minus_D"].comparison_role) == {"PRIMARY"}
    ne = rq1[rq1.status != "ESTIMABLE"]
    assert ne.difference.isna().all() and ne.realized_coverage_a.isna().all()  # never reported as zero


# Governance clearance in the execution gate ----------------------------------------------------
def _auth(tmp_path, cfg_sha, **over):
    a = {"authorized": True, "scope": "PRIMARY_EXPERIMENT", "config_sha256": cfg_sha, "authorized_by": "x", "date": "2026-01-01",
         "governance_clearance": {k: "ATTESTED test" for k in pp.REQUIRED_CLEARANCES}}
    a.update(over)
    p = tmp_path / "auth.yaml"
    p.write_text(yaml.safe_dump(a))
    return p


@pytest.mark.parametrize("gc", [None, {}, {"F-D15": "ATTESTED", "F-D16": "ATTESTED", "A-D10": "ATTESTED"},
                                {"F-D15": "pending", "F-D16": "ATTESTED", "A-D10": "WAIVED", "PA-1": "ATTESTED"}])
def test_missing_or_invalid_governance_clearance_refused(fx, tmp_path, gc):
    sha = pp.sha256_file(fx["config"])
    with pytest.raises(pp.AuthorizationError, match="governance_clearance"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "execute", artifact_class="PRIMARY_EXPERIMENT",
               authorization=_auth(tmp_path, sha, governance_clearance=gc))
    assert not (tmp_path / "o").exists()


def test_valid_clearance_passes_gate_but_not_status_check(fx, tmp_path):
    """A complete authorization only passes the gate; the synthetic config still fails the real-status preflight."""
    sha = pp.sha256_file(fx["config"])
    a = pp.check_authorization(_auth(tmp_path, sha), sha, "PRIMARY_EXPERIMENT")
    assert set(a["governance_clearance"]) == set(pp.REQUIRED_CLEARANCES)
    with pytest.raises(pp.PreflightError, match="config_status"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "execute", artifact_class="PRIMARY_EXPERIMENT",
               authorization=_auth(tmp_path, sha))
    assert not (tmp_path / "o" / "folds").exists()


def test_clearance_gate_does_not_alter_protocol():
    cfg = yaml.safe_load((ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))
    assert pp.sha256_file(ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml") == \
        "f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae"
    assert cfg["thresholds"]["matched_coverage"]["selection"] == "exact_count"
    assert cfg["evaluation"]["primary_comparison"] == "s_C_vs_s_C_minus_D"


# Registered sensitivity analyses: every one has an execution path (synthetic only here) ------------
SENS = ["clean_realization", "windows_60_60", "pre_event_label_normal", "offset_invariant_features",
        "k_10", "k_50", "prior_correction", "extended_family_map"]


def test_every_registered_sensitivity_has_an_override():
    cfg = yaml.safe_load((ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))
    assert set(cfg["sensitivity_analyses"]) == set(pp.SENSITIVITY_OVERRIDES)
    for name in SENS:
        c2 = pp.apply_sensitivity(cfg, name)
        diff = {k for k in c2 if c2[k] != cfg.get(k)} - {"sensitivity_applied"}
        assert len(diff) == 1, (name, diff)  # exactly one config section changes
    assert cfg == yaml.safe_load((ROOT / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def fx_pre(tmp_path_factory):
    return make_fixture(tmp_path_factory.mktemp("pre") / "fx", pre_event_rows=90)


@pytest.mark.parametrize("name", SENS)
def test_sensitivity_synthetic_path(fx_pre, tmp_path, name):
    res = pp.run(fx_pre["config"], fx_pre["root"], fx_pre["raw"], tmp_path / "o", "synthetic", sensitivity=name)
    assert res["status"] == "COMPLETED" and res["sensitivity"]["name"] == name
    assert res["effective_config_sha256"] != res["config_sha256"]
    for f in ("coverage_risk.csv", "estimability.csv", "rq1.csv", "rq2.csv"):
        t = pd.read_csv(tmp_path / "o" / f)
        assert set(t.analysis) == {name} and set(t.artifact_class) == {"SYNTHETIC_TEST"}
    rq1 = res["rq1"]
    assert set(rq1.status) <= {"ESTIMABLE", "NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL"}
    if name == "clean_realization":
        assert res["realization"] == "clean"
    if name == "offset_invariant_features":
        assert res["features"]["n_features"] == 16 * 5


def test_pre_event_sensitivity_changes_windows_but_primary_excludes_them(fx_pre, tmp_path):
    cfg = yaml.safe_load(fx_pre["config"].read_text())
    ft0, _ = pp.build_features(cfg, fx_pre["root"], fx_pre["raw"], "noise_added")
    ft1, _ = pp.build_features(pp.apply_sensitivity(cfg, "pre_event_label_normal"), fx_pre["root"], fx_pre["raw"], "noise_added")
    leak_runs = ft0[ft0.label_mapped == "LEAK"].Scenario_ID.unique()
    assert (ft0[ft0.Scenario_ID.isin(leak_runs)].label_mapped == "LEAK").all()
    assert (ft1[ft1.Scenario_ID.isin(leak_runs)].label_mapped == "NORMAL").any() and len(ft1) > len(ft0)


def test_policy_warning_only_is_embedded_in_every_run(base):
    fx, d, res = base
    assert {"primary", "warning_only"} <= set(res["coverage_risk"].variant)
    with pytest.raises(pp.PreflightError, match="produced by every run"):
        pp.apply_sensitivity(yaml.safe_load(fx["config"].read_text()), "policy_warning_only")


def test_unregistered_sensitivity_refused(fx, tmp_path):
    with pytest.raises(pp.PreflightError, match="not registered"):
        pp.apply_sensitivity({"sensitivity_analyses": ["k_10"]}, "k_50")


def test_sensitivity_execution_requires_its_own_scope(fx, tmp_path):
    sha = pp.sha256_file(fx["config"])
    with pytest.raises(pp.AuthorizationError, match="scope must be SENSITIVITY_EXPERIMENT:k_10"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "execute", artifact_class="SENSITIVITY_EXPERIMENT",
               authorization=_auth(tmp_path, sha), sensitivity="k_10")
    with pytest.raises(pp.AuthorizationError, match="requires --sensitivity"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "o", "execute", artifact_class="SENSITIVITY_EXPERIMENT",
               authorization=_auth(tmp_path, sha))
    assert not (tmp_path / "o").exists()


def test_inner_fold_record_must_match_runner_splits(fx, tmp_path):
    f = pd.read_csv(fx["folds"])
    m = pd.read_csv(fx["manifest"])
    topo = dict(zip(m.Scenario_ID, m.topology))
    rows = []
    for k, d in f.groupby("outer_fold_id"):
        tr = d[d.split_role == "train"].Scenario_ID
        for i, t in enumerate(sorted({topo[s] for s in tr})):
            val = sorted(s for s in tr if topo[s] == t)
            rows.append({"outer_fold_id": k, "scheme": "LOTO_within_train", "inner_split": i, "val_scenarios": ";".join(val)})
    good = pd.DataFrame(rows)
    p = fx["root"] / "inner.csv"
    good.to_csv(p, index=False, lineterminator="\n")
    cfg = _rehash(fx)
    cfg["splits"]["inner"] = {"file": "inner.csv", "sha256": pp.sha256_file(p)}
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode())
    assert pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "ok", "preflight")["status"] == "PREFLIGHT_PASSED"
    bad = good.copy()
    a, b = bad.val_scenarios.iloc[0].split(";"), bad.val_scenarios.iloc[1].split(";")
    bad.loc[bad.index[0], "val_scenarios"] = ";".join(a[1:] + b[:1])
    bad.loc[bad.index[1], "val_scenarios"] = ";".join(b[1:] + a[:1])
    bad.to_csv(p, index=False, lineterminator="\n")
    cfg["splits"]["inner"]["sha256"] = pp.sha256_file(p)
    fx["config"].write_bytes(yaml.safe_dump(cfg, sort_keys=True).encode())
    with pytest.raises(pp.PreflightError, match="inner_folds_match_runner"):
        pp.run(fx["config"], fx["root"], fx["raw"], tmp_path / "bad", "preflight")
