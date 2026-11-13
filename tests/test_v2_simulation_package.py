"""SIMULATION_GENERATION:V2_NORMAL_SUPPORT package v3: design invariants, the project lead's attempt policy implemented in
the real gate (preflight non-consuming; atomic one-attempt claim at 'run'; consumption on success, failure and
interruption; concurrent starts; unauthorized retry), and an end-to-end dry run on FABRICATED MATLAB-shaped outputs in a
temporary folder. No simulation is run; no data are produced in the repository."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import time
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
REQ3 = yaml.safe_load((PKG / "AUTH_SIMULATION_GENERATION_V3_REQUEST.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def granted(tmp_path, monkeypatch):
    """A GRANTED copy of the real v3 request (bound to the current files) in a temporary package folder."""
    rec = copy.deepcopy(REQ3)
    rec.update(authorized=True, authorized_by="unit-test fixture (not a real grant)", date="2026-11-13")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    rp = pkg / "AUTH_SIMULATION_GENERATION_V3_TEST.yaml"
    rp.write_text(yaml.safe_dump(rec), encoding="utf-8")
    monkeypatch.setattr(auth, "PKG", pkg)
    return rp


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
    assert D.groupby("scenario_id").independence_group.nunique().eq(1).all() and D.independence_group.nunique() == 9


# ------------------------------------------------------------------------------------------------ records
def test_repository_state_v1_v2_void_v3_pending_and_policy_recorded():
    for name in ("AUTH_SIMULATION_GENERATION.yaml", "AUTH_SIMULATION_GENERATION_V2_REQUEST.yaml"):
        assert auth.evaluate(yaml.safe_load((PKG / name).read_text(encoding="utf-8")))   # void, fail closed
    assert auth.evaluate(REQ3) == ["authorized is not true"]                              # bound, not granted
    assert auth.state() == "NOT_AUTHORIZED"
    v2 = yaml.safe_load((PKG / "AUTH_SIMULATION_GENERATION_V2_REQUEST.yaml").read_text(encoding="utf-8"))
    assert v2["authorized"] is True and v2["authorized_by"] == "Ahmed Zayed (project lead)"   # original preserved
    pol = yaml.safe_load((PKG / "POLICY_CLARIFICATION_2026-11-13.yaml").read_text(encoding="utf-8"))
    assert "'run'" in pol["decision"]["attempt_begins"] and "preflight" in " ".join(pol["decision"]["non_consuming"])
    hist = pd.read_csv(PKG / "AUTHORIZATION_HISTORY.csv")
    assert dict(zip(hist.package_version, hist.status)) == {"v1": "VOID_SUPERSEDED", "v2": "VOID_SUPERSEDED",
                                                            "policy": "RECORDED", "v3": "PENDING_PROJECT_LEAD_AUTHORIZATION"}
    assert not list(PKG.glob("claims/*.claim.json"))                                     # nothing has been claimed


def test_changed_bound_file_voids_even_a_granted_record(granted, monkeypatch):
    real = auth.current_hashes()
    monkeypatch.setattr(auth, "current_hashes", lambda: {**real, "validator": "0" * 64})
    with pytest.raises(auth.NotAuthorized):
        auth.require_active()
    with pytest.raises(auth.NotAuthorized):
        auth.claim("anywhere")
    assert not auth.claim_path(granted).exists()


# ------------------------------------------------------------------------------------------------ attempt policy
def test_preflight_is_repeatable_and_non_consuming(granted):
    for _ in range(5):
        rec, rp = auth.require_active()             # what the MATLAB preflight's status check relies on
        assert rp == granted
    assert auth.state() == "ACTIVE_UNCLAIMED" and not auth.claim_path(granted).exists()
    assert auth.main(["status"]) == 0 and auth.main(["check"]) == 0


def test_first_run_claims_atomically_and_consumes(granted, tmp_path):
    c = auth.claim(tmp_path / "out")
    assert len(c["attempt_id"]) == 32 and c["bound_hashes"] == auth.current_hashes()
    assert auth.state() == "CLAIMED" and auth.main(["check"]) == 1
    with pytest.raises(auth.AlreadyClaimed):
        auth.claim(tmp_path / "out")                 # same folder: still refused
    assert auth.require_claimed(tmp_path / "out")["attempt_id"] == c["attempt_id"]
    auth.require_active()                            # preflight after consumption: allowed, harmless


def test_failed_run_stays_consumed(granted, tmp_path):
    out = tmp_path / "out"
    auth.claim(out)
    (out / "development").mkdir(parents=True)
    (out / "development" / "V2N_X_center_FAILED.json").write_text("{}")
    with pytest.raises(auth.AlreadyClaimed):
        auth.claim(tmp_path / "retry")
    with pytest.raises(SystemExit):
        post.main([str(out)])                        # failed attempt cannot be post-processed
    assert val.main([str(out)]) == 1                 # nor accepted


def test_unauthorized_retry_into_another_folder_is_refused(granted, tmp_path):
    auth.claim(tmp_path / "out")
    with pytest.raises(auth.AlreadyClaimed):
        auth.claim(tmp_path / "other")
    with pytest.raises(auth.NotAuthorized):
        auth.require_claimed(tmp_path / "other")
    with pytest.raises(auth.NotAuthorized):
        post.main([str(tmp_path / "other")])
    with pytest.raises(auth.NotAuthorized):
        val.main([str(tmp_path / "other")])


def test_claim_requires_a_granted_record(tmp_path, monkeypatch):
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "AUTH_SIMULATION_GENERATION_V3_TEST.yaml").write_text(yaml.safe_dump(REQ3), encoding="utf-8")  # not granted
    monkeypatch.setattr(auth, "PKG", pkg)
    with pytest.raises(auth.NotAuthorized) as e:
        auth.claim(tmp_path / "out")
    assert not isinstance(e.value, auth.AlreadyClaimed) and not list(pkg.rglob("*.claim.json"))


def test_corrupt_claim_still_counts_as_consumed(granted, tmp_path):
    p = auth.claim_path(granted)
    p.parent.mkdir(parents=True)
    p.write_bytes(b"\x00 truncated")
    with pytest.raises(auth.AlreadyClaimed):
        auth.claim(tmp_path / "out")
    with pytest.raises(auth.NotAuthorized):
        auth.require_claimed(tmp_path / "out")


_CHILD = r"""
import sys, time, os
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import v2_normal_authorization as a
rec, out, go, mode = Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), sys.argv[5]
while not go.exists():
    time.sleep(0.001)
