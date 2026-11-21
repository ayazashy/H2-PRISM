#!/usr/bin/env python3
"""
H2Net v1 design-freeze calculations (PROVISIONAL, independent steady-state reference; NOT X06 targets, no MATLAB, no
dataset). Evaluates the approval-checklist proposals D1 (split compression C1 -> 5.0 MPa, C2 -> 6.5 MPa) and D7 (supply
3.2 MPa) on the three released topologies with the solver of h2net_v1_provisional_network.py (unchanged physics):
  A  nominal D1+D7 operating point: feasibility, compressor temperatures / power / cooler duty (real-gas tables)
  B  NORMAL load extremes (x0.5, x1.5)
  C  fault states with FIXED-dp compressor semantics (Simscape Pressure Source (G) imposes a pressure differential):
     C1 trip, C1 at 50 % dp, C2 trip, C2 at 50 % dp  -> fault-envelope check (>= 2.5 MPa proposed)
  D  steady-state event signatures vs NORMAL: leak 0.5 / 2 / 10 % of total demand (as an extra sink at the G3 node,
     CV_A, and at the G4 node, CV_B; a mid-pipe leak lies between the adjacent node values), compressor faults
  E  line-pack coefficients dM/dp per pipe and per mass-balance control volume, from the hydrogen density tables
Output: 06_audit_preparation/simulation/h2net_v1/candidate/DESIGN_FREEZE_CALCS.json   (--check: stale -> exit 1)
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_provisional_network as pn  # noqa: E402

OUT = pn.CAND / "DESIGN_FREEZE_CALCS.json"
D1D7 = {"supply_MPa": 3.2, "discharge_MPa": {"C1": 5.0, "C2": 6.5}}
CV = {  # mass-balance control volumes: pipes inside, by released pipe SID
    "center": {"CV_A": ["47", "48", "49", "309"], "CV_B": ["106", "221", "107"]},
    "up": {"CV_A": ["47", "48", "49", "309", "107"], "CV_B": ["106", "221"]},
    "down": {"CV_A": ["47", "48", "49", "309"], "CV_B": ["106", "221", "108"]},
}
POS = {"Normal_HNetwork_gest_center": "center", "Normal_HNetwork_gest_up": "up", "Normal_HNetwork_gest_down": "down"}


def params(base, **kw):
    p = copy.deepcopy(base)
    p.update(copy.deepcopy(D1D7))
    for k, v in kw.items():
        p[k] = v
    return p


def fixed_dp(graph, prm, gas, thermo, dp_scale):
    """Compressors as fixed pressure differentials: dp_k = scale_k * nominal dp_k; iterate the discharge set-points."""
    nom = pn.solve(graph, prm, gas, thermo)
    dps = {c["compressor"]: c["dp_MPa"] for c in nom["compressors"]}
    p = copy.deepcopy(prm)
    for _ in range(6):
        p["discharge_MPa"]["C1"] = p["supply_MPa"] + dp_scale["C1"] * dps["C1"]
        r = pn.solve(graph, p, gas, thermo) if p["discharge_MPa"]["C2"] >= 0 else None
        suction2 = next(c["p_suction_MPa"] for c in r["compressors"] if c["compressor"] == "C2")
        p["discharge_MPa"]["C2"] = suction2 + dp_scale["C2"] * dps["C2"]
    return pn.solve(graph, p, gas, thermo), dps


def summary(r):
    c = r["checks"]
    out = {"feasible_normal_envelope": c["feasible"], "min_pipe_pressure_MPa": c["min_pipe_pressure_MPa"],
           "max_pipe_pressure_MPa": c["max_pipe_pressure_MPa"], "max_outlet_velocity_m_s": c["max_outlet_velocity_m_s"],
           "mass_residual_kg_s": c["mass_conservation_max_residual_kg_s"]}
    for k in r["compressors"]:
        out[k["compressor"]] = {kk: k[kk] for kk in ("p_suction_MPa", "p_discharge_MPa", "dp_MPa", "mdot_kg_s",
                                                     "T_discharge_isentropic_K", "power_isentropic_kW", "T_discharge_eta0.75_K",
                                                     "power_eta0.75_kW", "aftercooler_duty_eta0.75_kW")}
    return out


def line_pack(graph, r, gas, T):
    pipes = {c["sid"]: c for c in graph["components"] if c["class"] == "pipe"}
    rows = {}
    for e in r["pipes"]:
        c = pipes[e["sid"]]
        D = pn._len(c["params"]["Dh"])
        L = pn._len(c["params"]["length"])
        p = 0.5 * (e["p_in_MPa"] + e["p_out_MPa"]) * 1e6
        drho = (gas.rho(p + 1e4, T) - gas.rho(p - 1e4, T)) / 2e4
        rows[e["sid"]] = {"name": e["name"], "volume_m3": np.pi * D ** 2 / 4 * L, "mean_p_MPa": p / 1e6,
                          "dM_dp_kg_per_kPa": np.pi * D ** 2 / 4 * L * drho * 1e3, "mass_kg": np.pi * D ** 2 / 4 * L * gas.rho(p, T)}
    return rows


def build():
    P = yaml.safe_load((pn.CAND / "PARAMETER_DECISIONS_PROPOSED.yaml").read_text(encoding="utf-8"))
    graphs = json.loads((pn.CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    gas, thermo = pn.load_h2_tables(), pn.Thermo()
    base = pn.base_params(P)
    out = {"status": "PROVISIONAL_EXPLORATORY (D1+D7 proposals; not owner decisions; not X06 targets)",
           "assumptions": ["isothermal pipes at T_ref after aftercoolers", "compressors as pressure-rise elements, fixed dp in faults",
                           "leak modelled as an extra sink at a network node (steady state); choked leak flow independent of downstream",
                           "steady states only: transient signatures (DELAY, onset dynamics, line-pack) need MATLAB"],
           "D1_D7": D1D7, "models": {}}
    for name, pos in POS.items():
        g = graphs[name]
        prm = params(base)
        nom = pn.solve(g, prm, gas, thermo)
        T = prm["T_ref_K"]
        m = {"A_nominal": summary(nom),
             "B_load": {f"x{s}": summary(pn.solve(g, params(base, demand={k: v * s for k, v in base["demand"].items()}), gas, thermo))
                        for s in (0.5, 1.5)}}
        faults = {}
        for label, sc in (("C1_trip", {"C1": 0.0, "C2": 1.0}), ("C1_half", {"C1": 0.5, "C2": 1.0}),
                          ("C2_trip", {"C1": 1.0, "C2": 0.0}), ("C2_half", {"C1": 1.0, "C2": 0.5})):
            r, dps = fixed_dp(g, prm, gas, thermo, sc)
            s = summary(r)
            s["within_fault_envelope_2p5MPa"] = bool(s["min_pipe_pressure_MPa"] >= 2.5)
            s["node_pressure_change_vs_nominal_kPa"] = {n: (r["node_pressures_MPa"][n] - nom["node_pressures_MPa"][n]) * 1e3
                                                        for n in nom["node_pressures_MPa"]}
            faults[label] = s
        m["C_faults"] = faults
        total = sum(base["demand"].values())
        sig = {}
        for node_sink in ("G3", "G4"):
            for frac in (0.005, 0.02, 0.10):
                d = dict(base["demand"])
                d[node_sink] = d[node_sink] + frac * total
                r = pn.solve(g, params(base, demand=d), gas, thermo)
                dn = {n: (r["node_pressures_MPa"][n] - nom["node_pressures_MPa"][n]) * 1e3 for n in nom["node_pressures_MPa"]}
                sig[f"leak_{frac:.3f}_at_{node_sink}"] = {"leak_kg_s": frac * total, "max_abs_node_dp_kPa": max(abs(v) for v in dn.values()),
                                                         "supply_flow_change_kg_s": r["checks"]["supply_flow_kg_s"] - nom["checks"]["supply_flow_kg_s"]}
        lo = pn.solve(g, params(base, demand={k: v * 0.5 for k, v in base["demand"].items()}), gas, thermo)
        hi = pn.solve(g, params(base, demand={k: v * 1.5 for k, v in base["demand"].items()}), gas, thermo)
        sig["normal_load_x0.5_to_x1.5_max_abs_node_dp_kPa"] = max(abs(hi["node_pressures_MPa"][n] - lo["node_pressures_MPa"][n]) * 1e3 for n in lo["node_pressures_MPa"])
        m["D_signatures"] = sig
        lp = line_pack(g, nom, gas, T)
        cvs = {}
        for cv, sids in CV[pos].items():
            k = sum(lp[s]["dM_dp_kg_per_kPa"] for s in sids if s in lp)
            cvs[cv] = {"pipes": sids, "dM_dp_kg_per_kPa": k, "mass_kg": sum(lp[s]["mass_kg"] for s in sids if s in lp),
                       "dp_dt_resolution_for_0p1_kg_s_Pa_per_s": 0.1 / (k / 1e3)}
        m["E_line_pack"] = {"pipes": lp, "control_volumes": cvs}
        out["models"][name] = m
    return out


def main(argv) -> int:
    text = json.dumps(build(), indent=1, default=float) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("design-freeze calcs: " + ("current" if ok else "STALE"))
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    d = json.loads(text)
    for name, m in d["models"].items():
        a = m["A_nominal"]
        print(f"== {name}: feasible={a['feasible_normal_envelope']} p=[{a['min_pipe_pressure_MPa']:.3f},{a['max_pipe_pressure_MPa']:.3f}] vmax={a['max_outlet_velocity_m_s']:.2f}")
        for c in ("C1", "C2"):
            k = a[c]
            print(f"   {c}: {k['p_suction_MPa']:.3f}->{k['p_discharge_MPa']:.3f} dp={k['dp_MPa']:.3f} T2s={k['T_discharge_isentropic_K']:.1f} P={k['power_isentropic_kW']/1e3:.2f} MW "
                  f"T2(0.75)={k['T_discharge_eta0.75_K']:.1f} P(0.75)={k['power_eta0.75_kW']/1e3:.2f} MW cooler={k['aftercooler_duty_eta0.75_kW']/1e3:.2f} MW")
        for lbl, s in m["B_load"].items():
            print(f"   load {lbl}: feasible={s['feasible_normal_envelope']} pmin={s['min_pipe_pressure_MPa']:.3f} vmax={s['max_outlet_velocity_m_s']:.2f}")
        for lbl, s in m["C_faults"].items():
            print(f"   {lbl}: pmin={s['min_pipe_pressure_MPa']:.3f} pmax={s['max_pipe_pressure_MPa']:.3f} vmax={s['max_outlet_velocity_m_s']:.2f} fault_env={s['within_fault_envelope_2p5MPa']} "
                  f"max|dP|={max(abs(v) for v in s['node_pressure_change_vs_nominal_kPa'].values()):.0f} kPa")
        print("   signatures:", {k: (round(v['max_abs_node_dp_kPa'], 3) if isinstance(v, dict) else round(v, 2)) for k, v in m["D_signatures"].items()})
        print("   line pack:", {k: (round(v['dM_dp_kg_per_kPa'], 1), round(v['dp_dt_resolution_for_0p1_kg_s_Pa_per_s'], 2)) for k, v in m["E_line_pack"]["control_volumes"].items()})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
