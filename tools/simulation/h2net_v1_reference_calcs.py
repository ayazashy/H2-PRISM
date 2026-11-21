#!/usr/bin/env python3
"""
H2Net v1 CANDIDATE reference calculations (X03 support; inputs to S4, S5, S6). ENGINEERING EVIDENCE, NOT DECISIONS and
NOT X06 V2 targets (those need decided operating points). Uses the hash-verified normal-hydrogen tables and the
grant-bound reference code src/h2prism/gas_physics.py UNCHANGED (only its public functions are called).

  A  choked flow of the RELEASED withdrawal orifices (1e-3 m^2, Cd 0.64) and the released terminal vent (Pipe (G)5 exit,
     0.0989 m^2) with hydrogen, versus the velocity-limited capacity of the 1.2 m line -> S4 (demands / vents)
  B  roughness sensitivity of the pressure drop: proposed 0.02 / 0.045 / 0.1 mm versus the released values -> S6
  C  candidate leak orifice areas for 0.5 / 2 / 10 % of a candidate nominal throughput -> S4
  E  envelope consistency of the candidate leak areas (sized once at 5 MPa, 313 K) over 2-8 MPa x 283-313 K, for demand
     that scales with line capacity and for a FIXED nominal demand (kg/s) -> S4 / V8
  F  20 m/s capacity of every released pipe diameter over the envelope; largest nominal that is feasible at the lowest
     pressure -> S4 nominal, V8
  G  isentropic discharge temperature of the released compressor (dp = 4 MPa) over suction 2-6 MPa, 283-313 K -> S3, V3
  D  Simscape Pipe (G) lumping (one internal node per block, density at that node; installed pipe.ssc) versus the
     distributed RK4 solution, as a function of the number of segments -> S5 discretisation
Perfect-gas orifice formula evaluated with LOCAL hydrogen Z and cp (gamma = cp / (cp - Z R)); this is an approximation
for choked real-gas flow and is labelled as such. Output: 06_audit_preparation/simulation/h2net_v1/candidate/REFERENCE_CALCS.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from h2prism.gas_physics import PerfectGas, Pipe, friction_factor, orifice_mass_flow, pipe_outlet_pressure  # noqa: E402
from h2net_v1_reference import load_h2_tables  # noqa: E402

OUT = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "candidate" / "REFERENCE_CALCS.json"
P_ATM = 101325.0
CD_RELEASED, A_WITHDRAWAL, A_VENT = 0.64, 1e-3, 0.0989
D_MAIN, V_LIMIT = 1.2, 20.0


def local_perfect(gas, p, T):
    pr = gas.props(p, T)
    return PerfectGas(R=gas.R, Z=pr["Z"], cp=pr["cp"], mu=pr["mu"], k=pr["k"], name="H2_local")


def capacity(gas, p, T, D=D_MAIN, v=V_LIMIT):
    return gas.rho(p, T) * np.pi * D ** 2 / 4 * v


def part_a(gas):
    rows = []
    for T in (283.15, 313.15):
        for p_mpa in (2.0, 5.0, 8.0):
            p = p_mpa * 1e6
            g = local_perfect(gas, p, T)
            m_w = orifice_mass_flow(p, P_ATM, T, A_WITHDRAWAL, g, CD_RELEASED)
            m_v = orifice_mass_flow(p, P_ATM, T, A_VENT, g, 1.0)
            cap = capacity(gas, p, T)
            rows.append({"T_K": T, "p_MPa": p_mpa, "gamma_local": g.gamma(), "withdrawal_kg_s": m_w,
                         "four_withdrawals_kg_s": 4 * m_w, "terminal_vent_upper_bound_kg_s": m_v,
                         "capacity_1p2m_at_20m_s_kg_s": cap, "withdrawal_share_of_capacity": m_w / cap,
                         "vent_over_capacity": m_v / cap})
    return rows


def part_b(gas, T=313.15, p_in=5e6, v=10.0):
    released = {"Pipe (G)5 (0.0045 mm)": 4.5e-6, "Pipe (G)1 (0.045 mm)": 4.5e-5, "Pipe (G)3/8 (0.45 mm)": 4.5e-4,
                "Pipe (G)2 (4.5 mm)": 4.5e-3, "Pipe (G)6 down (45 mm)": 4.5e-2, "Pipe (G)4/7 (50 mm)": 5e-2}
    proposed = {"proposed 0.02 mm": 2e-5, "proposed 0.045 mm": 4.5e-5, "proposed 0.1 mm": 1e-4}
    pipe_L = 16000.0
    mdot = gas.rho(p_in, T) * np.pi * D_MAIN ** 2 / 4 * v
    rows = []
    for label, eps in {**proposed, **released}.items():
        pp = Pipe("a", "b", pipe_L, D_MAIN, eps)
        p_out, _ = pipe_outlet_pressure(pp, p_in, mdot, T, gas)
        mu = gas.props(p_in, T)["mu"]
        Re = mdot * D_MAIN / (pp.area * mu)
        rows.append({"case": label, "roughness_m": eps, "Re": Re, "f_haaland": friction_factor(Re, eps / D_MAIN),
                     "dp_kPa_16km_1p2m_10m_s": (p_in - p_out) / 1e3})
    return {"state": {"T_K": T, "p_in_MPa": p_in / 1e6, "v_in_m_s": v, "mdot_kg_s": mdot}, "rows": rows}


def part_c(gas, T=313.15, p=5e6):
    nominal = 0.5 * capacity(gas, p, T)
    g = local_perfect(gas, p, T)
    flux = orifice_mass_flow(p, P_ATM, T, 1.0, g, 1.0)                    # choked mass flow per m^2 at Cd = 1
    rows = []
    for frac in (0.005, 0.02, 0.10):
        for cd in (0.61, 0.64, 1.0):
            area = frac * nominal / (cd * flux)
            rows.append({"fraction_of_nominal": frac, "Cd": cd, "area_m2": area, "equivalent_diameter_mm": 2e3 * np.sqrt(area / np.pi)})
    return {"nominal_throughput_kg_s": nominal, "nominal_definition": "candidate: 50 % of the 20 m/s capacity of the 1.2 m line at 5 MPa, 313.15 K",
            "rows": rows}


def lumped_chain(gas, pipe: Pipe, p_in, mdot, T, n_seg, length_add=0.0):
    """Simscape Pipe (G) steady form per block: two half-length friction losses evaluated at the internal-node density
    (installed foundation.gas.elements.pipe, dynamic compressibility on, inertia off). n_seg blocks in series."""
    p = p_in
    L_eff = pipe.length / n_seg + length_add
    for _ in range(n_seg):
        pI = p
        for _ in range(100):
            rho = gas.rho(pI, T)
            mu = gas.props(pI, T)["mu"]
            Re = mdot * pipe.diameter / (pipe.area * mu)
            f = friction_factor(Re, pipe.roughness / pipe.diameter)
            half = f * mdot * abs(mdot) * (L_eff / 2) / (2 * rho * pipe.diameter * pipe.area ** 2)
            new = p - half
            if abs(new - pI) < 1e-6:
                break
            pI = new
        p = pI - half
    return p


def part_d(gas, T=313.15, p_in=5e6, v=20.0):
    rows = []
    for L, D, eps in ((30000.0, 1.2, 4.5e-5), (16000.0, 1.2, 4.5e-5), (4000.0, 0.355, 4.5e-5)):
        pipe = Pipe("a", "b", L, D, eps, n_steps=2000)
        mdot = gas.rho(p_in, T) * pipe.area * v
        p_ref, _ = pipe_outlet_pressure(pipe, p_in, mdot, T, gas)
        dp_ref = p_in - p_ref
        prev = None
        for n in (1, 2, 4, 8, 16, 32):
            p_l = lumped_chain(gas, pipe, p_in, mdot, T, n)
            err = (p_in - p_l - dp_ref) / dp_ref
            halving = None if prev is None else abs((p_in - p_l) - prev) / prev
            rows.append({"length_m": L, "Dh_m": D, "segments": n, "segment_km": L / n / 1e3, "dp_kPa_distributed": dp_ref / 1e3,
                         "dp_kPa_lumped": (p_in - p_l) / 1e3, "relative_error_vs_distributed": err,
                         "relative_change_on_halving": halving})
            prev = p_in - p_l
    return {"state": {"T_K": T, "p_in_MPa": p_in / 1e6, "v_in_m_s": v}, "rows": rows}


def part_e(gas, leak_cd=0.64):
    c = part_c(gas)
    nominal = c["nominal_throughput_kg_s"]
    areas = {r["fraction_of_nominal"]: r["area_m2"] for r in c["rows"] if r["Cd"] == leak_cd}
    rows = []
    for T in (283.15, 313.15):
        for p_mpa in (2.0, 3.0, 5.0, 8.0):
            p = p_mpa * 1e6
            g = local_perfect(gas, p, T)
            cap = capacity(gas, p, T)
            for frac, a in areas.items():
                m_leak = orifice_mass_flow(p, P_ATM, T, a, g, leak_cd)
                rows.append({"T_K": T, "p_MPa": p_mpa, "design_fraction": frac, "leak_kg_s": m_leak,
                             "fraction_if_demand_scales_with_capacity": m_leak / (0.5 * cap),
                             "fraction_if_demand_fixed_at_nominal": m_leak / nominal,
                             "fixed_nominal_feasible_at_20m_s": bool(nominal <= cap),
                             "choked": bool(p / P_ATM > (2 / (g.gamma() + 1)) ** (-g.gamma() / (g.gamma() - 1)))})
    return {"nominal_kg_s": nominal, "leak_areas_m2": areas, "rows": rows}


def part_f(gas):
    diam = {"1.2 m (Pipe 1, 2, 3, 8)": 1.2, "1.0 m (Pipe 4, 7)": 1.0, "0.4 m (Pipe 6, down)": 0.4, "0.355 m (Pipe 5)": 0.355}
    rows = []
    for T in (283.15, 313.15):
        for p_mpa in (2.0, 3.0, 5.0, 8.0):
            for label, D in diam.items():
                rows.append({"T_K": T, "p_MPa": p_mpa, "pipe": label, "capacity_20m_s_kg_s": capacity(gas, p_mpa * 1e6, T, D)})
    worst = min(r["capacity_20m_s_kg_s"] for r in rows if r["pipe"].startswith("1.2") and r["p_MPa"] == 2.0)
    return {"rows": rows, "max_nominal_feasible_at_2MPa_313K_in_1p2m_kg_s": worst}


def part_g(gas, dp=4e6):
    rows = []
    for T1 in (283.15, 313.15):
        for p1_mpa in (2.0, 3.0, 4.0, 6.0):
            p1 = p1_mpa * 1e6
            p2 = p1 + dp
            # isentropic exponent from the local gamma at suction and discharge pressure (ideal-gas-like estimate)
            g1 = local_perfect(gas, p1, T1).gamma()
            T2 = T1 * (p2 / p1) ** ((g1 - 1) / g1)
            g2 = local_perfect(gas, p2, min(T2, 500.0)).gamma()
            gm = 0.5 * (g1 + g2)
            T2 = T1 * (p2 / p1) ** ((gm - 1) / gm)
            rows.append({"T_suction_K": T1, "p_suction_MPa": p1_mpa, "p_discharge_MPa": p2 / 1e6, "pressure_ratio": p2 / p1,
                         "gamma_mean": gm, "T_discharge_isentropic_K": T2, "above_330K": bool(T2 > 330.0),
                         "outside_table_500K": bool(T2 > 500.0)})
    return {"note": "ideal-gas isentropic relation with mean local gamma; real-gas isentropic path not computed", "rows": rows}


def build():
    gas = load_h2_tables()
    return {"status": "CANDIDATE_ENGINEERING_EVIDENCE (not decisions; not X06 targets)", "gas": gas.source,
            "A_released_orifices_and_vent": part_a(gas), "B_roughness_sensitivity": part_b(gas),
            "C_candidate_leak_areas": part_c(gas), "D_lumping_vs_segments": part_d(gas),
            "E_leak_consistency_over_envelope": part_e(gas), "F_capacity_over_envelope": part_f(gas),
            "G_compressor_discharge_temperature": part_g(gas)}


def main(argv) -> int:
    doc = build()
    text = json.dumps(doc, indent=1) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("reference calcs: " + ("current" if ok else "STALE"))
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    a = doc["A_released_orifices_and_vent"]
    print("A  T     p   gamma  withdrawal  4x     vent_ub   capacity  vent/cap")
    for r in a:
        print(f"   {r['T_K']:.0f} {r['p_MPa']:.0f}  {r['gamma_local']:.3f}  {r['withdrawal_kg_s']:.2f}  {r['four_withdrawals_kg_s']:.2f}  "
              f"{r['terminal_vent_upper_bound_kg_s']:.0f}  {r['capacity_1p2m_at_20m_s_kg_s']:.1f}  {r['vent_over_capacity']:.2f}")
    print("B ", [(r["case"], round(r["dp_kPa_16km_1p2m_10m_s"], 2)) for r in doc["B_roughness_sensitivity"]["rows"]])
    c = doc["C_candidate_leak_areas"]
    print("C  nominal", round(c["nominal_throughput_kg_s"], 1), [(r["fraction_of_nominal"], r["Cd"], round(r["equivalent_diameter_mm"], 1)) for r in c["rows"] if r["Cd"] == 0.64])
    print("D ", [(r["length_m"], r["segments"], f"{r['relative_error_vs_distributed']:.2e}", None if r["relative_change_on_halving"] is None else f"{r['relative_change_on_halving']:.2e}") for r in doc["D_lumping_vs_segments"]["rows"]])
    e = doc["E_leak_consistency_over_envelope"]
    print("E ", [(r["T_K"], r["p_MPa"], r["design_fraction"], round(r["fraction_if_demand_scales_with_capacity"], 4), round(r["fraction_if_demand_fixed_at_nominal"], 4), r["fixed_nominal_feasible_at_20m_s"]) for r in e["rows"] if r["T_K"] == 313.15])
    f = doc["F_capacity_over_envelope"]
    print("F  max nominal at 2 MPa", round(f["max_nominal_feasible_at_2MPa_313K_in_1p2m_kg_s"], 1), [(r["p_MPa"], r["pipe"][:6], round(r["capacity_20m_s_kg_s"], 1)) for r in f["rows"] if r["T_K"] == 313.15])
    print("G ", [(r["T_suction_K"], r["p_suction_MPa"], round(r["pressure_ratio"], 2), round(r["T_discharge_isentropic_K"], 0)) for r in doc["G_compressor_discharge_temperature"]["rows"]])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
