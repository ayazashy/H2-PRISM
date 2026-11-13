"""H2Net v1 step (a): the generated normal-hydrogen tables load into the independent reference, are physically
consistent inside the envelope, match their recorded hashes and V1 report, and drive a converging real-gas network."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "simulation"))
PROPS = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "properties"

import h2net_v1_reference as ref  # noqa: E402
from h2prism import gas_physics as gp  # noqa: E402


def test_outputs_match_recorded_hashes_and_v1_passed():
    for line in (PROPS / "OUTPUT_HASHES.sha256").read_text(encoding="utf-8").splitlines():
        h, name = line.split()
        assert hashlib.sha256((PROPS / name).read_bytes()).hexdigest() == h, name
    rep = json.loads((PROPS / "V1_REPORT.json").read_text(encoding="utf-8"))
    assert rep["checks"]["V1_PASS"] is True and rep["checks"]["interpolation_points"] >= 50
    assert rep["meta"]["coolprop_version"] == "7.2.0"
    assert "Leachman" in rep["meta"]["references"]["BibTeX-EOS"]


def test_tables_have_simscape_layout_and_hydrogen_constants():
    j = json.loads((PROPS / "H2_REALGAS_TLU2.json").read_text(encoding="utf-8"))
    d = j["data"]
    nT, nP = len(d["T_TLU2"]), len(d["p_TLU2"])
    for k in ("rho", "s", "h", "cp", "mu", "k", "beta", "alpha"):
        assert np.array(d[f"{k}_TLU2"]).shape == (nT, nP), k
    assert d["R_kJ_per_kgK"] * 1e3 == pytest.approx(gp.R_UNIVERSAL / gp.M_H2, rel=1e-9)
    assert min(d["p_TLU2"]) <= 0.1 and max(d["p_TLU2"]) >= 10 and min(d["T_TLU2"]) <= 250 and max(d["T_TLU2"]) >= 400


def test_loaded_gas_is_physically_consistent_in_the_envelope():
    g = ref.load_h2_tables()
    pts = [(p * 1e6, T) for p in (0.1, 1.0, 5.0, 10.0) for T in (250.0, 300.0, 400.0)]
    assert gp.check_gas_properties(g, molar_mass=gp.M_H2, points=pts) == []
    assert 1.05 < g.z(10e6, 250.0) < 1.08                 # real-gas effect at 10 MPa (ideal gas would say 1)
    assert g.rho(101325.0, 273.15) == pytest.approx(0.0899, rel=3e-3)


def test_real_gas_network_converges_and_conserves_mass():
    g = ref.load_h2_tables()
    net = gp.Network(T=288.15, gas=g, fixed_pressure={"S": 7.0e6},
                     pipes=[gp.Pipe("S", "J", 16000.0, 1.2, 4.5e-5, 100), gp.Pipe("J", "D", 11000.0, 1.2, 4.5e-5, 100)],
                     demands={"D": 30.0})
    s = net.solve()
    assert s["converged"] and s["flows"]["S->J"] == pytest.approx(30.0, rel=1e-5)
    assert s["pressures"]["S"] > s["pressures"]["J"] > s["pressures"]["D"] > 0


def test_tampered_tables_are_refused(tmp_path):
    bad = tmp_path / "H2_REALGAS_TLU2.json"
    bad.write_bytes((PROPS / "H2_REALGAS_TLU2.json").read_bytes().replace(b"1.0", b"1.1", 1))
    with pytest.raises(ValueError):
        ref.load_h2_tables(bad)
