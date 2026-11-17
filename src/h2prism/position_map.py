"""
Diagram-derived sensor position map (CANDIDATE protocol 2.0, D2; not approved).

The release column names (PS1..PS12, MFS1..MFS4) are export-variable numbers, not positions: the down source model
logs different sensor blocks under PS5..PS10 than the center and up models (03_results/diagnostics/
sensor_correspondence/SENSOR_CORRESPONDENCE.csv). A position map assigns, per source-model topology, which release
column carries each canonical physical sensor (one canonical name per Simscape sensor block present in all three
models). It is derived from the .slx diagrams only; signal values never choose it.

apply_position_map() rebuilds the canonical feature columns row by row from the row's own topology's source column.
It fails closed: unknown topology, a canonical channel missing for any topology, a missing source column, a
duplicate assignment, or a hash mismatch raise PositionMapError. Nothing is imputed.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

REQUIRED = ("canonical_channel", "topology", "source_channel")


class PositionMapError(ValueError):
    pass


def load_position_map(path: Path, sha256: str | None = None) -> pd.DataFrame:
    path = Path(path)
    if sha256 is not None:
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != sha256:
            raise PositionMapError(f"position map hash mismatch: {got} != pinned {sha256}")
    m = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in m.columns]
    if missing:
        raise PositionMapError(f"position map lacks columns {missing}")
    if m.duplicated(["canonical_channel", "topology"]).any():
        raise PositionMapError("a canonical channel is assigned twice for one topology")
    if m.duplicated(["topology", "source_channel"]).any():
        raise PositionMapError("one release column is assigned to two canonical channels in one topology")
    return m


def canonical_channels(pmap: pd.DataFrame) -> List[str]:
    return list(dict.fromkeys(pmap.canonical_channel))


def apply_position_map(ft: pd.DataFrame, pmap: pd.DataFrame, statistics: Sequence[str],
                       topology_col: str = "topology") -> pd.DataFrame:
    """Return ft with canonical columns `<canonical>__<stat>` read from each row's topology-specific source column;
    all original sensor feature columns are dropped (so no unmapped channel can enter a model)."""
    topos = sorted(set(pmap.topology))
    unknown = sorted(set(ft[topology_col]) - set(topos))
    if unknown:
        raise PositionMapError(f"rows with topologies absent from the position map: {unknown}")
    canon = canonical_channels(pmap)
    for c in canon:
        have = set(pmap.loc[pmap.canonical_channel == c, "topology"])
        if have != set(topos):
            raise PositionMapError(f"canonical channel {c} is not mapped for topologies {sorted(set(topos) - have)}")
    lut: Dict[tuple, str] = {(r.canonical_channel, r.topology): r.source_channel for r in pmap.itertuples()}
    out = ft[[c for c in ft.columns if "__" not in c]].copy()
    t = ft[topology_col].to_numpy()
    for c in canon:
        for s in statistics:
            v = np.full(len(ft), np.nan)
            for topo in topos:
                src = f"{lut[(c, topo)]}__{s}"
                if src not in ft.columns:
                    raise PositionMapError(f"source column {src} missing for topology {topo}")
                m = t == topo
                v[m] = ft.loc[m, src].to_numpy(float)
            out[f"{c}__{s}"] = v
    return out
