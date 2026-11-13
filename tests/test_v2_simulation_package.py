"""SIMULATION_GENERATION:V2_NORMAL_SUPPORT package v2: design invariants, fail-closed authorization, and an end-to-end
dry run (solver grid -> resampling -> noise -> validation -> seal) on FABRICATED MATLAB-shaped outputs in a temporary
folder. No real simulation is run and no data are produced in the repository."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support"
TOOLS = REPO / "tools" / "simulation"
sys.path.insert(0, str(TOOLS))

import postprocess_v2_normal_runs as post  # noqa: E402
import v2_normal_authorization as auth  # noqa: E402
import validate_v2_normal_outputs as val  # noqa: E402


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


D = pd.read_csv(PKG / "DESIGN.csv")
PTS = D.drop_duplicates("scenario_id")
REQ = yaml.safe_load((PKG / "AUTH_SIMULATION_GENERATION_V2_REQUEST.yaml").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ design
def test_design_is_balanced_excludes_released_point_and_partitions_in_advance():
    assert len(D) == 27 and set(D.model) == {"center", "down", "up"} and len(PTS) == 9
    assert not ((PTS.ps_step_final_value_MPa == 6.4) & (PTS.ps_ramp_slope_MPa_per_s == -1e-5)
                & (PTS.withdrawal_restriction_area_m2 == 1e-3)).any()
    for f in ("ps_step_final_value_MPa", "ps_ramp_slope_MPa_per_s", "withdrawal_restriction_area_m2"):
        assert set(PTS[f].value_counts()) == {3}
        assert set(PTS[PTS.partition == "confirmation"][f].value_counts()) == {1}
        assert set(PTS[PTS.partition == "development"][f].value_counts()) == {2}
    assert D.noise_seed.is_unique and (PKG / "DESIGN.sha256").read_text().split()[0] == _sha(PKG / "DESIGN.csv")
    existing = set(pd.read_csv(REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv").independence_group)
    assert not set(D.independence_group) & existing
    # one independence group per operating point, shared by its three model runs
    assert D.groupby("scenario_id").independence_group.nunique().eq(1).all() and D.independence_group.nunique() == 9


def test_static_operating_range_within_gas_property_limits():
    """Highest compressor outlet = supply reservoir (0.684 MPa) + largest lift must stay below the 10 MPa table limit."""
    assert 0.684 + PTS.ps_step_final_value_MPa.max() < 9.5
    assert (-0.3 + PTS.ps_ramp_slope_MPa_per_s.min() * 20000) > -1.0      # let-down differential stays moderate


# ------------------------------------------------------------------------------------------------ authorization
def test_v1_authorization_is_void_and_v2_request_is_bound_but_not_active():
    v1 = yaml.safe_load((PKG / "AUTH_SIMULATION_GENERATION.yaml").read_text(encoding="utf-8"))
    assert auth.evaluate(v1)                                      # void (hashes/package changed)
    assert auth.evaluate(REQ) == ["authorized is not true"]       # bound to the current files, only the grant missing
    with pytest.raises(auth.NotAuthorized):
        auth.require_active()
    hist = pd.read_csv(PKG / "AUTHORIZATION_HISTORY.csv")
    assert set(hist.status) == {"VOID_SUPERSEDED", "PENDING_PROJECT_LEAD_AUTHORIZATION"}


def test_tools_refuse_without_active_authorization(tmp_path):
    with pytest.raises(auth.NotAuthorized):
        post.main([str(tmp_path)])
    with pytest.raises(auth.NotAuthorized):
        val.main([str(tmp_path)])


def test_any_change_to_a_bound_file_voids_an_otherwise_active_record():
    rec = copy.deepcopy(REQ)
    rec["authorized"] = True
    assert auth.evaluate(rec) == []
    rec["bound_to"]["validator"]["sha256"] = "0" * 64
    assert any("validator" in w for w in auth.evaluate(rec))


# ------------------------------------------------------------------------------------------------ generator text
def test_generator_contract():
    m = (PKG / "generate_v2_normal_support.m").read_text(encoding="utf-8")
    assert "save_system" not in m and "close_system(mdl, 0)" in m and "copyfile" in m
    assert "isMATLABReleaseOlderThan('R2025a')" in m and "license('test', 'Simscape')" in m
    assert "load_system(fullfile(runDir" in m and "is not the private copy" in m
    assert "'preflight'" in m and "_FAILED.json" in m and "released model changed" in m
    for sid in ("59", "241", "213", "222", "312", "215"):
        assert f"'{sid}'" in m
    edges = pd.read_csv(REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "NETWORK_EDGES.csv")
    for model, g in edges[edges.scenario_kind == "normal"].groupby("model"):
        comps = " ".join(g.component)
        for sid in ("213", "222", "312", "215"):
            assert f"SID {sid};" in comps, (model, sid)


# ------------------------------------------------------------------------------------------------ dry run
@pytest.fixture
def active(monkeypatch):
    rec = copy.deepcopy(REQ)
    rec["authorized"], rec["authorized_by"], rec["date"] = True, "unit-test fixture (not a real grant)", "2026-11-13"
    monkeypatch.setattr(auth, "require_active", lambda path=None: rec)
    return rec


def _fabricate(out: Path, bad=None):
    """MATLAB-shaped outputs: solver-grid clean CSV (own sensor list) + provenance, physically NORMAL-like."""
    logged, rel = val.expected_logged(), val.released_hashes()
    rng = np.random.default_rng(0)
    for r in D.itertuples():
        d = out / r.partition
        d.mkdir(parents=True, exist_ok=True)
        base = d / f"{r.scenario_id}_{r.model}"
        t = np.arange(0.0, 20000.0 + 1e-9, r.fixed_step_s)
        cols = {"Timestamp": t}
        for c in val.expected_columns(logged[r.model])[1:]:
            lvl = 6.0 if c.startswith("PS") else 6.5
            cols[c] = lvl - 1e-5 * t / 2 + rng.normal(0, 1e-4, len(t))
        if bad and bad[0] == r.scenario_id and bad[1] == r.model:
            cols["PS1"] = cols["PS1"] + 6.0                                   # 12 MPa: outside the gas table
        pd.DataFrame(cols).to_csv(f"{base}_clean_solver_grid.csv", index=False)
        prov = {"scenario_id": r.scenario_id, "independence_group": r.independence_group, "partition": r.partition,
                "model": r.model, "model_name": r.model_name, "released_model_sha256": rel[r.model],
                "ps_step_final_value_MPa": r.ps_step_final_value_MPa, "ps_ramp_slope_MPa_per_s": r.ps_ramp_slope_MPa_per_s,
                "withdrawal_restriction_area_m2": [r.withdrawal_restriction_area_m2] * 4, "solver": "ode14x",
                "fixed_step_s": r.fixed_step_s, "logged_variables": logged[r.model], "noise_seed": int(r.noise_seed),
                "clean_solver_grid_csv_sha256": _sha(f"{base}_clean_solver_grid.csv"), "package_version": "v2",
                "authorization_scope": "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"}
        Path(f"{base}_provenance.json").write_text(json.dumps(prov), encoding="utf-8")


def test_end_to_end_dry_run_accepts_and_seals(tmp_path, active):
    _fabricate(tmp_path)
    assert post.main([str(tmp_path)]) == 0
    assert val.main([str(tmp_path)]) == 0
    seal = (tmp_path / "CONFIRMATION_PARTITION.sha256").read_text().splitlines()
    assert sum(not s.startswith("#") for s in seal) == 9 * 4 and seal[-1].startswith("# aggregate ")
    assert len(pd.read_csv(tmp_path / "DEVELOPMENT_MANIFEST.csv")) == 18
    rep = json.loads((tmp_path / "VALIDATION_REPORT.json").read_text())
    conf = [r for r in rep["runs"] if r["partition"] == "confirmation"]
    assert len(conf) == 9 and all(not any(k.startswith("value_") for k in r) for r in conf)   # PASS/FAIL only
    assert all(isinstance(v, bool) for r in conf for k, v in r.items() if k.startswith("P"))
    c = pd.read_csv(next((tmp_path / "development").glob("*_clean.csv")))
    assert len(c) == 20000 and np.array_equal(c.Timestamp.to_numpy(), np.arange(20000.0))


def test_tampered_parameter_is_rejected_and_nothing_is_sealed(tmp_path, active):
    _fabricate(tmp_path)
    post.main([str(tmp_path)])
    p = next((tmp_path / "development").glob("*_provenance.json"))
    pv = json.loads(p.read_text()); pv["ps_step_final_value_MPa"] = 9.9; p.write_text(json.dumps(pv))
    assert val.main([str(tmp_path)]) == 1
    assert not (tmp_path / "CONFIRMATION_PARTITION.sha256").exists()


def test_physical_failure_on_a_confirmation_run_is_reported_without_values(tmp_path, active):
    r = PTS[PTS.partition == "confirmation"].iloc[0]
    _fabricate(tmp_path, bad=(r.scenario_id, "up"))
    post.main([str(tmp_path)])
    assert val.main([str(tmp_path)]) == 1
    rep = json.loads((tmp_path / "VALIDATION_REPORT.json").read_text())
    hit = [x for x in rep["runs"] if x["run"] == f"{r.scenario_id}_up"][0]
    assert hit["P2_pressure"] is False and not any(k.startswith("value_") for k in hit)
    assert not (tmp_path / "CONFIRMATION_PARTITION.sha256").exists()


def test_failed_run_record_blocks_postprocessing_and_sealing(tmp_path, active):
    _fabricate(tmp_path)
    (tmp_path / "development" / "X_FAILED.json").write_text("{}")
    with pytest.raises(SystemExit):
        post.main([str(tmp_path)])
    assert val.main([str(tmp_path)]) == 1


# ------------------------------------------------------------------------------------------------ components
def test_resampling_is_linear_and_requires_full_coverage():
    t = np.arange(0.0, 20000.0 + 1e-9, 0.9)
    raw = pd.DataFrame({"Timestamp": t, "PS1": 2.0 * t})
    out = post.resample(raw)
    assert np.allclose(out.PS1, 2.0 * np.arange(20000.0)) and len(out) == 20000
    with pytest.raises(ValueError):
        post.resample(raw[raw.Timestamp < 15000])


def test_noise_is_seeded_white_and_matches_released_sigma():
    clean = pd.DataFrame({"Timestamp": np.arange(20000.0), "PS1": np.full(20000, 6.0), "MFS1": np.full(20000, 30.0)})
    a, b = post.add_noise(clean, 123), post.add_noise(clean, 123)
    assert a.equals(b) and not a.equals(post.add_noise(clean, 124))
    e = (a.PS1 - clean.PS1).to_numpy()
    assert e.std() == pytest.approx(0.0005, rel=0.05) and (a.MFS1 - clean.MFS1).std() == pytest.approx(0.25, rel=0.05)
    assert abs(np.corrcoef(e[:-1], e[1:])[0, 1]) < 0.03


def test_released_normal_runs_pass_the_fixed_physical_checks():
    """The thresholds were fixed from the released clean NORMAL runs; those runs must pass them."""
    man = pd.read_csv(REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv")
    n = man[(man.label_mapped == "NORMAL") & man.eligible_primary.astype(bool)]
    raw = REPO / "data" / "raw"
    if not all((raw / f).exists() for f in n.file_clean):
        pytest.skip("released raw data not available")
    lg = val.expected_logged()
    mp = {"Center": "center", "Downstream": "down", "Upstream": "up"}
    for r in n.itertuples():
        c = pd.read_parquet(raw / r.file_clean).reset_index()
        chk, _ = val.physical_checks(c[val.expected_columns(lg[mp[r.topology_source_model]])])
        assert all(chk.values()), (r.topology_source_model, chk)
