"""SIMULATION_GENERATION:V2_NORMAL_SUPPORT package: design invariants, authorization binding, and an end-to-end dry run of
noise + validation + sealing on FABRICATED MATLAB-shaped outputs (temporary folder; no real simulation, no data)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

import importlib.util

REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support"
TOOLS = REPO / "tools" / "simulation"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


noise = _load("add_measurement_noise")
val = _load("validate_v2_normal_outputs")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


D = pd.read_csv(PKG / "DESIGN.csv")
PTS = D.drop_duplicates("scenario_id")


def test_design_is_balanced_excludes_released_point_and_partitions_in_advance():
    assert len(D) == 27 and set(D.model) == {"center", "down", "up"} and len(PTS) == 9
    assert not ((PTS.ps_step_final_value_MPa == 6.4) & (PTS.ps_ramp_slope_MPa_per_s == -1e-5)
                & (PTS.withdrawal_restriction_area_m2 == 1e-3)).any()
    for f in ("ps_step_final_value_MPa", "ps_ramp_slope_MPa_per_s", "withdrawal_restriction_area_m2"):
        assert set(PTS[f].value_counts()) == {3}
        assert set(PTS[PTS.partition == "confirmation"][f].value_counts()) == {1}
        assert set(PTS[PTS.partition == "development"][f].value_counts()) == {2}
    assert (PTS.partition == "development").sum() >= 4 and (PTS.partition == "confirmation").sum() >= 3
    assert D.noise_seed.is_unique
    assert (PKG / "DESIGN.sha256").read_text().split()[0] == _sha(PKG / "DESIGN.csv")
    existing = set(pd.read_csv(REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv").independence_group)
    assert not set(D.independence_group) & existing


def test_authorization_is_bound_to_current_files_and_scoped():
    a = yaml.safe_load((PKG / "AUTH_SIMULATION_GENERATION.yaml").read_text(encoding="utf-8"))
    assert a["scope"] == "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION" and a["authorized"] is True
    for v in a["bound_to"].values():
        assert _sha(REPO / v["file"]) == v["sha256"], v["file"]
    assert "training" in a["not_covered"] and "confirmation partition" in a["not_covered"]
    assert "NOT_RECORDED" in a["executor"]


def test_generator_never_saves_models_and_targets_existing_block_ids():
    m = (PKG / "generate_v2_normal_support.m").read_text(encoding="utf-8")
    assert "save_system" not in m and "close_system(mdl, 0)" in m and "copyfile" in m
    for sid in ("59", "241", "213", "222", "312", "215"):
        assert f"'{sid}'" in m or f'"{sid}"' in m
    trace = pd.read_csv(REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "NETWORK_EDGES.csv")
    normal = trace[trace.scenario_kind == "normal"]
    for model, g in normal.groupby("model"):
        comps = " ".join(g.component)
        for sid in ("213", "222", "312", "215"):
            assert f"SID {sid};" in comps, (model, sid)


def _fabricate(out: Path):
    """MATLAB-shaped outputs for every design row: clean CSV with the model's own sensor list + provenance JSON."""
    logged, rel = val.expected_logged(), val.released_hashes()
    rng = np.random.default_rng(0)
    for r in D.itertuples():
        d = out / r.partition
        d.mkdir(parents=True, exist_ok=True)
        base = d / f"{r.scenario_id}_{r.model}"
        cols = {"Timestamp": np.arange(300.0)}
        for v in sorted(logged[r.model], key=lambda s: (not s.startswith("pressure"), int(s.rsplit("sensor", 1)[1]))):
            cols[("PS" if v.startswith("pressure") else "MFS") + v.rsplit("sensor", 1)[1]] = 5 + rng.normal(0, 0.01, 300)
        pd.DataFrame(cols).to_csv(f"{base}_clean.csv", index=False)
        prov = {"scenario_id": r.scenario_id, "independence_group": r.independence_group, "partition": r.partition,
                "model": r.model, "model_name": r.model_name, "released_model_sha256": rel[r.model],
                "ps_step_final_value_MPa": r.ps_step_final_value_MPa, "ps_ramp_slope_MPa_per_s": r.ps_ramp_slope_MPa_per_s,
                "withdrawal_restriction_area_m2": [r.withdrawal_restriction_area_m2] * 4, "solver": "ode14x",
                "fixed_step_s": r.fixed_step_s, "logged_variables": logged[r.model], "noise_seed": int(r.noise_seed),
                "clean_csv_sha256": _sha(f"{base}_clean.csv"),
                "authorization_scope": "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"}
        Path(f"{base}_provenance.json").write_text(json.dumps(prov), encoding="utf-8")


def test_end_to_end_dry_run_seals_confirmation_without_reading_it(tmp_path):
    _fabricate(tmp_path)
    assert noise.main([str(tmp_path)]) == 0
    # replace one confirmation signal file by unparseable bytes and record its hash: the validator must not parse it
    c = next((tmp_path / "confirmation").glob("*_noise_added.csv"))
    c.write_bytes(b"\x00\xffnot a csv")
    pv_p = Path(str(c).replace("_noise_added.csv", "_provenance.json"))
    pv = json.loads(pv_p.read_text()); pv["noise_added_csv_sha256"] = _sha(c); pv_p.write_text(json.dumps(pv))
    assert val.main([str(tmp_path)]) == 0
    seal = (tmp_path / "CONFIRMATION_PARTITION.sha256").read_text().splitlines()
    assert sum(not s.startswith("#") for s in seal) == 3 * 3 * 3 and seal[-1].startswith("# aggregate ")
    man = pd.read_csv(tmp_path / "DEVELOPMENT_MANIFEST.csv")
    assert len(man) == 18 and set(man.partition) == {"development"}


def test_validator_rejects_tampering_and_does_not_seal(tmp_path):
    _fabricate(tmp_path)
    noise.main([str(tmp_path)])
    p = next((tmp_path / "development").glob("*_provenance.json"))
    pv = json.loads(p.read_text()); pv["ps_step_final_value_MPa"] = 9.9; p.write_text(json.dumps(pv))
    assert val.main([str(tmp_path)]) == 1
    assert not (tmp_path / "CONFIRMATION_PARTITION.sha256").exists()


def test_noise_is_seeded_white_and_matches_released_sigma():
    clean = pd.DataFrame({"Timestamp": np.arange(20000.0), "PS1": np.full(20000, 6.0), "MFS1": np.full(20000, 30.0)})
    a, b = noise.add_noise(clean, 123), noise.add_noise(clean, 123)
    assert a.equals(b) and not a.equals(noise.add_noise(clean, 124))
    e = (a.PS1 - clean.PS1).to_numpy()
    assert e.std() == pytest.approx(0.0005, rel=0.05) and (a.MFS1 - clean.MFS1).std() == pytest.approx(0.25, rel=0.05)
    assert abs(np.corrcoef(e[:-1], e[1:])[0, 1]) < 0.03
