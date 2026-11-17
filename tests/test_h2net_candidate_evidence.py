"""Read-only released-network extraction and candidate H2 reference calcs are reproducible and consistent."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CAND = ROOT / "06_audit_preparation" / "simulation" / "h2net_v1" / "candidate"


def _run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / "tools" / "simulation" / script), *args], capture_output=True, text=True)


def test_released_network_extraction_is_current_and_matches_known_structure():
    assert _run("extract_released_network.py", "--check").returncode == 0
    g = json.loads((CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    assert len(g) == 6 and {m["gas_properties"]["gas_spec"] for m in g.values()} == {"1"}
    for name, m in g.items():
        ps = [c for c in m["components"] if c["class"] == "pressure_source"]
        assert all(c["params"]["power_spec"].endswith("isentropic") for c in ps)
        assert len(ps) == (3 if name.endswith("down") else 2)


@pytest.mark.slow
def test_reference_calcs_are_current_and_support_the_recorded_findings():
    assert _run("h2net_v1_reference_calcs.py", "--check").returncode == 0
    d = json.loads((CAND / "REFERENCE_CALCS.json").read_text(encoding="utf-8"))
    assert all(r["vent_over_capacity"] > 3 for r in d["A_released_orifices_and_vent"])
    assert max(abs(r["relative_error_vs_distributed"]) for r in d["D_lumping_vs_segments"]["rows"]) < 1e-5
    b = {r["case"]: r["dp_kPa_16km_1p2m_10m_s"] for r in d["B_roughness_sensitivity"]["rows"]}
    assert b["Pipe (G)4/7 (50 mm)"] > 5 * b["proposed 0.045 mm"]


@pytest.mark.slow
def test_envelope_consistency_findings_quoted_in_the_decision_package():
    d = json.loads((CAND / "REFERENCE_CALCS.json").read_text(encoding="utf-8"))
    e = d["E_leak_consistency_over_envelope"]["rows"]
    assert all(r["choked"] for r in e)
    assert not any(r["fixed_nominal_feasible_at_20m_s"] for r in e if r["p_MPa"] == 2.0)
    scal = [r["fraction_if_demand_scales_with_capacity"] / r["design_fraction"] for r in e]
    fixed = [r["fraction_if_demand_fixed_at_nominal"] / r["design_fraction"] for r in e]
    assert 0.93 < min(scal) and max(scal) < 1.06 and min(fixed) < 0.45 and max(fixed) > 1.6
    g = [r["T_discharge_isentropic_K"] for r in d["G_compressor_discharge_temperature"]["rows"]]
    assert min(g) >= 329 and max(g) < 500
    pkg = (CAND.parent / "H2NET_V1_DECISION_PACKAGE.md").read_text(encoding="utf-8")
    assert "Not sent, not approved" in pkg and "OWNER_DECISIONS_REQUIRED" in pkg
