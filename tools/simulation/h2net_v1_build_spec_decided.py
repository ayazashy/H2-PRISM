#!/usr/bin/env python3
"""
H2Net v1 build specification FROM THE OWNER DECISION RECORD (status SPECIFICATION_DECIDED). Consumed by
tools/matlab/h2prism_build_h2net_v1.m. Requires gate 'build' minus the build itself (decisions + V2 targets of THIS record).
Every operation is concrete: released SID, port (A = LConn1 side, B = RConn1 side, from the .slx XML), new block library
path, parameters and logging variable. Output: h2net_v1_run/build/H2NET_V1_BUILD_SPEC_DECIDED.json
Usage: python tools/simulation/h2net_v1_build_spec_decided.py [--decisions P] [--run DIR]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_gates as gates  # noqa: E402
import h2net_v1_v2_targets as v2t  # noqa: E402

CAND = gates.H2 / "candidate"
LIB = {"flow_source": "fl_lib/Gas/Sources/Flow Rate Source (G)", "reservoir": "fl_lib/Gas/Elements/Reservoir (G)",
       "pipe": "fl_lib/Gas/Elements/Pipe (G)", "restriction": "fl_lib/Gas/Elements/Local Restriction (G)",
       "flow_sensor": "fl_lib/Gas/Sensors/Flow Rate Sensor (G)", "pt_sensor": "fl_lib/Gas/Sensors/Pressure & Temperature Sensor (G)",
       "temperature_source": "fl_lib/Thermal/Thermal Sources/Temperature Source", "thermal_reference": "fl_lib/Thermal/Thermal Elements/Thermal Reference"}
POS = {"Normal_HNetwork_gest_center": "center", "Normal_HNetwork_gest_up": "up", "Normal_HNetwork_gest_down": "down"}
DEMAND = {"213": "G3", "222": "G4", "312": "G5", "215": "G6"}
NEW_METER = {"222": "MFS5", "215": "MFS6"}


def port_of(comp: dict, net: str) -> str:
    return "A" if comp["nets"][0] == net else "B"


def build(dec: dict, targets: dict, decisions_sha: str) -> dict:
    graph = json.loads((CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    E = json.loads((gates.REPO / "tools/matlab/h2prism_matlab_expectations.json").read_text(encoding="utf-8"))
    base, levels = v2t.params(dec)
    s3, s4 = dec["S3_compressor_stations"]["value"], dec["S4_demand_and_leaks"]["value"]
    cooler_L = s3.get("aftercoolers", {}).get("cooler_pipe_length_m")
    if not isinstance(cooler_L, (int, float)):
        raise v2t.Refused("S3.value.aftercoolers.cooler_pipe_length_m must be a number (V3 sizing)")
    leaks = s4["leaks"]
    models = {}
    for name, pos in POS.items():
        g = graph[name]
        comps = {c["sid"]: c for c in g["components"]}
        pipe_nets = {n for c in g["components"] if c["class"] == "pipe" for n in c["nets"]}
        tg = targets["targets"].get(name)
        if not isinstance(tg, list):
            models[name] = {"status": f"NOT_BUILT: {tg}"}
            continue
        nominal = min(tg, key=lambda p: abs(p["demand_multiplier"] - 1.0))
        node_p = nominal["node_pressures_MPa"]
        dp = {c["compressor"]: c["dp_MPa"] for c in nominal["compressors"]}
        ops = [{"id": "gas", "op": "apply_h2_tables", "sid": "4"}]
        for c in g["components"]:
            if c["class"] == "pipe":
                ops.append({"id": f"pipe{c['sid']}", "op": "set_params", "sid": c["sid"],
                            "params": {"roughness": str(base["roughness_m"]), "roughness_unit": "m",
                                       "p_init": f"{node_p[c['nets'][0]]:.6f}", "p_init_unit": "MPa",
                                       "T_init": str(base["T_ref_K"]), "T_init_unit": "K"}})
        for sid, key in (("55", "C1"), ("239", "C2")):
            ops.append({"id": f"comp_{key}", "op": "drive_pressure_source", "sid": sid, "variable": f"h2_dp_{key}", "nominal_dp_MPa": dp[key]})
            ops.append({"id": f"cooler_{key}", "op": "insert_series", "target_sid": sid, "target_port": "B", "orientation": "from_target",
                        "block": LIB["pipe"], "name": f"Aftercooler_{key}", "params": {"length": str(cooler_L), "length_unit": "m",
                        "Dh": "1.2", "Dh_unit": "m", "area": "1.1304", "area_unit": "m^2", "roughness": str(base["roughness_m"]), "roughness_unit": "m"},
                        "thermal": {"temperature_source": LIB["temperature_source"], "thermal_reference": LIB["thermal_reference"],
                                    "temperature_K": str(s3["aftercoolers"]["outlet_temperature_K"])}})
        ops.append({"id": "MFS0", "op": "insert_series", "target_sid": "47", "target_port": "A", "orientation": "to_target",
                    "block": LIB["flow_sensor"], "name": "MFS0", "log": {"variable": "flow_sensor_MFS0", "unit": "kg/s"}})
        ops.append({"id": "MFS2s", "op": "insert_series", "target_sid": "106", "target_port": "A", "orientation": "to_target",
                    "block": LIB["flow_sensor"], "name": "MFS2s", "log": {"variable": "flow_sensor_MFS2s", "unit": "kg/s"}})
        for c in g["components"]:
            if c["class"] == "local_restriction" and c["sid"] in DEMAND:
                net = next(n for n in c["nets"] if n in pipe_nets)
                ops.append({"id": f"sink_{DEMAND[c['sid']]}", "op": "replace_two_port", "sid": c["sid"], "network_port": port_of(c, net),
                            "block": LIB["flow_source"], "name": f"Demand_{DEMAND[c['sid']]}",
                            "params": {"flow_type": "foundation.enum.mass_volumetric_flow.mass", "source_type": "foundation.enum.constant_controlled.controlled",
                                       "power_spec": "foundation.enum.power_spec.none"}, "variable": f"h2_demand_{DEMAND[c['sid']]}"})
                if c["sid"] in NEW_METER:
                    ops.append({"id": NEW_METER[c["sid"]], "op": "insert_series", "target_sid": f"new:sink_{DEMAND[c['sid']]}", "target_port": "B",
                                "orientation": "from_target", "block": LIB["flow_sensor"], "name": NEW_METER[c["sid"]],
                                "log": {"variable": f"flow_sensor_{NEW_METER[c['sid']]}", "unit": "kg/s"}})
            if c["class"] == "reservoir" and c["nets"][0] in pipe_nets:
                up = next(p for p in g["components"] if p["class"] == "pipe" and c["nets"][0] in p["nets"])
                ops.append({"id": "sink_END", "op": "insert_series", "target_sid": c["sid"], "target_port": "A", "orientation": "to_target",
                            "block": LIB["flow_source"], "name": "Demand_END", "upstream_pipe_sid": up["sid"],
                            "params": {"flow_type": "foundation.enum.mass_volumetric_flow.mass", "source_type": "foundation.enum.constant_controlled.controlled",
                                       "power_spec": "foundation.enum.power_spec.none"}, "variable": "h2_demand_END"})
                if pos != "down":
                    ops.append({"id": "MFS7", "op": "insert_series", "target_sid": c["sid"], "target_port": "A", "orientation": "to_target",
                                "block": LIB["flow_sensor"], "name": "MFS7", "log": {"variable": "flow_sensor_MFS7", "unit": "kg/s"}})
                    ops.append({"id": "PS_END", "op": "add_pt_sensor", "at_sid": up["sid"], "at_port": "B", "block": LIB["pt_sensor"],
                                "name": "PS_END", "log": {"variable": "pressure_sensor_PS_END", "unit": "MPa"}})
        if pos in ("center", "down"):
            ops.append({"id": "PS_N6", "op": "add_pt_sensor", "at_sid": "49", "at_port": "B", "block": LIB["pt_sensor"], "name": "PS_N6",
                        "log": {"variable": "pressure_sensor_PS_N6", "unit": "MPa"}})
        for sid in [str(s) for s in leaks["pipes"]]:
            if sid in comps:
                ops.append({"id": f"leak_{sid}", "op": "split_pipe_with_leak", "sid": sid, "fraction": float(leaks["position_fraction"]),
                            "block": LIB["restriction"], "reservoir": LIB["reservoir"], "name": f"Leak_{sid}",
                            "params": {"restriction_type": "foundation.enum.restriction_type.variable", "Cd": str(leaks["Cd"]),
                                       "min_area": "1e-10", "min_area_unit": "m^2", "max_area": "0.01", "max_area_unit": "m^2"},
                            "variable": f"h2_leak_area_{sid}"})
        for key in ("C1", "C2"):
            ops.append({"id": f"T_{key}_out", "op": "add_pt_sensor", "at_sid": f"new:cooler_{key}", "at_port": "B", "block": LIB["pt_sensor"],
                        "name": f"T_{key}_out", "log": {"variable": f"temperature_sensor_{key}_out", "unit": "K", "port_index": 2}})
        total = sum(base["demand"].values())
        from h2prism.gas_physics import PerfectGas, orifice_mass_flow
        gas = v2t.pn.load_h2_tables()
        for o in ops:
            if o["op"] == "split_pipe_with_leak":
                pipe = comps[o["sid"]]
                p_up = node_p[pipe["nets"][0]] * 1e6
                pr = gas.props(p_up, base["T_ref_K"])
                pg = PerfectGas(R=gas.R, Z=pr["Z"], cp=pr["cp"], mu=pr["mu"], k=pr["k"])
                flux = orifice_mass_flow(p_up, 101325.0, base["T_ref_K"], 1.0, pg, float(leaks["Cd"]))
                o["v4_area_m2_for_2pct"] = 0.02 * total / flux
                o["v4_expected_leak_kg_s_nozzle"] = 0.02 * total
        smap = {}
        for s in next(m for m in E["models"] if m["name"] == name)["sensors"]:
            c = comps.get(s["sid"])
            if s["sid"] == "210":
                smap[s["variable"]] = {"kind": "chamber"}
            elif s["variable"].startswith("pressure"):
                smap[s["variable"]] = {"kind": "pressure", "net": c["nets"][0]}
            else:
                pipe_side = next((n for n in c["nets"] if n in pipe_nets), None)
                outlet = next((DEMAND[r["sid"]] for r in g["components"] if r["sid"] in DEMAND and set(r["nets"]) & set(c["nets"])), None)
                smap[s["variable"]] = {"kind": "demand", "outlet": outlet} if outlet else {"kind": "flow_at_net", "net": pipe_side or c["nets"][0]}
        smap.update({"flow_sensor_MFS0": {"kind": "flow", "pipe_sid": "47"}, "flow_sensor_MFS2s": {"kind": "flow", "pipe_sid": "106"},
                     "flow_sensor_MFS5": {"kind": "demand", "outlet": "G4"}, "flow_sensor_MFS6": {"kind": "demand", "outlet": "G6"}})
        if pos != "down":
            smap.update({"flow_sensor_MFS7": {"kind": "demand", "outlet": "END"},
                         "pressure_sensor_PS_END": {"kind": "pressure", "net": next(c["nets"][1] for c in g["components"] if c["sid"] == "107")}})
        if pos in ("center", "down"):
            smap["pressure_sensor_PS_N6"] = {"kind": "pressure", "net": comps["49"]["nets"][1]}
        models[name] = {"position": pos, "target_name": f"h2net_v1_{pos}", "sensor_map": smap, "source_sha256": next(m for m in E["models"] if m["name"] == name)["sha256"],
                        "operations": ops, "expected_log_variables": sorted({o["log"]["variable"] for o in ops if "log" in o}
                                                                            | {s["variable"] for s in next(m for m in E["models"] if m["name"] == name)["sensors"]}),
                        "nominal_target": {"demand_multiplier": nominal["demand_multiplier"], "node_pressures_MPa": node_p}}
    return {"status": "SPECIFICATION_DECIDED", "decisions_sha256": decisions_sha, "library": LIB,
            "verification": "UNVERIFIED in MATLAB until h2prism_build_h2net_v1 completes and V2 passes", "models": models}


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--decisions", type=Path, default=gates.DECISIONS)
    a.add_argument("--run", type=Path, default=gates.RUN)
    args = a.parse_args(argv)
    try:
        dec = yaml.safe_load(args.decisions.read_text(encoding="utf-8"))
        v2t.gate(dec)
        tp = args.run / "targets" / "V2_TARGETS.json"
        if not tp.exists():
            raise v2t.Refused(f"{tp} missing: run h2net_v1_v2_targets.py --out {tp}")
        targets = json.loads(tp.read_text(encoding="utf-8"))
        if targets.get("decisions_sha256") != gates.sha(args.decisions):
            raise v2t.Refused("V2 targets were computed from a different decision record")
        spec = build(dec, targets, gates.sha(args.decisions))
    except v2t.Refused as e:
        print(f"REFUSED: {e}")
        return 2
    out = args.run / "build" / "H2NET_V1_BUILD_SPEC_DECIDED.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{out}: " + ", ".join(f"{m.get('position', k)}={len(m.get('operations', []))} ops" for k, m in spec["models"].items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
