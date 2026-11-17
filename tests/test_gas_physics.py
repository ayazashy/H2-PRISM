"""Invariants of the MATLAB-free gas-physics references (src/h2prism/gas_physics.py). Expected values are analytic or
classical (Moody chart region), justified in each test; no hydrogen property data are assumed."""

from __future__ import annotations

import numpy as np
import pytest

from h2prism import gas_physics as gp


pytestmark = pytest.mark.slow
# released H2-SimNet Gas Properties (G) active perfect-gas constants (all six models, block SID 4), SI units
RELEASED = gp.PerfectGas(R=287.0, Z=0.998386, cp=346.9, mu=10.98e-6, k=48.2e-3, name="released_h2simnet")
AIR = gp.PerfectGas(R=287.0, Z=1.0, cp=1005.0, mu=18.2e-6, k=25.9e-3, name="air_textbook")


def test_hydrogen_gas_constant_from_codata():
    assert gp.R_H2 == pytest.approx(4124.2, abs=0.5)


def test_released_constants_fail_and_textbook_air_passes():
    v = gp.check_gas_properties(RELEASED, molar_mass=gp.M_H2)
    assert any("gamma" in s for s in v) and any("Prandtl" in s for s in v) and any("molar mass" in s for s in v)
    assert RELEASED.gamma() == pytest.approx(5.747, abs=0.01)
    assert gp.check_gas_properties(AIR, molar_mass=28.965e-3) == []


def test_tabulated_gas_interpolates_exactly_on_grid_and_refuses_extrapolation():
    T, p = np.array([250.0, 300.0, 350.0]), np.array([1e5, 5e6, 1e7])
    Z = np.array([[1.0, 1.03, 1.06], [1.0, 1.02, 1.05], [1.0, 1.02, 1.04]])
    one = np.ones((3, 3))
    g = gp.TabulatedGas(R=gp.R_H2, T=T, p=p, Z=Z, cp=14000 * one, mu=9e-6 * one, k=0.18 * one, source="synthetic test")
    assert g.z(5e6, 300.0) == pytest.approx(1.02)
    assert g.z(2.55e6, 275.0) == pytest.approx(np.mean([1.0, 1.03, 1.0, 1.02]), rel=1e-3)
    with pytest.raises(ValueError):
        g.z(2e7, 300.0)
    with pytest.raises(ValueError):
        g.z(5e6, 400.0)


def test_friction_factor_limits():
    assert gp.friction_factor(1000, 1e-4) == pytest.approx(0.064)
    f_cb = gp.friction_factor(1e6, 1e-4, "colebrook")
    assert f_cb == pytest.approx(0.0134, abs=3e-4)                       # Moody chart
    assert gp.friction_factor(1e6, 1e-4, "haaland") == pytest.approx(f_cb, rel=0.02)
    f2, f3 = gp.friction_factor(2000, 1e-4), gp.friction_factor(4000, 1e-4)
    assert min(f2, f3) <= gp.friction_factor(3000, 1e-4) <= max(f2, f3)  # continuous blend


def test_pipe_matches_isothermal_closed_form_for_constant_f():
    gas = gp.PerfectGas(R=gp.R_H2, Z=1.0, cp=14300.0, mu=8.9e-6, k=0.18)
    pipe = gp.Pipe("a", "b", length=20000.0, diameter=0.6, roughness=4.5e-5, n_steps=400)
    m, T, f, p1 = 20.0, 288.15, 0.012, 6.0e6
    p2, mach = gp.pipe_outlet_pressure(pipe, p1, m, T, gas, f_const=f)
    assert p1 ** 2 - p2 ** 2 == pytest.approx(gp.isothermal_closed_form_dp2(pipe, m, T, gas.R, 1.0, f), rel=1e-6)
    assert mach < 0.3


def test_series_pipes_equal_one_long_pipe():
    gas = gp.PerfectGas(R=gp.R_H2, Z=1.0, cp=14300.0, mu=8.9e-6, k=0.18)
    a = gp.Pipe("a", "m", 8000.0, 0.6, 4.5e-5)
    b = gp.Pipe("m", "b", 12000.0, 0.6, 4.5e-5)
    ab = gp.Pipe("a", "b", 20000.0, 0.6, 4.5e-5, n_steps=400)
    pm, _ = gp.pipe_outlet_pressure(a, 6e6, 15.0, 288.15, gas)
    pb, _ = gp.pipe_outlet_pressure(b, pm, 15.0, 288.15, gas)
    p_direct, _ = gp.pipe_outlet_pressure(ab, 6e6, 15.0, 288.15, gas)
    assert pb == pytest.approx(p_direct, rel=1e-6)


def test_choked_orifice_matches_textbook_formula():
    p0, T0, A = 5e6, 288.15, 1e-3
    m = gp.orifice_mass_flow(p0, 1e5, T0, A, AIR)
    g = AIR.gamma()
    expected = A * p0 * np.sqrt(g / (AIR.R * T0)) * (2 / (g + 1)) ** ((g + 1) / (2 * (g - 1)))
    assert m == pytest.approx(expected, rel=1e-9)
    assert gp.orifice_mass_flow(p0, 0.99 * p0, T0, A, AIR) < m                     # unchoked: less
    assert gp.orifice_mass_flow(p0, p0, T0, A, AIR) == 0.0


def test_network_conserves_mass_and_converges():
    """Supply at 6 MPa feeding a junction that splits to a demand node and an orifice withdrawal: at convergence
    the supply flow equals the total withdrawal and pressures decrease along the flow."""
    gas = gp.PerfectGas(R=gp.R_H2, Z=1.0, cp=14300.0, mu=8.9e-6, k=0.18)
    net = gp.Network(T=288.15, gas=gas, fixed_pressure={"S": 6.0e6},
                     pipes=[gp.Pipe("S", "J", 10000.0, 0.6, 4.5e-5, 100), gp.Pipe("J", "D1", 5000.0, 0.4, 4.5e-5, 100),
                            gp.Pipe("J", "D2", 4000.0, 0.3, 4.5e-5, 100)],
                     demands={"D1": 8.0}, orifices={"D2": (2e-4, 0.8, 1.0e5)})
    s = net.solve()
    assert s["converged"] and s["max_relative_mass_residual"] < 1e-6
    P, F = s["pressures"], s["flows"]
    orifice = gp.orifice_mass_flow(P["D2"], 1e5, 288.15, 2e-4, gas, 0.8)
    assert F["S->J"] == pytest.approx(8.0 + orifice, rel=1e-5)
    assert P["S"] > P["J"] > P["D1"] and P["J"] > P["D2"]
