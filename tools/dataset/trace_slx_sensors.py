#!/usr/bin/env python3
"""
D2: trace every logged sensor of the six MATLAB/Simscape source models to its physical position, from the .slx
diagram alone (blocks, physical connections, signal lines, Goto/From tags, parameters). No signal values are used.

For each model and each logged variable (pressure_sensorN / flow_sensorN):
  ToWorkspace (subsystem "Sensor Variable Workspace") <- Inport k <- root signal into that subsystem's port k
  <- From tag <- Goto tag <- PS-Simulink Converter <- sensor measurement port (physical connection)
  -> sensor gas port(s) -> physical net -> adjacent components (pipes, restrictions, sources, reservoirs, chambers).
Position is described by the adjacent components and by the shortest pipe-length path (km) to the nearest compressor
outlet (Pressure Source B port), without routing through a compressor.

SENSOR_CORRESPONDENCE.csv then compares each release column name (PS1..PS12, MFS1..MFS4) across the three models by
diagram identity (block SID, class, adjacent components). Signal values are never used.

Writes 03_results/diagnostics/sensor_correspondence/{SENSOR_TRACE.csv, NETWORK_EDGES.csv, MODEL_FILES.csv}.
Paths are recorded relative to the dataset root; the raw files are not copied.
Usage: python tools/dataset/trace_slx_sensors.py
"""

from __future__ import annotations

import hashlib
import heapq
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
SIM = REPO / "data" / "raw" / "H2-SimNet-Dataset" / "MATLAB_SIMSCAPE_Simulation"
OUT = REPO / "03_results" / "diagnostics" / "sensor_correspondence"
MODELS = {
    ("anomalous", "center"): "anomalous_scenarios/Anomalous_HNetwork_gest_center.slx",
    ("anomalous", "down"): "anomalous_scenarios/Anomalous_HNetwork_gest_down.slx",
    ("anomalous", "up"): "anomalous_scenarios/Anomalous_HNetwork_gest_up.slx",
    ("normal", "center"): "normality_scenarios/normality_datasets/Normal_HNetwork_gest_center.slx",
    ("normal", "down"): "normality_scenarios/normality_datasets/Normal_HNetwork_gest_down.slx",
    ("normal", "up"): "normality_scenarios/normality_datasets/Normal_HNetwork_gest_up.slx",
}
KEY_PARAMS = ("length", "area", "Dh", "restriction_area", "restriction_type", "pressure_differential", "source_type",
              "reservoir_pressure", "pressure_spec", "volume", "area_A")


def _p(el, name):
    for e in el.findall("P"):
        if e.get("Name") == name:
            return e.text or ""
    return ""


def _clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def _endpoints(line):
    """All endpoints of a line, including nested branches."""
    pts = []
    s = _p(line, "Src")
    if s:
        pts.append(s)
    d = _p(line, "Dst")
    if d:
        pts.append(d)
    for br in line.findall("Branch"):
        pts += _endpoints(br)
    return pts


def _dsts(line):
    out = []
    d = _p(line, "Dst")
    if d:
        out.append(d)
    for br in line.findall("Branch"):
        out += _dsts(br)
    return out


class Model:
    def __init__(self, path: Path):
        self.z = zipfile.ZipFile(path)
        self.root = ET.fromstring(self.z.read("simulink/systems/system_root.xml"))
        self.blocks = {}
        for b in self.root.findall("Block"):
            inst = b.find("InstanceData")
            params = {e.get("Name"): (e.text or "") for e in inst.findall("P")} if inst is not None else {}
            self.blocks[b.get("SID")] = {
                "sid": b.get("SID"), "type": b.get("BlockType"), "name": _clean(b.get("Name")),
                "cls": params.get("ClassName", "") or _clean(_p(b, "SourceType")) or b.get("BlockType"),
                "pos": _p(b, "Position"), "goto": _p(b, "GotoTag"), "params": params,
                "system": (b.find("System").get("Ref") if b.find("System") is not None else ""),
            }
        # physical nets (union-find over connection endpoints)
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        self.signal = []
        for ln in self.root.findall("Line"):
            if ln.get("LineType") == "Connection":
                pts = _endpoints(ln)
                for a in pts[1:]:
                    parent[find(a)] = find(pts[0])
                for a in pts:
                    find(a)
            else:
                self.signal.append((_p(ln, "Src"), _dsts(ln)))
        self.net_of = {pt: find(pt) for pt in parent}
        self.net_members = defaultdict(list)
        for pt, n in self.net_of.items():
            self.net_members[n].append(pt)

    def ports_on_net(self, pt):
        n = self.net_of.get(pt)
        return [] if n is None else [q for q in self.net_members[n] if q != pt]

    def sig_src(self, dst):
        for s, ds in self.signal:
            if dst in ds:
                return s
        return None

    def sub(self, ref):
        return ET.fromstring(self.z.read(f"simulink/systems/{ref}.xml"))


