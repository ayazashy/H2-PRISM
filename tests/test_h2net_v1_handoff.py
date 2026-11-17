"""H2Net v1 Windows handoff: gates, decided spec, evaluator, scenario plan, return package, entrypoints (static/synthetic).
None of these tests runs MATLAB or validates Simulink dynamics. Fixture decision records only; the real record is untouched."""

import copy
import csv
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools" / "simulation"
sys.path.insert(0, str(TOOLS))
import h2net_v1_build_spec_decided as bsd  # noqa: E402
import h2net_v1_gates as gates  # noqa: E402
import h2net_v1_package_return as pkg  # noqa: E402
import h2net_v1_scenarios as scen  # noqa: E402
import h2net_v1_v2_targets as v2t  # noqa: E402
import h2net_v1_validation as val  # noqa: E402

FIX = "TEST-FIXTURE (not an approval)"


def fixture_decisions():
    t = yaml.safe_load(gates.TEMPLATE)                                # valid YAML; placeholders are "<...>" strings
    t["status"] = "DECIDED_WITH_DEFERRALS"
    for k, v in t.items():
        if isinstance(v, dict) and "decided_by" in v:
            v["decided"], v["decided_by"] = True, FIX
    t["S6_roughness_and_initial_state"]["source"] = FIX
    t["operating_envelope_V8"]["source"] = FIX
    t["S5_discretisation"]["reason"] = "fixture"
    nm = t["methods_review"]["value"]["noise_model"]
    nm.update(pressure={"sigma_kPa": 1.0, "source": FIX}, mass_flow={"sigma_kg_s": 0.01, "source": FIX},
              temperature={"sigma_K": 0.1, "source": FIX})
    t["methods_review"]["value"]["leak_labels"] = "A"
    s3 = t["S3_compressor_stations"]["value"]
    s3["aftercoolers"].update(outlet_tolerance_K=0.5, cooler_pipe_length_m=200)
    s3["down_model_letdown_sid_111"] = "isenthalpic reduction to 4.0 MPa"
    t["S4_demand_and_leaks"]["value"]["leaks"]["severity_definition"] = "A"
    t["S7_sensors_and_units"]["value"]["released_MFS2"] = "keep as MFS2_chamber"
    t["scenarios"]["value"].update(run_duration_s=7200, sample_period_s=1.0, onset_window_s=[1800, 5400], master_seed=12345,
                                   families_per_topology={"development": 4, "confirmation": 2})
    t["methods_review"]["decided_by"] = "Faisal " + FIX
    t["methods_review"]["value"]["v4_tolerance_fraction"] = 0.05
    return t


@pytest.fixture(scope="module")
def fx(tmp_path_factory):
    d = tmp_path_factory.mktemp("h2run")
    dec = fixture_decisions()
    dp = d / "PARAMETER_DECISIONS.yaml"
    dp.write_text(yaml.safe_dump(dec, sort_keys=False), encoding="utf-8")
    run = d / "run"
    (run / "targets").mkdir(parents=True)
    tg = v2t.compute(dp, run / "targets" / "V2_TARGETS.json")
    return {"dec": dec, "dp": dp, "run": run, "targets": tg}


def test_template_and_real_record_keep_every_gate_closed():
    for st in gates.STAGES:
        assert gates.check(st), st                                   # real record: OWNER_DECISIONS_REQUIRED
    raw = yaml.safe_load(gates.TEMPLATE)
    with pytest.raises(v2t.Refused):
        v2t.gate(raw)                                                # unfilled template refused
    assert subprocess.run(["git", "diff", "--quiet", "ff11c87", "--", str(gates.DECISIONS)], cwd=ROOT).returncode == 0


def test_build_gate_names_missing_executor_and_targets(fx):
    p = gates.check("build", decisions=fx["dp"], run=fx["run"].parent / "elsewhere")
    assert any("EXECUTOR_DESIGNATION" in x for x in p) and any("V2 targets" in x or "V2_TARGETS" in x for x in p)


