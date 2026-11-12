"""
Scenario independence units (forensic FA-03; candidate protocol 2.0 component P2-C).

Protocol 1.1 counts *topology-scoped families* (Scenario_Family_ID) as independent support. The same simulated
scenario is replicated in each topology (CS_<TOPOLOGY>_<stem>), so two families can share one scenario ancestor.
An *independence group* is the connected component of runs linked by EITHER relation:
  * same Scenario_Family_ID (related runs within a topology, e.g. weak/strong variants of one fault), or
  * same scenario stem across topologies (replicas of one simulated scenario).
This module only DEFINES the unit; protocol 1.1 behaviour is unchanged unless a config opts in.
"""

from __future__ import annotations

from typing import Dict, Iterable

import pandas as pd


def ancestor(scenario_id: str) -> str:
    """Scenario stem without the topology token: CS_<TOPOLOGY>_<stem> -> <stem> (SYN_ for synthetic test fixtures)."""
    parts = str(scenario_id).split("_")
    if len(parts) < 3 or parts[0] not in ("CS", "SYN"):
        raise ValueError(f"unexpected Scenario_ID format: {scenario_id!r}")
    return "_".join(parts[2:])


def independence_groups(scenario_ids: Iterable[str], families: Iterable[str]) -> Dict[str, str]:
    """Map every Scenario_ID to its independence group (deterministic id = smallest stem in the component)."""
    sid = pd.Series(list(scenario_ids), dtype=str)
    fam = pd.Series(list(families), dtype=str)
    if len(sid) != len(fam):
        raise ValueError("scenario_ids and families differ in length")
    pairs = pd.DataFrame({"sid": sid, "fam": fam}).drop_duplicates()
    if pairs.sid.duplicated().any():
        raise ValueError("a Scenario_ID maps to more than one family")
    parent: Dict[str, str] = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    for r in pairs.itertuples():
        union(f"S:{r.sid}", f"F:{r.fam}")
        union(f"S:{r.sid}", f"A:{ancestor(r.sid)}")
    comp: Dict[str, list] = {}
    for r in pairs.itertuples():
        comp.setdefault(find(f"S:{r.sid}"), []).append(ancestor(r.sid))
    label = {root: "IG_" + min(stems) for root, stems in comp.items()}
    return {r.sid: label[find(f"S:{r.sid}")] for r in pairs.itertuples()}