def gas_ports(cls):
    """Physical gas ports per Simscape class (lconn/rconn order from InternalSimscapePortConfiguration)."""
    return {"pressure_temperature_sensor": ["lconn:1"], "flow_sensor": ["lconn:1", "rconn:1"],
            "pipe": ["lconn:1", "rconn:1"], "local_restriction": ["lconn:1", "rconn:1"],
            "pressure_source": ["lconn:1", "rconn:1"], "reservoir": ["lconn:1"], "controlled_reservoir": ["lconn:1"],
            "constant_volume_chamber": ["lconn:1", "lconn:2"], "flow_rate_source": ["lconn:1", "rconn:1"],
            "mass_flow_rate_source": ["lconn:1", "rconn:1"]}.get(cls, [])


def describe(m: Model, sid):
    b = m.blocks[sid]
    kp = ";".join(f"{k}={b['params'][k]}{(' ' + b['params'].get(k + '_unit', '')) if b['params'].get(k + '_unit') not in (None, '', '1') else ''}"
                  for k in KEY_PARAMS if k in b["params"])
    return f"{b['name']} [{b['cls']}; SID {sid}{('; ' + kp) if kp else ''}]"


def network(m: Model):
    """Edges between physical nets through two-port components, weighted by pipe length (km); others weight 0."""
    edges = []
    for sid, b in m.blocks.items():
        gp = gas_ports(b["cls"])
        if len(gp) == 2 and "sensor" not in b["cls"] and b["cls"] != "pressure_source":  # never route through a compressor
            a, c = (m.net_of.get(f"{sid}#{p}") for p in gp)
            if a and c:
                w = float(b["params"].get("length", 0) or 0) / 1000.0 if b["cls"] == "pipe" else 0.0
                edges.append((a, c, w, sid))
        if b["cls"] == "flow_sensor":  # an in-line sensor joins its two nets with zero length
            a, c = (m.net_of.get(f"{sid}#{p}") for p in gas_ports(b["cls"]))
            if a and c:
                edges.append((a, c, 0.0, sid))
    return edges


def distances(edges, start):
    g = defaultdict(list)
    for a, c, w, _ in edges:
        g[a].append((c, w))
        g[c].append((a, w))
    dist = {start: 0.0}
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18):
            continue
        for v, w in g[u]:
            if d + w < dist.get(v, 1e18):
                dist[v] = d + w
                heapq.heappush(pq, (d + w, v))
    return dist