@pytest.mark.slow
def test_decided_spec_contains_every_structural_operation(fx):
    spec = bsd.build(fx["dec"], fx["targets"], "sha")
    assert spec["status"] == "SPECIFICATION_DECIDED"
    for name, m in spec["models"].items():
        ops = [o["op"] for o in m["operations"]]
        ids = {o["id"] for o in m["operations"]}
        assert ops.count("replace_two_port") == 4 and ops.count("split_pipe_with_leak") == 6
        assert {"cooler_C1", "cooler_C2", "comp_C1", "comp_C2", "MFS0", "MFS2s", "MFS5", "MFS6", "sink_END", "T_C1_out", "T_C2_out"} <= ids
        assert ({"MFS7", "PS_END"} <= ids) == (m["position"] != "down") and ("PS_N6" in ids) == (m["position"] != "up")
        assert set(m["expected_log_variables"]) <= set(m["sensor_map"]) | {f"temperature_sensor_{k}_out" for k in ("C1", "C2")}
        assert all(o["v4_area_m2_for_2pct"] > 0 for o in m["operations"] if o["op"] == "split_pipe_with_leak")
    m = (ROOT / "tools/matlab/h2prism_apply_structural_ops.m").read_text(encoding="utf-8")
    for op in {o["op"] for mm in spec["models"].values() for o in mm["operations"]}:
        assert f"'{op}'" in m, f"MATLAB handler missing for {op}"


@pytest.mark.slow
def test_evaluator_passes_exact_targets_and_refuses_missing_thresholds(fx, tmp_path):
    run = tmp_path / "run"
    (run / "targets").mkdir(parents=True)
    (run / "targets" / "V2_TARGETS.json").write_text(json.dumps(fx["targets"]), encoding="utf-8")
    spec = bsd.build(fx["dec"], fx["targets"], "sha")
    (run / "build").mkdir()
    (run / "build" / "H2NET_V1_BUILD_SPEC_DECIDED.json").write_text(json.dumps(spec), encoding="utf-8")
    raw = {"models": {}}
    build = {"status": "COMPLETE", "models": []}
    for name, m in spec["models"].items():
        pts = fx["targets"]["targets"][name]
        v2 = []
        for pt in pts:
            vals = {}
            for var, kind in m["sensor_map"].items():
                e, _ = val._expected(kind, pt)
                if e is not None:
                    vals[var] = {"last": e, "drift": 0.0}
            vals["temperature_sensor_C1_out"] = vals["temperature_sensor_C2_out"] = {"last": 313.2, "drift": 0.0}
            v2.append({"demand_multiplier": pt["demand_multiplier"], "values": vals})
        nominal = min(v2, key=lambda r: abs(r["demand_multiplier"] - 1))
        v4 = [{"leak": o["id"], "values": {"flow_sensor_MFS0": {"last": nominal["values"]["flow_sensor_MFS0"]["last"] + o["v4_expected_leak_kg_s_nozzle"], "drift": 0}}}
              for o in m["operations"] if o["op"] == "split_pipe_with_leak"]
        raw["models"][name] = {"V2": v2, "V4": v4, "V6": {"ref": nominal["values"], "tight": nominal["values"]}}
        build["models"].append({"model": name, "diff": [{"id": o["id"]} for o in m["operations"]], "released_hash_ok": True, "copy_sha256": "x"})
    (run / "validation").mkdir()
    (run / "validation" / "VALIDATION_RAW.json").write_text(json.dumps(raw), encoding="utf-8")
    (run / "build" / "BUILD_REPORT.json").write_text(json.dumps(build), encoding="utf-8")
    rep = val.evaluate(run, fx["dp"])
    assert all(rep["gates"][k] == "PASS" for k in ("V2", "V3", "V4", "V6", "V8", "D1"))
    assert rep["gates"]["V5"] == "NOT_EVALUABLE" and rep["overall"] == "NOT_PASSED"      # S5 deferred in the fixture
    name = next(iter(raw["models"]))
    raw["models"][name]["V2"][0]["values"]["pressure_sensor1"]["last"] += 0.5            # 0.5 MPa error
    (run / "validation" / "VALIDATION_RAW.json").write_text(json.dumps(raw), encoding="utf-8")
    assert val.evaluate(run, fx["dp"])["gates"]["V2"] == "FAIL"