try:
    a.claim(out, record_path=rec)
except a.AlreadyClaimed:
    sys.exit(3)
if mode == "interrupt":
    os._exit(9)            # killed right after claiming: no cleanup, no simulation
sys.exit(0)
"""


def _spawn(n, record, out, go, mode="normal"):
    return [subprocess.Popen([sys.executable, "-c", _CHILD, str(TOOLS), str(record), str(out), str(go), mode])
            for _ in range(n)]


def test_concurrent_starts_exactly_one_claim(granted, tmp_path):
    go = tmp_path / "go"
    procs = _spawn(8, granted, tmp_path / "out", go)
    time.sleep(1.0)
    go.write_text("go")
    codes = sorted(p.wait(timeout=120) for p in procs)
    assert codes.count(0) == 1 and codes.count(3) == 7
    assert len(list(auth.claim_path(granted).parent.glob("*.claim.json"))) == 1


def test_interrupted_run_stays_consumed(granted, tmp_path):
    go = tmp_path / "go"
    go.write_text("go")
    (p,) = _spawn(1, granted, tmp_path / "out", go, mode="interrupt")
    assert p.wait(timeout=120) == 9
    assert auth.state() == "CLAIMED"
    with pytest.raises(auth.AlreadyClaimed):
        auth.claim(tmp_path / "out")


# ------------------------------------------------------------------------------------------------ generator text
def test_generator_claims_before_simulation_and_preflight_never_simulates():
    m = (PKG / "generate_v2_normal_support.m").read_text(encoding="utf-8")
    i_claim, i_mk = m.index("claim --out-dir"), m.index("mkdir(outDir)")
    i_sim, i_pre = m.index("simOut = sim(mdl)"), m.index("if strcmp(mode, 'preflight')\n                pre(end+1)")
    assert i_claim < i_mk < i_sim                     # claim before any output folder or simulation
    assert i_pre < i_sim and "continue" in m[i_pre:i_sim]   # preflight leaves the loop before sim()
    pre_gate = m[m.index("if strcmp(mode, 'preflight')\n        [st, txt]"):m.index("else\n        % atomic")]
    assert "status" in pre_gate and "claim" not in pre_gate    # preflight never claims
    assert "save_system" not in m and "close_system(mdl, 0)" in m and "released model changed" in m
    assert "isMATLABReleaseOlderThan('R2025a')" in m and "'package_version', 'v3', 'attempt_id', attemptId" in m
    edges = pd.read_csv(REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "NETWORK_EDGES.csv")
    for model, g in edges[edges.scenario_kind == "normal"].groupby("model"):
        for sid in ("213", "222", "312", "215"):
            assert f"SID {sid};" in " ".join(g.component), (model, sid)


# ------------------------------------------------------------------------------------------------ dry run
def _fabricate(out: Path, attempt_id: str, bad=None):
    logged, rel = val.expected_logged(), val.released_hashes()
    rng = np.random.default_rng(0)
    for r in D.itertuples():
        d = out / r.partition
        d.mkdir(parents=True, exist_ok=True)
        base = d / f"{r.scenario_id}_{r.model}"
        t = np.arange(0.0, 20000.0 + 1e-9, r.fixed_step_s)
        cols = {"Timestamp": t}
        for c in val.expected_columns(logged[r.model])[1:]:
            cols[c] = (6.0 if c.startswith("PS") else 6.5) - 1e-5 * t / 2 + rng.normal(0, 1e-4, len(t))
        if bad and bad[0] == r.scenario_id and bad[1] == r.model:
            cols["PS1"] = cols["PS1"] + 6.0
        pd.DataFrame(cols).to_csv(f"{base}_clean_solver_grid.csv", index=False)
        prov = {"scenario_id": r.scenario_id, "independence_group": r.independence_group, "partition": r.partition,
                "model": r.model, "model_name": r.model_name, "released_model_sha256": rel[r.model],
                "ps_step_final_value_MPa": r.ps_step_final_value_MPa, "ps_ramp_slope_MPa_per_s": r.ps_ramp_slope_MPa_per_s,
                "withdrawal_restriction_area_m2": [r.withdrawal_restriction_area_m2] * 4, "solver": "ode14x",
                "fixed_step_s": r.fixed_step_s, "logged_variables": logged[r.model], "noise_seed": int(r.noise_seed),
                "clean_solver_grid_csv_sha256": _sha(f"{base}_clean_solver_grid.csv"), "package_version": "v3",
                "attempt_id": attempt_id,
                "authorization_scope": "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"}
        Path(f"{base}_provenance.json").write_text(json.dumps(prov), encoding="utf-8")


def test_end_to_end_dry_run_accepts_and_seals(granted, tmp_path):
    out = tmp_path / "out"
    c = auth.claim(out)                               # what the MATLAB 'run' does first
    _fabricate(out, c["attempt_id"])
    assert post.main([str(out)]) == 0
    assert val.main([str(out)]) == 0
    seal = (out / "CONFIRMATION_PARTITION.sha256").read_text().splitlines()
    assert sum(not s.startswith("#") for s in seal) == 36 and seal[-1].startswith("# aggregate ")
    rep = json.loads((out / "VALIDATION_REPORT.json").read_text())
    assert rep["attempt_id"] == c["attempt_id"] and len(pd.read_csv(out / "DEVELOPMENT_MANIFEST.csv")) == 18
    conf = [r for r in rep["runs"] if r["partition"] == "confirmation"]
    assert len(conf) == 9 and all(not any(k.startswith("value_") for k in r) for r in conf)


def test_outputs_from_another_attempt_are_rejected(granted, tmp_path):
    out = tmp_path / "out"
    auth.claim(out)
    _fabricate(out, "f" * 32)                         # provenance not from the claimed attempt
    post.main([str(out)])
    assert val.main([str(out)]) == 1
    assert not (out / "CONFIRMATION_PARTITION.sha256").exists()


def test_physical_failure_on_a_confirmation_run_is_reported_without_values(granted, tmp_path):
    out = tmp_path / "out"
    c = auth.claim(out)
    r = PTS[PTS.partition == "confirmation"].iloc[0]
    _fabricate(out, c["attempt_id"], bad=(r.scenario_id, "up"))
    post.main([str(out)])
    assert val.main([str(out)]) == 1
    hit = [x for x in json.loads((out / "VALIDATION_REPORT.json").read_text())["runs"] if x["run"] == f"{r.scenario_id}_up"][0]
    assert hit["P2_pressure"] is False and not any(k.startswith("value_") for k in hit)


# ------------------------------------------------------------------------------------------------ components
def test_resampling_is_linear_and_requires_full_coverage():
    t = np.arange(0.0, 20000.0 + 1e-9, 0.9)
    raw = pd.DataFrame({"Timestamp": t, "PS1": 2.0 * t})
    assert np.allclose(post.resample(raw).PS1, 2.0 * np.arange(20000.0))
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
