#!/usr/bin/env python3
"""
Candidate sensor position map v0.1 (D2) from the diagram trace only.

Input: 03_results/diagnostics/sensor_correspondence/SENSOR_CORRESPONDENCE.csv (tools/dataset/trace_slx_sensors.py).
Canonical channel = the name the center and up models log for that sensor block (they agree for every shared block).
Only blocks logged by all three source models are mapped; blocks logged by one or two models are listed as excluded.
Writes 06_audit_preparation/protocol2/CANDIDATE_SENSOR_POSITION_MAP_V01.csv and ..._EXCLUDED.csv, plus a .sha256.
Status: CANDIDATE, NOT APPROVED (requires the dataset owner's D2 acceptance).
Usage: python tools/dataset/build_position_map.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CORR = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "SENSOR_CORRESPONDENCE.csv"
OUT = REPO / "06_audit_preparation" / "protocol2"
TOPO = {"center": "Center", "down": "Downstream", "up": "Upstream"}


def main() -> int:
    c = pd.read_csv(CORR)
    c = c[c.logged.astype(bool)].copy()
    c["sensor_block_sid"] = c.sensor_block_sid.astype(int)
    rows, excl = [], []
    for sid, g in c.groupby("sensor_block_sid"):
        names = dict(zip(g.model, g.sensor_id))
        if set(names) != set(TOPO):
            excl.append({"sensor_block_sid": sid, "logged_as": ";".join(f"{TOPO[m]}:{n}" for m, n in sorted(names.items())),
                         "reason": "block not logged by every source model"})
            continue
        if names["center"] != names["up"]:
            raise SystemExit(f"center and up name block {sid} differently; canonical naming undefined")
        same_node = g.physical_node_adjacent_components.nunique() == 1
        for m, n in sorted(names.items()):
            rows.append({"canonical_channel": names["center"], "canonical_block_sid": sid, "topology": TOPO[m],
                         "source_channel": n, "renamed": n != names["center"],
                         "node_status": "SAME_NODE" if same_node else "SAME_BLOCK_DIFFERENT_JUNCTION",
                         "verification_status": g.verification_status.iloc[0]})
    order = lambda s: s.str.replace(r"(\d+)", lambda x: x.group(1).zfill(3), regex=True)  # noqa: E731
    M = pd.DataFrame(rows).sort_values(["canonical_channel", "topology"], key=lambda s: order(s) if s.name == "canonical_channel" else s)
    p = OUT / "CANDIDATE_SENSOR_POSITION_MAP_V01.csv"
    M.to_csv(p, index=False, lineterminator="\n")
    pd.DataFrame(excl).to_csv(OUT / "CANDIDATE_SENSOR_POSITION_MAP_V01_EXCLUDED.csv", index=False, lineterminator="\n")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT / "CANDIDATE_SENSOR_POSITION_MAP_V01.sha256").write_text(f"{h}  {p.name}\n", encoding="utf-8")
    print(M.to_string(index=False))
    print(pd.DataFrame(excl).to_string(index=False))
    print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
