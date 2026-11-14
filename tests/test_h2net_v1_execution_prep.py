"""H2Net v1 execution preparation: proposed record, provisional steady states, build spec, gated builder."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "06_audit_preparation" / "simulation" / "h2net_v1" / "candidate"
TOOLS = ROOT / "tools" / "simulation"
sys.path.insert(0, str(TOOLS))


def test_proposed_record_is_not_a_decision_and_the_real_record_is_untouched():
    P = yaml.safe_load((CAND / "PARAMETER_DECISIONS_PROPOSED.yaml").read_text(encoding="utf-8"))
    assert P["status"] == "PROPOSED_NOT_APPROVED" and P["approved_by"] is None
    assert all(not v["decided"] for k, v in P.items() if isinstance(v, dict) and "decided" in v)
    real = yaml.safe_load((CAND.parent / "PARAMETER_DECISIONS.yaml").read_text(encoding="utf-8"))
    assert real["status"] == "OWNER_DECISIONS_REQUIRED" and real["decided_by"] is None
    r = subprocess.run(["git", "diff", "--quiet", "ff11c87", "--", str(CAND.parent / "PARAMETER_DECISIONS.yaml")], cwd=ROOT)
    assert r.returncode == 0


@pytest.mark.slow
def test_provisional_steady_states_are_current_conservative_and_feasible():
    assert subprocess.run([sys.executable, str(TOOLS / "h2net_v1_provisional_network.py"), "--check"]).returncode == 0
    d = json.loads((CAND / "PROVISIONAL_STEADY_STATES.json").read_text(encoding="utf-8"))
    assert d["status"].startswith("PROVISIONAL")
    for name, r in d["base"].items():
        c = r["checks"]
        assert c["feasible"] and c["mass_conservation_max_residual_kg_s"] < 1e-9
        assert abs(c["supply_flow_kg_s"] - c["total_demand_kg_s"]) < 1e-12
        assert set(c["sinks_found"]) == {"G3", "G4", "G5", "G6", "END"}
        assert d["numerical_tolerance"][name]["max_node_pressure_change_Pa_200_vs_800_steps"] < 1.0
        for k in r["compressors"]:
            assert k["T_discharge_isentropic_K"] > k["T_suction_K"] and k["power_isentropic_kW"] >= 0
    down = d["base"]["Normal_HNetwork_gest_down"]["letdown"]
    assert down and down["T_out_isenthalpic_K"] > down["T_in_K"]          # inverse Joule-Thomson for H2 near ambient


def test_build_spec_is_current_and_consistent_with_the_released_models():
    assert subprocess.run([sys.executable, str(TOOLS / "h2net_v1_build_spec.py"), "--check"]).returncode == 0
    S = json.loads((CAND / "H2NET_V1_BUILD_SPEC.json").read_text(encoding="utf-8"))
    assert S["status"].startswith("SPECIFICATION_PROPOSED")
    g = json.loads((CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    for name, m in S["models"].items():
        sids = {c["sid"] for c in g[name]["components"]} | {"4"}
        assert all(op["sid"] in sids for op in m["parameter_ops"])
        kinds = [op["op"] for op in m["structural_ops"]]
        assert kinds.count("replace_demand_orifice") == 4 and kinds.count("replace_end_vent") == 1
        assert kinds.count("insert_aftercooler") == 2 and kinds.count("insert_leak_branch") == 6
        assert all(s["nets"] for s in m["sensor_map"])


def test_builder_is_gated_and_only_writes_copies():
    raw = (ROOT / "tools/matlab/h2prism_build_h2net_v1.m").read_text(encoding="utf-8")
    code = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("%"))      # drop comment lines only
    # gate delegated to tools/simulation/h2net_v1_gates.py ('check validate': decisions, executor, grant hashes, V2 targets,
    # MATLAB readiness); the spec must be SPECIFICATION_DECIDED; memory-guarded; released hash verified before and after
    for gate in ("h2net_v1_gates.py", "check validate", "SPECIFICATION_DECIDED", "h2prism_memory_guard", "released_hash_ok", "source_sha256"):
        assert gate in code
    assert not re.search(r"\bsim\s*\(|parsim|batchsim", code)
    assert re.findall(r"save_system\(([^,)]*)", code) == ["copyName"]
    assert "load_system(rel" not in code and "copyfile(rel, copyFile)" in code


@pytest.mark.slow
def test_design_freeze_calcs_are_current_and_support_the_spec():
    assert subprocess.run([sys.executable, str(TOOLS / "h2net_v1_design_freeze_calcs.py"), "--check"]).returncode == 0
    d = json.loads((CAND / "DESIGN_FREEZE_CALCS.json").read_text(encoding="utf-8"))
    for m in d["models"].values():
        a = m["A_nominal"]
        assert a["feasible_normal_envelope"] and a["mass_residual_kg_s"] < 1e-9
        assert a["C2"]["dp_MPa"] > 1.0 and a["C1"]["T_discharge_isentropic_K"] < 400
        assert all(f["within_fault_envelope_2p5MPa"] for f in m["C_faults"].values())
        s = m["D_signatures"]
        assert s["normal_load_x0.5_to_x1.5_max_abs_node_dp_kPa"] > 5 * s["leak_0.100_at_G4"]["max_abs_node_dp_kPa"]
        assert m["E_line_pack"]["control_volumes"]["CV_A"]["dM_dp_kg_per_kPa"] > 40


def test_v2_targets_refuse_today_and_run_only_from_a_complete_decision_record(tmp_path):
    import h2net_v1_v2_targets as v2t
    out = tmp_path / "t.json"
    assert v2t.main(["--out", str(out)]) == 2 and not out.exists()          # real record: OWNER_DECISIONS_REQUIRED
    dec = {"status": "DECIDED_WITH_DEFERRALS",
           "S2_thermal_boundary": {"decided": False, "deferred": True},
           "S3_compressor_stations": {"decided": True, "decided_by": "TEST-FIXTURE", "value": {
               "supply_reservoir_pressure_MPa": 3.2, "C1_pressure_source_sid_55": {"discharge_setpoint_MPa": 5.0},
               "C2_pressure_source_sid_239": {"discharge_setpoint_MPa": 6.5}, "down_model_letdown_sid_111": "DEFERRED"}},
           "S4_demand_and_leaks": {"decided": True, "decided_by": "TEST-FIXTURE", "value": {
               "nominal_demand_kg_s": {"G3": 4.0, "G5": 4.0, "G4": 5.0, "G6": 5.0, "END": 2.0}, "demand_levels": [0.6, 0.8, 1.0, 1.2, 1.4]}},
           "S6_roughness_and_initial_state": {"decided": True, "decided_by": "TEST-FIXTURE", "value": {"roughness_m": 4.5e-5}},
           "operating_envelope_V8": {"decided": True, "decided_by": "TEST-FIXTURE", "value": {
               "isothermal_reference_temperature_K": 313.15, "normal": {"pressure_MPa": [3.0, 8.0], "velocity_limit_m_s": 20.0}}}}
    bad = dict(dec, S5_discretisation={"decided": False})                    # undecided and not deferred -> refused
    pb = tmp_path / "bad.yaml"; pb.write_text(yaml.safe_dump(bad))
    assert v2t.main(["--decisions", str(pb), "--out", str(out)]) == 2 and not out.exists()
    pg = tmp_path / "ok.yaml"; pg.write_text(yaml.safe_dump(dec))
    assert v2t.main(["--decisions", str(pg), "--out", str(out)]) == 0
    r = json.loads(out.read_text(encoding="utf-8"))
    assert r["targets"]["Normal_HNetwork_gest_down"].startswith("NOT_COMPUTED")
    assert all(len(r["targets"][m]) == 5 and all(p["checks"]["feasible"] for p in r["targets"][m])
               for m in ("Normal_HNetwork_gest_center", "Normal_HNetwork_gest_up"))