def trace(kind, topo, rel):
    path = SIM / rel
    m = Model(path)
    ws = next(b for b in m.blocks.values() if b["type"] == "SubSystem" and "Workspace" in b["name"])
    sub = m.sub(ws["system"])
    sblocks = {b.get("SID"): b for b in sub.findall("Block")}
    sig = [(_p(ln, "Src"), _dsts(ln)) for ln in sub.findall("Line")]
    edges = network(m)
    comp = [sid for sid, b in m.blocks.items() if b["cls"] == "pressure_source"]
    starts = [m.net_of.get(f"{sid}#rconn:1") for sid in comp]
    dist = {}
    for s in starts:
        for k, v in distances(edges, s).items():
            dist[k] = min(v, dist.get(k, 1e18))
    rows = []
    for sid, b in sblocks.items():
        if b.get("BlockType") != "ToWorkspace":
            continue
        var = _p(b, "VariableName")
        src = next((s for s, ds in sig if f"{sid}#in:1" in ds), None)
        inport = sblocks[src.split("#")[0]]
        k = _p(inport, "Port") or "1"
        cur = m.sig_src(f"{ws['sid']}#in:{k}")
        chain = [f"Inport {_clean(inport.get('Name'))} (port {k})"]
        tag = ""
        if cur and m.blocks[cur.split("#")[0]]["type"] == "From":
            tag = m.blocks[cur.split("#")[0]]["goto"]
            goto = next(s for s, bb in m.blocks.items() if bb["type"] == "Goto" and bb["goto"] == tag)
            cur = m.sig_src(f"{goto}#in:1")
            chain.append(f"From/Goto tag {tag}")
        conv = cur.split("#")[0]
        chain.append(f"PS-Simulink Converter SID {conv}")
        unit = m.blocks[conv]["params"].get("Unit", "")
        meas = [q for q in m.ports_on_net(f"{conv}#lconn:1")]
        sens = meas[0].split("#")[0] if meas else None
        sb = m.blocks[sens]
        neigh, nets = [], []
        for gp in gas_ports(sb["cls"]):
            n = m.net_of.get(f"{sens}#{gp}")
            nets.append(n)
            for q in m.ports_on_net(f"{sens}#{gp}"):
                qs = q.split("#")[0]
                if qs != sens:
                    neigh.append(f"{gp}->{q.split('#')[1]} of {describe(m, qs)}")
        d = [dist.get(n) for n in nets if n in dist]
        rows.append({
            "scenario_kind": kind, "model": topo, "model_file": rel, "variable": var,
            "sensor_id": ("PS" if var.startswith("pressure") else "MFS") + re.sub(r"\D", "", var),
            "goto_tag": tag, "signal_chain": " <- ".join(chain), "converter_unit": unit or "inherit",
            "sensor_block": describe(m, sens), "sensor_sid": sens, "sensor_class": sb["cls"],
            "sensor_position_xy": sb["pos"],
            "quantity": "pressure (absolute)" if sb["cls"] == "pressure_temperature_sensor" else "mass flow rate",
            "adjacent_components": " | ".join(sorted(set(neigh))),
            "pipe_km_from_compressor_outlet": (min(d) if d else None),
        })
    E = pd.DataFrame([{"scenario_kind": kind, "model": topo, "net_a": a, "net_b": c, "km": w,
                       "component": describe(m, s)} for a, c, w, s in edges])
    return rows, E


def _neighbours(adj):
    """Adjacent physical components (gas ports only), excluding other sensors: the measurement node's identity."""
    keep = []
    for part in str(adj).split(" | "):
        m = re.search(r"of (.+?) \[(\w+); SID (\d+)", part)
        if m and "sensor" not in m.group(2) and m.group(2) not in ("gas_properties", "solver"):
            keep.append(f"{m.group(2)}:{m.group(3)}")
    return ",".join(sorted(set(keep)))


