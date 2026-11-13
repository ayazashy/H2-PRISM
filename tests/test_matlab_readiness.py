"""MATLAB readiness tooling (no MATLAB needed): pinned expectations current, static safety of the .m scripts,
independent PASS/FAIL evaluation of reports."""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ML = ROOT / "tools" / "matlab"
sys.path.insert(0, str(ML))
import check_matlab_reports as cmr  # noqa: E402

READ_ONLY = ["h2prism_verify_environment.m", "h2prism_smoke_test_models.m", "h2prism_check_h2_integration.m",
             "h2prism_run_readiness.m", "h2prism_sha256file.m", "h2prism_memory_status.m", "h2prism_memory_guard.m",
             "h2prism_add_check.m", "h2prism_write_report.m", "h2prism_load_expectations.m"]
FORBIDDEN = [r"\bsave_system\b", r"\bsim\s*\(", r"\bparsim\b", r"\bbatchsim\b", r"\bparpool\b", r"\bsave\s*\(",
             r"\bSimulink\.BlockDiagram\.\w*save", r"'claim'", r"\bdelete\s*\("]


def _code(p):
    return "\n".join(l.split("%", 1)[0] for l in p.read_text(encoding="utf-8").splitlines())


def test_expectations_file_is_current_and_consistent():
    r = subprocess.run([sys.executable, str(ML / "build_matlab_expectations.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
    E = json.loads((ML / "h2prism_matlab_expectations.json").read_text(encoding="utf-8"))
    assert len(E["models"]) == 6 and {m["position"]: len(m["sensors"]) for m in E["models"]} == {"center": 13, "up": 13, "down": 16}
    assert {m["kind"] for m in E["models"] if m["parameter_interface"]} == {"normal"}
    assert E["h2net_v1_grant"]["status"] == "ACTIVE" and E["released_gas"]["block_sid"] == "4"


@pytest.mark.parametrize("name", READ_ONLY)
def test_readiness_scripts_never_save_simulate_or_parallelise(name):
    code = _code(ML / name)
    for pat in FORBIDDEN:
        assert not re.search(pat, code), f"{name}: forbidden call {pat}"
    for m in re.finditer(r"set_param\s*\(([^;]*)\)", code):            # only the update-diagram command is allowed
        assert "'SimulationCommand', 'update'" in m.group(1), f"{name}: set_param changes a value: {m.group(0)}"
    for m in re.finditer(r"close_system\s*\(([^)]*)\)", code):          # always without saving
        assert m.group(1).strip().endswith("0"), f"{name}: close_system without the no-save flag"


def test_released_models_are_only_ever_copied_never_loaded_directly():
    code = _code(ML / "h2prism_smoke_test_models.m") + _code(ML / "h2prism_check_h2_integration.m")
    assert "load_system(rel" not in code and "open_system" not in code
    assert code.count("copyfile(rel") == 2


def test_gas_application_is_gated():
    code = _code(ML / "h2prism_apply_h2_gas_to_copy.m")
    for guard in ("startsWith(copyModel, 'h2net_v1_')", "/data/raw/", "'DECIDED'", "realGasSpecValue", "h2prism:grant"):
        assert guard in code
    assert "save_system" not in code and not re.search(r"\bsim\s*\(", code)


def _write(d, env_checks, smoke_checks, integ_checks, stopped=""):
    (d / "ENVIRONMENT_REPORT.json").write_text(json.dumps({"checks": env_checks}))
    (d / "SMOKE_REPORT.json").write_text(json.dumps({"checks": smoke_checks, "extra": {"stopped": stopped}}))
    (d / "H2_INTEGRATION_REPORT.json").write_text(json.dumps({"checks": integ_checks, "extra": {"build_gate": "CLOSED"}}))


def _ok_reports():
    c = lambda i, s="PASS", det="": {"id": i, "name": i, "status": s, "detail": det}
    env = [c("E1"), c("E2.1"), c("E3.1"), c("E4"), c("E5"), c("E6"), c("E8.1"), c("E8.S"), c("E9.1"), c("E10.1")]
    env += [c(f"E7.{k}") for k in range(1, 7)]
    smoke = []
    for k in range(1, 7):
        for suf in cmr.SMOKE_SUFFIXES:
            smoke.append(c(f"M{k}{suf}", "SKIP", "no interface registered for anomalous models") if (suf == ".8" and k <= 3) else c(f"M{k}{suf}"))
    return env, smoke, [c(i) for i in ("I1", "I2", "I3", "I4", "I5")]


def test_checker_passes_complete_reports_and_reports_build_gate(tmp_path):
    _write(tmp_path, *_ok_reports())
    r = cmr.evaluate(tmp_path)
    assert r["verdict"] == "READY_FOR_AUTHORIZED_STEPS" and any("build gate: CLOSED" in n for n in r["notes"])


@pytest.mark.parametrize("mutate", ["gas_mismatch", "missing_model", "compile_fail", "stopped", "no_integration", "memory"])
def test_checker_fails_on_any_required_failure(tmp_path, mutate):
    env, smoke, integ = _ok_reports()
    stopped = ""
    if mutate == "gas_mismatch":
        next(c for c in smoke if c["id"] == "M2.5")["status"] = "FAIL"
    if mutate == "missing_model":
        env = [c for c in env if c["id"] != "E7.6"]
    if mutate == "compile_fail":
        next(c for c in smoke if c["id"] == "M5.9")["status"] = "FAIL"
    if mutate == "stopped":
        stopped = "stopped before X: 900 MB available < 1500 MB"
    if mutate == "no_integration":
        integ = [c for c in integ if c["id"] != "I5"]
    if mutate == "memory":
        next(c for c in env if c["id"] == "E4")["status"] = "FAIL"
    _write(tmp_path, env, smoke, integ, stopped)
    assert cmr.evaluate(tmp_path)["verdict"] == "NOT_READY"


def test_checker_refuses_missing_reports(tmp_path):
    r = cmr.evaluate(tmp_path)
    assert r["verdict"] == "NOT_READY" and len(r["problems"]) == 3
