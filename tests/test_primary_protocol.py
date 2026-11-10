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
    a, ra = pp.outer_stage(cfg, dev, test, feats, devres)
    test2 = test.copy()
    test2["label_mapped"] = np.random.default_rng(0).permutation(test2.label_mapped.to_numpy())
    b, rb = pp.outer_stage(cfg, dev, test2, feats, devres)
    for x, y in zip(ra, rb):
        assert x["status"] == y["status"]
        if x["status"] == "ESTIMABLE":
            pd.testing.assert_frame_equal(x["decisions"], y["decisions"])


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