def correspond(A: pd.DataFrame, N: pd.DataFrame) -> pd.DataFrame:
    """One row per (release column, model): what it physically measures and whether it matches the same name elsewhere."""
    rows = []
    topos = ["center", "down", "up"]
    for sid_name in sorted(set(A.sensor_id), key=lambda x: (x[:2], int(re.sub(r"\D", "", x)))):
        sub = A[A.sensor_id == sid_name].set_index("model")
        sids = {t: sub.loc[t, "sensor_sid"] for t in topos if t in sub.index}
        neigh = {t: _neighbours(sub.loc[t, "adjacent_components"]) for t in sids}
        same_block = len(set(sids.values())) == 1 and len(sids) == 3
        same_node = same_block and len(set(neigh.values())) == 1
        cu_block = sids.get("center") is not None and sids.get("center") == sids.get("up")
        cu_node = cu_block and neigh.get("center") == neigh.get("up")
        if len(sids) < 3:
            verdict, comp = "DOWN_ONLY_SENSOR", "not comparable (absent in center/up; release pads a constant)"
        elif same_node:
            verdict, comp = "VERIFIED_SAME_BLOCK_SAME_NODE", "same measurement node in all three models; network operating context differs by design (withdrawal branch location)"
        elif same_block:
            verdict, comp = "SAME_BLOCK_DIFFERENT_JUNCTION", "same sensor block, but its node's adjacent components differ between models"
        elif cu_block:
            verdict, comp = "DIFFERENT_PHYSICAL_SENSOR_IN_DOWN", ("same node in center and up only" if cu_node else
                                                                 "same block in center and up, different junction") + "; the down model logs a different sensor block under this name"
        else:
            verdict, comp = "DIFFERENT_PHYSICAL_SENSOR", "different sensor blocks under this name"
        for t in topos:
            if t not in sids:
                rows.append({"sensor_id": sid_name, "model": t, "logged": False, "verdict": verdict, "comparability": comp})
                continue
            r = sub.loc[t]
            same_as = [f"{x}:{y}" for x in topos for y, z in A[A.model == x].set_index("sensor_id").sensor_sid.items()
                       if z == r.sensor_sid and x != t]
            nm = N[(N.model == t) & (N.sensor_id == sid_name)]
            normal_ok = (len(nm) == 1 and nm.iloc[0].sensor_sid == r.sensor_sid
                         and _neighbours(nm.iloc[0].adjacent_components) == neigh[t])
            rows.append({
                "sensor_id": sid_name, "model": t, "logged": True, "sensor_block_sid": r.sensor_sid,
                "sensor_block": r.sensor_block.split(" [")[0], "quantity": r.quantity,
                "units": "MPa (Simscape default; converter unit 'inherit')" if r.quantity.startswith("pressure")
                         else "kg/s (Simscape default; converter unit 'inherit')",
                "physical_node_adjacent_components": neigh[t],
                "pipe_km_to_nearest_compressor_outlet": r.pipe_km_from_compressor_outlet,
                "same_block_logged_elsewhere_as": ";".join(same_as),
                "normal_model_identical": normal_ok,
                "verdict": verdict, "comparability": comp,
                "evidence": f"{r.model_file}: ToWorkspace {r.variable} <- {r.signal_chain} <- sensor SID {r.sensor_sid}; "
                            "export scripts map pressure_sensorN->PSN, flow_sensorN->MFSN",
                "verification_status": ("VERIFIED_FROM_DIAGRAM" if normal_ok else "UNVERIFIED_NORMAL_MODEL_DIFFERS"),
            })
    return pd.DataFrame(rows)


def main() -> int:
    if not SIM.exists():
        print("source models not available locally", file=sys.stderr)
        return 1
    R, E, F = [], [], []
    for (kind, topo), rel in MODELS.items():
        r, e = trace(kind, topo, rel)
        R += r
        E.append(e)
        F.append({"scenario_kind": kind, "model": topo, "model_file": rel,
                  "sha256": hashlib.sha256((SIM / rel).read_bytes()).hexdigest()})
    OUT.mkdir(parents=True, exist_ok=True)
    T = pd.DataFrame(R).sort_values(["scenario_kind", "sensor_id", "model"],
                                    key=lambda s: s.str.replace(r"(\d+)", lambda x: x.group(1).zfill(3), regex=True)
                                    if s.dtype == object else s)
    T.to_csv(OUT / "SENSOR_TRACE.csv", index=False, lineterminator="\n")
    pd.concat(E).to_csv(OUT / "NETWORK_EDGES.csv", index=False, lineterminator="\n")
    pd.DataFrame(F).to_csv(OUT / "MODEL_FILES.csv", index=False, lineterminator="\n")
    C = correspond(T[T.scenario_kind == "anomalous"], T[T.scenario_kind == "normal"])
    C.to_csv(OUT / "SENSOR_CORRESPONDENCE.csv", index=False, lineterminator="\n")
    pd.set_option("display.width", 300, "display.max_colwidth", 200)
    print(T[["scenario_kind", "model", "sensor_id", "sensor_sid", "pipe_km_from_compressor_outlet", "adjacent_components"]]
          .to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