@pytest.mark.slow
def test_scenario_plan_is_matched_opaque_and_partition_safe(fx):
    p = scen.plan(fx["dec"], fx["targets"])
    assert scen.check(p) == []
    classes = {l["class"] for l in p["labels"]}
    assert classes == {"NORMAL", "LEAK", "COMPRESSOR_FAULT", "DELAY"}
    for l in p["labels"]:
        if l["class"] == "DELAY":
            assert l["load_profile"] in ("step", "ramp")
    assert all(re.fullmatch(r"[0-9a-f]{20}", r["run_id"]) for r in p["runs"])
    parts = {}
    for r in p["runs"]:
        parts.setdefault(r["family"], set()).add(r["partition"])
    assert all(len(v) == 1 for v in parts.values())
    bad = copy.deepcopy(p)
    bad["runs"][0]["partition"] = "confirmation" if bad["runs"][0]["partition"] == "development" else "development"
    assert any("spans partitions" in x for x in scen.check(bad))
    leak = next(r for r in p["runs"] if any(isinstance(v[-1][1], float) and v[-1][1] > 0 for k, v in r["signals"].items() if k.startswith("h2_leak_area")))
    assert leak


def test_return_package_reports_missing_stages_and_excludes_secrets(tmp_path):
    run = tmp_path / "run"
    (run / "logs").mkdir(parents=True)
    (run / "logs" / "build.log").write_text("log", encoding="utf-8")
    (run / "logs" / "network.lic").write_text("SECRET", encoding="utf-8")
    out = pkg.package(run)
    z = zipfile.ZipFile(out)
    names = z.namelist()
    st = json.loads(z.read("RETURN_STATUS.json"))
    assert "run/logs/build.log" in names and not any(n.endswith(".lic") for n in names)
    assert st["overall"] == "INCOMPLETE" and "build" in st["missing_or_failed_stages"]
    assert "SHA256SUMS.txt" in names and out.with_suffix(".zip.sha256").exists()


def test_entrypoints_are_portable_gated_and_reference_existing_tools():
    hd = ROOT / "handoff" / "h2net_v1"
    for f in ("START_HERE.md", "01_PREFLIGHT.ps1", "02_VALIDATE_ENVIRONMENT.ps1", "03_BUILD_AND_VALIDATE.ps1",
              "04_RUN_AUTHORIZED_SCENARIOS.ps1", "05_PACKAGE_RETURN.ps1", "EXPECTED_OUTPUTS.md", "HANDOFF_MANIFEST.json"):
        assert (hd / f).exists(), f
    for ps in hd.glob("*.ps1"):
        s = ps.read_text(encoding="utf-8")
        assert "C:\\Users" not in s and "/Users/" not in s
        for ref in re.findall(r"tools[\\/][\w\\/]+\.py", s):
            assert (ROOT / ref.replace("\\", "/")).exists(), ref
        for fn in re.findall(r"(h2prism_\w+)\(", s):
            assert (ROOT / "tools" / "matlab" / f"{fn}.m").exists(), fn
    s4 = (hd / "04_RUN_AUTHORIZED_SCENARIOS.ps1").read_text(encoding="utf-8")
    assert s4.index("'check', 'dataset'") < s4.index("h2prism_run_scenarios")
    for m in ("h2prism_validate_h2net_v1.m", "h2prism_run_scenarios.m", "h2prism_build_h2net_v1.m"):
        code = (ROOT / "tools/matlab" / m).read_text(encoding="utf-8")
        assert "h2net_v1_gates.py" in code and "h2prism_memory_guard" in code
        assert "parsim" not in code and "parpool" not in code
    b = (ROOT / "tools/matlab/h2prism_build_h2net_v1.m").read_text(encoding="utf-8")
    assert re.findall(r"save_system\(([^,)]*)", b) == ["copyName"] and "load_system(rel" not in b
    assert subprocess.run([sys.executable, str(TOOLS / "h2net_v1_handoff_manifest.py"), "--check"]).returncode == 0
