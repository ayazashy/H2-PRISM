#!/usr/bin/env python3
"""
H2Net v1 BUILD SPECIFICATION (action X05 preparation). Machine-readable list of every change that turns a COPY of a
released normal model into an H2Net v1 model, derived from:
  candidate/RELEASED_NETWORK_GRAPH.json        (released SIDs, nets, parameters; hash-checked extraction)
  candidate/PARAMETER_DECISIONS_PROPOSED.yaml  (PROPOSED values; owner decisions pending)
  candidate/PROVISIONAL_STEADY_STATES.json     (provisional initial state)
  tools/matlab/h2prism_matlab_expectations.json (sensor ids / SIDs)
Library paths are those of the installed R2026b fl_lib (library browser: Gas/Sources, Gas/Elements, Thermal/...).

Two kinds of operation:
  parameter_ops   set_param on an EXISTING block, addressed by SID -> implemented in tools/matlab/h2prism_build_h2net_v1.m
  structural_ops  add/replace blocks and connections                -> SPECIFIED ONLY; implemented and verified in the
                                                                        first authorized MATLAB session (needs the GUI /
                                                                        port-handle checks that cannot be verified here)
Status of every value: PROPOSED (not owner-approved). Output: candidate/H2NET_V1_BUILD_SPEC.json (--check: stale -> 1)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CAND = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "candidate"
OUT = CAND / "H2NET_V1_BUILD_SPEC.json"
POS = {"Normal_HNetwork_gest_center": "center", "Normal_HNetwork_gest_up": "up", "Normal_HNetwork_gest_down": "down"}
LIB = {"flow_source": "fl_lib/Gas/Sources/Flow Rate Source (G)",
       "reservoir": "fl_lib/Gas/Elements/Reservoir (G)",
       "pipe": "fl_lib/Gas/Elements/Pipe (G)",
       "restriction": "fl_lib/Gas/Elements/Local Restriction (G)",
       "temperature_source": "fl_lib/Thermal/Thermal Sources/Temperature Source",
       "thermal_reference": "fl_lib/Thermal/Thermal Elements/Thermal Reference"}
LIB_NOTE = ("Library block names may contain a line break (e.g. 'Local Restriction\\n(G)' in the library browser); "
            "resolve with find_system('fl_lib', 'LookUnderMasks','all', 'Name', ...) before add_block.")
DEMAND_SID = {"213": "G3", "222": "G4", "312": "G5", "215": "G6"}
LEAK_PIPES = ["47", "48", "49", "309", "106", "221"]          # six mid-pipe leak positions (one per transmission pipe)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build() -> dict:
    graph = json.loads((CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    P = yaml.safe_load((CAND / "PARAMETER_DECISIONS_PROPOSED.yaml").read_text(encoding="utf-8"))
    ss = json.loads((CAND / "PROVISIONAL_STEADY_STATES.json").read_text(encoding="utf-8"))["base"]
    E = json.loads((REPO / "tools/matlab/h2prism_matlab_expectations.json").read_text(encoding="utf-8"))
    rough = P["S6_roughness_and_initial_state"]["proposal"]["roughness_m"]
    s3 = P["S3_compressor_stations"]["proposal"]
    demand = P["S4_demand_and_leaks"]["proposal"]["nominal_demand_kg_s"]
    T_ref = P["operating_envelope_V8"]["proposal"]["isothermal_reference_temperature_K"]
    models = {}
    for name, pos in POS.items():
        g = graph[name]
        comps = {c["sid"]: c for c in g["components"]}
        pipes = [c for c in g["components"] if c["class"] == "pipe"]
        pipe_nets = {n for c in pipes for n in c["nets"]}
        p_node = ss[name]["node_pressures_MPa"]
        pops = [{"sid": "4", "block": "Gas Properties (G)", "op": "apply_h2_tables",
                 "detail": "h2prism_apply_h2_gas_to_copy: gas_spec = real_gas (3) + the 15 fields of H2_REALGAS_TLU2_params.m"}]
        for c in pipes:
            pops.append({"sid": c["sid"], "block": c["name"], "op": "set_param", "params": {"roughness": str(rough), "roughness_unit": "m"},
                         "released": {"roughness": c["params"].get("roughness")}})
            p0 = p_node.get(c["nets"][0])
            if p0 is not None:
                pops.append({"sid": c["sid"], "block": c["name"], "op": "set_param",
                             "params": {"p_init": f"{p0:.6f}", "p_init_unit": "MPa", "T_init": f"{T_ref}", "T_init_unit": "K"},
                             "released": {"p_init": c["params"].get("p_init"), "T_init": c["params"].get("T_init")},
                             "note": "provisional steady-state initial condition (P13); recompute from X06 targets"})
        for sid, setp in (("55", s3["C1_discharge_setpoint_MPa"]), ("239", s3["C2_discharge_setpoint_MPa"])):
            pops.append({"sid": sid, "block": comps[sid]["name"], "op": "keep", "params": {"power_spec": "isentropic (1)"},
                         "note": f"discharge set-point {setp} MPa is applied through its control signal (released: step SID 59 / ramp SID 241)"})
        sops = []
        for c in g["components"]:
            if c["class"] == "local_restriction" and c["sid"] in DEMAND_SID:
                node = next(n for n in c["nets"] if n in pipe_nets)
                sops.append({"op": "replace_demand_orifice", "sid": c["sid"], "outlet": DEMAND_SID[c["sid"]], "network_net": node,
                             "new_blocks": [{"lib": LIB["flow_source"], "params": {"flow_type": "mass", "source_type": "controlled", "power_spec": "none (0)"},
                                             "port_A": node, "port_B": "new atmospheric Reservoir (G)"},
                                            {"lib": LIB["reservoir"], "params": {"pressure_spec": "atmospheric"}}],
                             "signal": f"demand profile {DEMAND_SID[c['sid']]} (nominal {demand[DEMAND_SID[c['sid']]]} kg/s) via Simulink-PS Converter",
                             "keep_sensor": "existing Flow Rate Sensor (G) on this branch stays in series (MFS ids unchanged)"})
            if c["class"] == "reservoir" and c["nets"][0] in pipe_nets:
                sops.append({"op": "replace_end_vent", "sid": c["sid"], "outlet": "END", "network_net": c["nets"][0],
                             "new_blocks": [{"lib": LIB["flow_source"], "params": {"flow_type": "mass", "source_type": "controlled", "power_spec": "none (0)"}},
                                            {"lib": LIB["reservoir"], "params": {"pressure_spec": "atmospheric"}}],
                             "signal": f"demand profile END (nominal {demand['END']} kg/s)"})
        for sid in ("55", "239"):
            c = comps[sid]
            sops.append({"op": "insert_aftercooler", "after_sid": sid, "between_nets": [c["nets"][1], "new net"],
                         "new_blocks": [{"lib": LIB["pipe"], "params": {"Dh": "same as downstream pipe", "length": "to be sized in V3 (outlet T within 0.5 K of set-point)"}},
                                        {"lib": LIB["temperature_source"], "params": {"T": f"{T_ref} K"}},
                                        {"lib": LIB["thermal_reference"]}],
                         "check": "V3: outlet temperature and duty vs PROVISIONAL_STEADY_STATES compressor records"})
        for sid in LEAK_PIPES:
            if sid in comps:
                c = comps[sid]
                sops.append({"op": "insert_leak_branch", "pipe_sid": sid, "pipe": c["name"],
                             "position": "split the pipe at 50 % length into two Pipe (G) blocks (lengths L/2, length_add split equally)",
                             "new_blocks": [{"lib": LIB["restriction"], "params": {"restriction_type": "variable", "Cd": "0.64"}},
                                            {"lib": LIB["reservoir"], "params": {"pressure_spec": "atmospheric"}}],
                             "signal": "leak area AR from the scenario (0 when no leak); severity definition A or B (owner)",
                             "label": f"LEAK@{c['name']}@0.5L; never on a demand block"})
        if name.endswith("down"):
            sops.append({"op": "replace_letdown", "sid": "111", "status": "DEFERRED (P15)",
                         "provisional": "pressure reduction to 4.0 MPa; isenthalpic outlet temperature 314.0 K in provisional steady states"})
        sens = next(m for m in E["models"] if m["name"] == name)["sensors"]
        net_of = {c["sid"]: c["nets"] for c in g["components"]}
        sensor_map = []
        for s in sens:
            nets = net_of.get(s["sid"], [])
            sensor_map.append({"sensor_id": s["sensor_id"], "sid": s["sid"], "variable": s["variable"], "nets": nets,
                               "steady_pressure_MPa": p_node.get(nets[0]) if nets else None})
        chamber = [c for c in g["components"] if c["class"] == "constant_volume_chamber"]
        models[name] = {"position": pos, "target_file": f"h2net_v1_{pos}.slx", "source_sha256": next(m for m in E["models"] if m["name"] == name)["sha256"],
                        "parameter_ops": pops, "structural_ops": sops, "sensor_map": sensor_map,
                        "findings": [f"Constant Volume Chamber (G) SID {c['sid']} behind Flow Rate Sensor (G)1 (MFS2) has ONE gas port (num_ports = one; "
                                     f"its other connection, net {c['nets'][1]}, is thermal port H on a Perfect Insulator) -> dead-end volume: MFS2 "
                                     "measures only chamber filling (0 kg/s in steady state)" for c in chamber]}
    return {"status": "SPECIFICATION_PROPOSED (values not owner-approved; structural ops not implemented)",
            "library": LIB, "library_note": LIB_NOTE,
            "provenance": {k: _sha(CAND / k) for k in ("RELEASED_NETWORK_GRAPH.json", "PARAMETER_DECISIONS_PROPOSED.yaml", "PROVISIONAL_STEADY_STATES.json")},
            "models": models}


def main(argv) -> int:
    text = json.dumps(build(), indent=1) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("build spec: " + ("current" if ok else "STALE"))
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    d = json.loads(text)
    for n, m in d["models"].items():
        print(n, len(m["parameter_ops"]), "parameter ops,", len(m["structural_ops"]), "structural ops,", len(m["sensor_map"]), "sensors;", m["findings"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
