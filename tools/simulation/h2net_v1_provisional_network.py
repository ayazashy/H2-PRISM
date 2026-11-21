#!/usr/bin/env python3
"""
H2Net v1 PROVISIONAL steady-state network calculations (exploratory; NOT X06 V2 targets).

The X06 target gate (h2net_v1_envelope_screening.py --targets) stays closed until PARAMETER_DECISIONS.yaml is DECIDED.
This script evaluates the PROPOSED parameter set (candidate/PARAMETER_DECISIONS_PROPOSED.yaml) on the three released
topologies (candidate/RELEASED_NETWORK_GRAPH.json) with the proposed changes applied:
  * Local Restriction (G)3/4/5/6 (SID 213/222/312/215) -> controlled demand sinks G3/G4/G5/G6 at their network node
  * open end vent (atmospheric Reservoir (G) at the end of Pipe (G)5 or (G)6) -> controlled END sink at that node
  * Pressure Source (G)3 (SID 55) and (G)1 (SID 239) -> compressors at a discharge set-point, aftercooled to T_ref
  * down models: Pressure Source (G)6 (SID 111) -> isenthalpic let-down to a set-point (P15 deferred; provisional)
  * fully open Local Restriction (G)2 / (G) (area ratio 0.99987) and flow sensors -> zero-loss connectors
  * Constant Volume Chamber (G) behind Flow Rate Sensor (G)1: single gas port (num_ports = one; the second extracted
    net is its thermal port H on a Perfect Insulator) -> dead-end volume, zero steady flow
Physics: isothermal pipes at T_ref with the grant-bound src/h2prism/gas_physics.py UNCHANGED (Haaland, RK4, effective
length = length + length_add as in installed pipe.ssc); hydrogen Z, mu from the hash-verified CoolProp tables;
compressor heating / power and let-down temperature from the real-gas h(T,p), s(T,p) tables (no ideal-gas exponent).
Output: 06_audit_preparation/simulation/h2net_v1/candidate/PROVISIONAL_STEADY_STATES.json   (--check: stale -> exit 1)
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import yaml
from scipy.optimize import brentq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from h2prism.gas_physics import Pipe, pipe_outlet_pressure  # noqa: E402
from h2net_v1_reference import TABLES, load_h2_tables  # noqa: E402

CAND = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "candidate"
OUT = CAND / "PROVISIONAL_STEADY_STATES.json"
DEMAND_SID = {"213": "G3", "222": "G4", "312": "G5", "215": "G6"}
COMPRESSOR_SID = {"55": "C1", "239": "C2"}
LETDOWN_SID = "111"
MODELS = ("Normal_HNetwork_gest_center", "Normal_HNetwork_gest_up", "Normal_HNetwork_gest_down")
TO_M = {"m": 1.0, "mm": 1e-3}


def _len(s):
    v, u = (s.split() + ["m"])[:2]
    return float(v) * TO_M[u]


class Thermo:
    """h(T, p) [kJ/kg] and s(T, p) [kJ/(kg K)] from the hash-verified real-gas tables (bilinear, no extrapolation)."""

    def __init__(self):
        d = json.loads(Path(TABLES).read_text(encoding="utf-8"))["data"]
        self.T, self.p = np.array(d["T_TLU2"]), np.array(d["p_TLU2"])
        self.h, self.s = np.array(d["h_TLU2"]), np.array(d["s_TLU2"])

    def _i(self, tab, T, p_mpa):
        if not (self.T[0] <= T <= self.T[-1] and self.p[0] <= p_mpa <= self.p[-1]):
            raise ValueError(f"({T} K, {p_mpa} MPa) outside the hydrogen tables")
        i = min(np.searchsorted(self.T, T, "right") - 1, len(self.T) - 2)
        j = min(np.searchsorted(self.p, p_mpa, "right") - 1, len(self.p) - 2)
        a, b = (T - self.T[i]) / (self.T[i + 1] - self.T[i]), (p_mpa - self.p[j]) / (self.p[j + 1] - self.p[j])
        return (1 - a) * (1 - b) * tab[i, j] + a * (1 - b) * tab[i + 1, j] + (1 - a) * b * tab[i, j + 1] + a * b * tab[i + 1, j + 1]

    def h_(self, T, p):
        return self._i(self.h, T, p)

    def s_(self, T, p):
        return self._i(self.s, T, p)

    def T_at(self, prop, value, p):
        f = (lambda T: self.h_(T, p) - value) if prop == "h" else (lambda T: self.s_(T, p) - value)
        return brentq(f, self.T[0], self.T[-1], xtol=1e-6)


def build_network(model: dict):
    """Directed tree from the supply node with edges (kind, sid, data, child); sinks per node."""
    comps = model["components"]
    supply = next(c["nets"][0] for c in comps if c["class"] == "controlled_reservoir")
    pipe_nets = {n for c in comps if c["class"] == "pipe" for n in c["nets"]}
    adj, sinks = defaultdict(list), {}
    for c in comps:
        cls, sid, nets = c["class"], c["sid"], c["nets"]
        if cls == "local_restriction" and sid in DEMAND_SID:
            node = next(n for n in nets if n in pipe_nets)
            sinks[node] = DEMAND_SID[sid]
            continue
        if cls == "reservoir":
            if nets[0] in pipe_nets:                              # the open vent at a pipe end
                sinks[nets[0]] = "END"
            continue
        if cls in ("pipe", "pressure_source", "flow_sensor", "local_restriction", "constant_volume_chamber") and len(nets) == 2:
            for a, b in ((nets[0], nets[1]), (nets[1], nets[0])):
                adj[a].append((cls, sid, c, b))
    tree, seen, order, q = defaultdict(list), {supply}, [supply], deque([supply])
    while q:
        n = q.popleft()
        for cls, sid, c, m in adj[n]:
            if m not in seen:
                seen.add(m)
                tree[n].append((cls, sid, c, m))
                order.append(m)
                q.append(m)
    n_edges = sum(len(v) for v in tree.values())
    assert n_edges == len(seen) - 1, "network is not a tree"
    return supply, tree, sinks, order


def solve(model: dict, prm: dict, gas, thermo: Thermo, n_steps: int = 200) -> dict:
    supply, tree, sinks, order = build_network(model)
    demand = {sinks[n]: 0.0 for n in sinks}
    for k, v in prm["demand"].items():
        if k in demand:
            demand[k] = v
    sub = {}                                                       # subtree demand (= edge flow into the child)
    for n in reversed(order):
        sub[n] = demand.get(sinks.get(n), 0.0) + sum(sub[m] for *_, m in tree[n])
    T, eps = prm["T_ref_K"], prm["roughness_m"]
    p = {supply: prm["supply_MPa"] * 1e6}
    edges, comp, letdown = [], [], None
    for n in order:
        for cls, sid, c, m in tree[n]:
            mdot = sub[m]
            if cls == "pipe":
                L = _len(c["params"]["length"]) + _len(c["params"].get("length_add", "0 m"))
                pp = Pipe(n, m, L, _len(c["params"]["Dh"]), eps, n_steps=n_steps)
                if mdot > 0:
                    p_out, mach = pipe_outlet_pressure(pp, p[n], mdot, T, gas)
                else:
                    p_out, mach = p[n], 0.0
                p[m] = p_out
                v_in, v_out = mdot / (gas.rho(p[n], T) * pp.area), mdot / (gas.rho(p_out, T) * pp.area)
                edges.append({"sid": sid, "name": c["name"], "from": n, "to": m, "mdot_kg_s": mdot, "p_in_MPa": p[n] / 1e6,
                              "p_out_MPa": p_out / 1e6, "dp_kPa": (p[n] - p_out) / 1e3, "v_in_m_s": v_in, "v_out_m_s": v_out,
                              "max_mach": mach, "Dh_m": pp.diameter, "L_eff_m": L})
            elif cls == "pressure_source" and sid in COMPRESSOR_SID:
                p_d = prm["discharge_MPa"][COMPRESSOR_SID[sid]] * 1e6
                if p_d < p[n]:
                    raise ValueError(f"{COMPRESSOR_SID[sid]} set-point below suction pressure")
                p1, p2 = p[n] / 1e6, p_d / 1e6
                h1, s1 = thermo.h_(T, p1), thermo.s_(T, p1)
                T2s = thermo.T_at("s", s1, p2)
                h2s = thermo.h_(T2s, p2)
                rec = {"compressor": COMPRESSOR_SID[sid], "sid": sid, "mdot_kg_s": mdot, "p_suction_MPa": p1, "p_discharge_MPa": p2,
                       "dp_MPa": p2 - p1, "T_suction_K": T, "T_discharge_isentropic_K": T2s,
                       "power_isentropic_kW": mdot * (h2s - h1)}
                for eta in prm["eta"]:
                    h2 = h1 + (h2s - h1) / eta
                    rec[f"T_discharge_eta{eta}_K"] = thermo.T_at("h", h2, p2)
                    rec[f"power_eta{eta}_kW"] = mdot * (h2 - h1)
                    rec[f"aftercooler_duty_eta{eta}_kW"] = mdot * (h2 - thermo.h_(T, p2))
                comp.append(rec)
                p[m] = p_d
            elif cls == "pressure_source" and sid == LETDOWN_SID:
                p_d = prm["letdown_MPa"] * 1e6
                h1 = thermo.h_(T, p[n] / 1e6)
                letdown = {"sid": sid, "p_in_MPa": p[n] / 1e6, "p_out_MPa": p_d / 1e6, "T_in_K": T,
                           "T_out_isenthalpic_K": thermo.T_at("h", h1, p_d / 1e6), "mdot_kg_s": mdot}
                p[m] = p_d
            else:                                                  # flow sensor, open restriction, chamber: no loss
                p[m] = p[n]
    # mass conservation at every node: inflow = sink + outflow
    inflow = defaultdict(float)
    for n in order:
        for *_, m in tree[n]:
            inflow[m] += sub[m]
    inflow[supply] = sum(demand.values())
    resid = max(abs(inflow[n] - demand.get(sinks.get(n), 0.0) - sum(sub[m] for *_, m in tree[n])) for n in order)
    trans = [e for e in edges if e["mdot_kg_s"] > 0]
    pmin = min(min(e["p_in_MPa"], e["p_out_MPa"]) for e in trans)
    pmax = max(max(e["p_in_MPa"], e["p_out_MPa"]) for e in trans)
    vmax = max(trans, key=lambda e: e["v_out_m_s"])
    lo, hi = prm["envelope_MPa"]
    checks = {
        "mass_conservation_max_residual_kg_s": resid,
        "supply_flow_kg_s": inflow[supply], "total_demand_kg_s": sum(demand.values()),
        "min_pipe_pressure_MPa": pmin, "max_pipe_pressure_MPa": pmax,
        "pressures_within_envelope": bool(lo - 1e-9 <= pmin and pmax <= hi + 1e-9),
        "max_outlet_velocity_m_s": vmax["v_out_m_s"], "max_velocity_pipe": vmax["name"],
        "velocity_within_limit": bool(vmax["v_out_m_s"] <= prm["v_limit"]),
        "max_mach": max(e["max_mach"] for e in trans),
        "compressor_discharge_within_tables": bool(all(c["T_discharge_isentropic_K"] < thermo.T[-1] for c in comp)),
        "sinks_found": sorted(set(sinks.values())),
    }
    checks["feasible"] = bool(checks["pressures_within_envelope"] and checks["velocity_within_limit"] and resid < 1e-9)
    return {"checks": checks, "pipes": edges, "compressors": comp, "letdown": letdown,
            "node_pressures_MPa": {n: p[n] / 1e6 for n in order}}


def base_params(P: dict) -> dict:
    s3, s4, env = P["S3_compressor_stations"]["proposal"], P["S4_demand_and_leaks"]["proposal"], P["operating_envelope_V8"]["proposal"]
    return {"supply_MPa": s3["supply_reservoir_pressure_MPa"],
            "discharge_MPa": {"C1": s3["C1_discharge_setpoint_MPa"], "C2": s3["C2_discharge_setpoint_MPa"]},
            "letdown_MPa": 4.0, "demand": dict(s4["nominal_demand_kg_s"]), "T_ref_K": env["isothermal_reference_temperature_K"],
            "roughness_m": P["S6_roughness_and_initial_state"]["proposal"]["roughness_m"],
            "envelope_MPa": env["transmission_pressure_MPa"], "v_limit": env["velocity_limit_m_s"],
            "eta": s3["isentropic_efficiency_for_power_reporting"]}


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build() -> dict:
    P = yaml.safe_load((CAND / "PARAMETER_DECISIONS_PROPOSED.yaml").read_text(encoding="utf-8"))
    graph = json.loads((CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    gas, thermo = load_h2_tables(), Thermo()
    base = base_params(P)
    out = {"status": "PROVISIONAL_EXPLORATORY (proposed parameters, not owner decisions; not X06 V2 targets)",
           "provenance": {"parameters": "candidate/PARAMETER_DECISIONS_PROPOSED.yaml",
                          "parameters_sha256": _sha(CAND / "PARAMETER_DECISIONS_PROPOSED.yaml"),
                          "network_graph_sha256": _sha(CAND / "RELEASED_NETWORK_GRAPH.json"),
                          "h2_tables_sha256": _sha(TABLES), "gas_physics_sha256": _sha(REPO / "src/h2prism/gas_physics.py"),
                          "pipe_integration": "RK4, 200 steps per pipe (tolerance checked against 800 steps below)",
                          "compressor_thermo": "real-gas isentropic path from h(T,p), s(T,p) tables; brentq xtol 1e-6 K"},
           "base_parameters": base, "base": {}, "numerical_tolerance": {}, "sensitivity": []}
    for name in MODELS:
        r = solve(graph[name], base, gas, thermo)
        r_fine = solve(graph[name], base, gas, thermo, n_steps=800)
        out["base"][name] = r
        out["numerical_tolerance"][name] = {"max_node_pressure_change_Pa_200_vs_800_steps": max(
            abs(r["node_pressures_MPa"][n] - r_fine["node_pressures_MPa"][n]) * 1e6 for n in r["node_pressures_MPa"])}
    sweeps = [("demand_scale", v) for v in (0.5, 1.0, 1.25, 1.5)] + [("T_ref_K", v) for v in (283.15, 313.15)] + \
             [("roughness_m", v) for v in (2e-5, 4.5e-5, 1e-4)] + [("discharge_MPa", v) for v in (4.0, 6.5, 8.0)] + \
             [("supply_MPa", v) for v in (3.0, 4.0)]
    for key, val in sweeps:
        prm = copy.deepcopy(base)
        if key == "demand_scale":
            prm["demand"] = {k: v * val for k, v in base["demand"].items()}
        elif key == "discharge_MPa":
            prm["discharge_MPa"] = {"C1": val, "C2": val}
        else:
            prm[key] = val
        for name in MODELS:
            try:
                r = solve(graph[name], prm, gas, thermo)
                c = r["checks"]
                c1 = next((x for x in r["compressors"] if x["compressor"] == "C1"), {})
                c2 = next((x for x in r["compressors"] if x["compressor"] == "C2"), {})
                out["sensitivity"].append({"parameter": key, "value": val, "model": name, "feasible": c["feasible"],
                                           "min_pipe_pressure_MPa": c["min_pipe_pressure_MPa"], "max_outlet_velocity_m_s": c["max_outlet_velocity_m_s"],
                                           "max_velocity_pipe": c["max_velocity_pipe"], "C1_power_isentropic_kW": c1.get("power_isentropic_kW"),
                                           "C1_T_discharge_isentropic_K": c1.get("T_discharge_isentropic_K"), "C2_dp_MPa": c2.get("dp_MPa"),
                                           "trunk_dp_kPa": sum(e["dp_kPa"] for e in r["pipes"] if e["sid"] in ("47", "48"))})
            except ValueError as e:
                out["sensitivity"].append({"parameter": key, "value": val, "model": name, "feasible": False, "error": str(e)[:120]})
    return out


def main(argv) -> int:
    doc = build()
    text = json.dumps(doc, indent=1) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("provisional steady states: " + ("current" if ok else "STALE"))
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for name, r in doc["base"].items():
        c = r["checks"]
        print(f"{name}: feasible={c['feasible']} sinks={c['sinks_found']} supply={c['supply_flow_kg_s']:.2f} kg/s "
              f"resid={c['mass_conservation_max_residual_kg_s']:.1e} p=[{c['min_pipe_pressure_MPa']:.4f},{c['max_pipe_pressure_MPa']:.4f}] MPa "
              f"vmax={c['max_outlet_velocity_m_s']:.2f} m/s ({c['max_velocity_pipe']}) tol={doc['numerical_tolerance'][name]['max_node_pressure_change_Pa_200_vs_800_steps']:.2e} Pa")
        for k in r["compressors"]:
            print(f"   {k['compressor']}: {k['p_suction_MPa']:.3f}->{k['p_discharge_MPa']:.3f} MPa, {k['mdot_kg_s']:.1f} kg/s, T2s={k['T_discharge_isentropic_K']:.1f} K, "
                  f"P_s={k['power_isentropic_kW']:.0f} kW, T2(eta0.75)={k['T_discharge_eta0.75_K']:.1f} K, cooler(0.75)={k['aftercooler_duty_eta0.75_kW']:.0f} kW")
        if r["letdown"]:
            print(f"   let-down: {r['letdown']['p_in_MPa']:.3f}->{r['letdown']['p_out_MPa']:.3f} MPa, T_out={r['letdown']['T_out_isenthalpic_K']:.2f} K")
    print("sensitivity (center):")
    for s in doc["sensitivity"]:
        if s["model"].endswith("center"):
            print("  ", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items() if k not in ("model",)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
