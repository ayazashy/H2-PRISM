#!/usr/bin/env python3
"""
Read-only extraction of the gas networks of the six released Simscape models directly from the .slx files
(zip + XML; no MATLAB, no model load, files never written). Uses the parser of tools/dataset/trace_slx_sensors.py.

Output (H2Net v1 engineering evidence for X03 / S2-S6; not a decision):
  06_audit_preparation/simulation/h2net_v1/candidate/RELEASED_NETWORK_GRAPH.json
      per model: file SHA-256 (must match the pinned value), gas components with their physical nets and the
      parameters that matter for S1-S6 (geometry, roughness, length_add, inertia, restriction areas, Cd, compressor
      power_spec, reservoirs), plus the Gas Properties (G) specification
  06_audit_preparation/simulation/h2net_v1/candidate/RELEASED_PIPES.csv     one row per model x pipe
Usage: python tools/simulation/extract_released_network.py [--check]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "dataset"))
import trace_slx_sensors as t  # noqa: E402

OUT = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "candidate"
EXPECT = REPO / "tools" / "matlab" / "h2prism_matlab_expectations.json"
KEEP = ("length", "area", "Dh", "roughness", "length_add", "Re_lam", "Re_tur", "inertia", "dynamic_compressibility",
        "Nu_lam", "restriction_area", "restriction_type", "Cd", "pressure_differential", "source_type", "power_spec",
        "reservoir_pressure", "pressure_spec", "reservoir_temperature", "volume", "area_A", "p_init", "T_init")
GAS_KEEP = ("gas_spec", "R", "Z", "T_ref", "h_ref", "cp_ref", "mu_ref", "k_ref", "p_min_perfect", "p_max_perfect")
TO_SI = {"m": 1.0, "mm": 1e-3, "km": 1e3}


def _val(params, k):
    v, u = params.get(k), params.get(k + "_unit", "")
    return None if v is None else (v + (" " + u if u not in ("", "1") else ""))


def model_graph(rel: str, sha_expected: str) -> dict:
    path = REPO / rel
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != sha_expected:
        raise SystemExit(f"{rel}: hash {sha} differs from the pinned value")
    m = t.Model(path)
    nets = {}

    def nid(pt):
        n = m.net_of.get(pt)
        return None if n is None else nets.setdefault(n, f"N{len(nets) + 1}")
    comps, gas = [], {}
    for sid, b in sorted(m.blocks.items(), key=lambda kv: int(kv[0])):
        if b["cls"] == "gas_properties":
            gas = {k: _val(b["params"], k) for k in GAS_KEEP if k in b["params"]}
            continue
        gp = t.gas_ports(b["cls"])
        if not gp:
            continue
        comps.append({"sid": sid, "class": b["cls"], "name": b["name"], "nets": [nid(f"{sid}#{p}") for p in gp],
                      "params": {k: _val(b["params"], k) for k in KEEP if k in b["params"]}})
    return {"file": rel, "sha256": sha, "gas_properties": gas, "components": comps}


def _len_m(s):
    if s is None:
        return None
    v, u = (s.split() + ["m"])[:2]
    return float(v) * TO_SI[u]


def build():
    E = json.loads(EXPECT.read_text(encoding="utf-8"))
    graphs = {m["name"]: model_graph(m["file"], m["sha256"]) for m in E["models"]}
    rows = []
    for name, g in graphs.items():
        for c in g["components"]:
            if c["class"] == "pipe":
                p = c["params"]
                rows.append({"model": name, "sid": c["sid"], "name": c["name"], "net_a": c["nets"][0], "net_b": c["nets"][1],
                             "length_m": _len_m(p.get("length")), "Dh_m": _len_m(p.get("Dh")),
                             "roughness_m": _len_m(p.get("roughness")), "length_add_m": _len_m(p.get("length_add")),
                             "inertia": p.get("inertia"), "dynamic_compressibility": p.get("dynamic_compressibility")})
    doc = {"schema": "released_network_graph/0.1", "source": "read-only XML parse of the released .slx files",
           "models": graphs}
    return doc, rows


def main(argv) -> int:
    doc, rows = build()
    text = json.dumps(doc, indent=1) + "\n"
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    gj, pc = OUT / "RELEASED_NETWORK_GRAPH.json", OUT / "RELEASED_PIPES.csv"
    if "--check" in argv:
        ok = gj.exists() and gj.read_text(encoding="utf-8") == text and pc.read_text(encoding="utf-8") == buf.getvalue()
        print("released network extraction: " + ("current" if ok else "STALE"))
        return 0 if ok else 1
    gj.write_text(text, encoding="utf-8", newline="\n")
    pc.write_text(buf.getvalue(), encoding="utf-8", newline="\n")
    print(f"{len(doc['models'])} models, {len(rows)} pipe rows -> {gj.relative_to(REPO).as_posix()}, {pc.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
