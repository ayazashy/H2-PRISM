#!/usr/bin/env python3
"""
X06: V2 steady-state REFERENCE TARGETS for H2Net v1, computed BEFORE any simulation from the OWNER DECISION RECORD
06_audit_preparation/simulation/h2net_v1/PARAMETER_DECISIONS.yaml (never from proposals). Fail-closed gate:
  * status must be DECIDED, or DECIDED_WITH_DEFERRALS where every undecided section carries deferred: true
  * M1-M5 sections (S3, S4, S6, operating_envelope_V8) must be decided: true with a decided_by
  * required values (schema of H2NET_V1_APPROVAL_CHECKLIST.md section 3) must be present; S4.value.demand_levels is
    required (>= 5 operating points per topology, specification V2)
Physics: the independent solver of h2net_v1_provisional_network.py (gas_physics.py unchanged; hydrogen tables).
Usage: python tools/simulation/h2net_v1_v2_targets.py [--decisions PATH] [--out PATH]
       (also reached through h2net_v1_envelope_screening.py --targets). Exit 2 = refused, nothing written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_provisional_network as pn  # noqa: E402

H2 = pn.REPO / "06_audit_preparation" / "simulation" / "h2net_v1"
DEFAULT_OUT = H2 / "V2_TARGETS.json"
REQUIRED = ("S3_compressor_stations", "S4_demand_and_leaks", "S6_roughness_and_initial_state", "operating_envelope_V8")


class Refused(Exception):
    pass


def gate(dec: dict) -> None:
    st = dec.get("status")
    if st not in ("DECIDED", "DECIDED_WITH_DEFERRALS"):
        raise Refused(f"status is {st!r}")
    for k, v in dec.items():
        if isinstance(v, dict) and "decided" in v and not v["decided"]:
            if not (st == "DECIDED_WITH_DEFERRALS" and v.get("deferred") is True):
                raise Refused(f"{k} neither decided nor explicitly deferred")
    for k in REQUIRED:
        v = dec.get(k) or {}
        if v.get("decided") is not True or not v.get("decided_by") or str(v.get("decided_by")).startswith("<"):
            raise Refused(f"{k} must be decided with a named decided_by")


def params(dec: dict):
    s3, s4 = dec["S3_compressor_stations"]["value"], dec["S4_demand_and_leaks"]["value"]
    s6, v8 = dec["S6_roughness_and_initial_state"]["value"], dec["operating_envelope_V8"]["value"]
    levels = s4.get("demand_levels")
    if not isinstance(levels, list) or len(levels) < 5:
        raise Refused("S4.value.demand_levels must list >= 5 demand multipliers (V2: >= 5 operating points per topology)")
    ld = str(s3.get("down_model_letdown_sid_111", "DEFERRED"))
    m = re.search(r"([0-9.]+)\s*MPa", ld)
    base = {"supply_MPa": float(s3["supply_reservoir_pressure_MPa"]),
            "discharge_MPa": {"C1": float(s3["C1_pressure_source_sid_55"]["discharge_setpoint_MPa"]),
                              "C2": float(s3["C2_pressure_source_sid_239"]["discharge_setpoint_MPa"])},
            "letdown_MPa": float(m.group(1)) if m else None,
            "demand": {k: float(v) for k, v in s4["nominal_demand_kg_s"].items()},
            "T_ref_K": float(v8["isothermal_reference_temperature_K"]), "roughness_m": float(s6["roughness_m"]),
            "envelope_MPa": [float(x) for x in v8["normal"]["pressure_MPa"]],
            "v_limit": float(v8["normal"]["velocity_limit_m_s"]),
            "eta": [float(x) for x in s3.get("efficiency_for_power_reporting", [0.75, 0.85])]}
    return base, [float(x) for x in levels]


def compute(decisions: Path, out: Path) -> dict:
    dec = yaml.safe_load(Path(decisions).read_text(encoding="utf-8"))
    gate(dec)
    base, levels = params(dec)
    graphs = json.loads((pn.CAND / "RELEASED_NETWORK_GRAPH.json").read_text(encoding="utf-8"))["models"]
    gas, thermo = pn.load_h2_tables(), pn.Thermo()
    res = {"status": "V2_TARGETS (from the owner decision record; computed before simulation)",
           "decisions_sha256": hashlib.sha256(Path(decisions).read_bytes()).hexdigest(),
           "decided_by": {k: dec[k].get("decided_by") for k in REQUIRED},
           "acceptance": "specification V2: pressures within 0.5 % of the pressure drop, flows within 1 %",
           "provenance": {"h2_tables_sha256": hashlib.sha256(Path(pn.TABLES).read_bytes()).hexdigest(),
                          "gas_physics_sha256": hashlib.sha256((pn.REPO / "src/h2prism/gas_physics.py").read_bytes()).hexdigest(),
                          "network_graph_sha256": hashlib.sha256((pn.CAND / "RELEASED_NETWORK_GRAPH.json").read_bytes()).hexdigest()},
           "parameters": base, "targets": {}}
    for name in pn.MODELS:
        if name.endswith("down") and base["letdown_MPa"] is None:
            res["targets"][name] = "NOT_COMPUTED: down-model let-down deferred (P15)"
            continue
        pts = []
        for s in levels:
            p = json.loads(json.dumps(base))
            p["demand"] = {k: v * s for k, v in base["demand"].items()}
            r = pn.solve(graphs[name], p, gas, thermo, n_steps=800)
            pts.append({"demand_multiplier": s, "demand_kg_s": p["demand"], "checks": r["checks"], "node_pressures_MPa": r["node_pressures_MPa"],
                        "pipes": r["pipes"], "compressors": r["compressors"], "letdown": r["letdown"]})
        res["targets"][name] = pts
    out.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    return res


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--decisions", type=Path, default=H2 / "PARAMETER_DECISIONS.yaml")
    a.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = a.parse_args(argv)
    try:
        r = compute(args.decisions, args.out)
    except Refused as e:
        print(f"REFUSED: V2 reference targets need the owner decision record: {e}")
        return 2
    n = sum(len(v) for v in r["targets"].values() if isinstance(v, list))
    infeasible = [(m, p["demand_multiplier"]) for m, v in r["targets"].items() if isinstance(v, list) for p in v if not p["checks"]["feasible"]]
    print(f"{n} target operating points -> {args.out}; infeasible: {infeasible or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
