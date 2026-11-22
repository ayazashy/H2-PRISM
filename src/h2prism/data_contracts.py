"""
Data, topology and sensor contracts (Master Execution Directive; issues on provenance / sensor identity / grouped
splits via actions X21 and X12 preparation). RESEARCH MODULE: schemas and validators only. Nothing here reads raw data,
and nothing here approves a dataset (dataset authority: Yazan).

Contracts (schema version DATA_CONTRACT_VERSION)
  NetworkRecord   network_id, nodes, directed edges (pipe ids), source model id, gas composition record
  SensorRecord    sensor_id (stable physical identity, never a column position), network_id, location (node or edge),
                  quantity, unit (whitelist), sampling period, availability
  RunRecord       run_id, network_id, independence_group, label + onset, composition, ancestry (parent run ids, e.g.
                  shared pre-event prefix or noise variant), provenance (generator + hash), data_quality_status
Validators
  validate_network / validate_sensors / validate_run    structural checks, return a list of violations ([] = valid)
  missing_is_not_zero(values, available)                 a value at an unavailable sample must be NaN, never 0
  check_partition_integrity(runs, partition)             an independence group (and every ancestry chain) lies in
                                                         ONE partition; returns violations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

DATA_CONTRACT_VERSION = "data_contract/0.1"
UNITS = {"pressure": {"Pa", "kPa", "MPa", "bar"}, "mass_flow": {"kg/s", "g/s"}, "temperature": {"K"},
         "volumetric_flow": {"m3/s"}, "composition": {"mol/mol"}}
DATA_QUALITY = ("UNCHECKED", "PASS", "PASS_WITH_WARNINGS", "FAIL")
LABEL_ONSET_REQUIRED = {"LEAK", "FAULT", "DELAY"}


@dataclass(frozen=True)
class NetworkRecord:
    network_id: str
    nodes: Tuple[str, ...]
    edges: Tuple[Tuple[str, str, str], ...]          # (edge_id, from_node, to_node)
    source_model: str
    composition: Mapping[str, object]
    version: str = DATA_CONTRACT_VERSION


@dataclass(frozen=True)
class SensorRecord:
    sensor_id: str
    network_id: str
    location_kind: str                               # "node" | "edge"
    location_id: str
    quantity: str
    unit: str
    sampling_period_s: float
    availability: str = "AVAILABLE"                  # AVAILABLE | INTERMITTENT | UNAVAILABLE


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    network_id: str
    independence_group: str
    label: str
    label_onset_s: Optional[float]
    composition: Mapping[str, object]
    provenance: Mapping[str, str]                    # e.g. {"generator": ..., "generator_sha256": ..., "file_sha256": ...}
    ancestry: Tuple[str, ...] = ()
    data_quality_status: str = "UNCHECKED"
    version: str = DATA_CONTRACT_VERSION


def validate_network(n: NetworkRecord) -> List[str]:
    v = []
    if n.version != DATA_CONTRACT_VERSION:
        v.append(f"{n.network_id}: contract version {n.version}")
    if len(set(n.nodes)) != len(n.nodes):
        v.append(f"{n.network_id}: duplicate node ids")
    ids = [e[0] for e in n.edges]
    if len(set(ids)) != len(ids):
        v.append(f"{n.network_id}: duplicate edge ids")
    for eid, a, b in n.edges:
        if a not in n.nodes or b not in n.nodes:
            v.append(f"{n.network_id}: edge {eid} references an unknown node")
    if not n.composition:
        v.append(f"{n.network_id}: composition missing")
    return v


def validate_sensors(sensors: Sequence[SensorRecord], networks: Mapping[str, NetworkRecord]) -> List[str]:
    v, seen = [], set()
    for s in sensors:
        key = (s.network_id, s.sensor_id)
        if key in seen:
            v.append(f"{s.sensor_id}: duplicate sensor id in {s.network_id}")
        seen.add(key)
        net = networks.get(s.network_id)
        if net is None:
            v.append(f"{s.sensor_id}: unknown network {s.network_id}")
            continue
        where = net.nodes if s.location_kind == "node" else [e[0] for e in net.edges] if s.location_kind == "edge" else ()
        if s.location_id not in where:
            v.append(f"{s.sensor_id}: location {s.location_kind}:{s.location_id} not in network {s.network_id}")
        if s.unit not in UNITS.get(s.quantity, set()):
            v.append(f"{s.sensor_id}: unit {s.unit!r} not allowed for {s.quantity!r}")
        if not (np.isfinite(s.sampling_period_s) and s.sampling_period_s > 0):
            v.append(f"{s.sensor_id}: sampling period must be positive")
        if s.availability not in ("AVAILABLE", "INTERMITTENT", "UNAVAILABLE"):
            v.append(f"{s.sensor_id}: availability {s.availability!r}")
    return v


def validate_run(r: RunRecord, networks: Mapping[str, NetworkRecord]) -> List[str]:
    v = []
    if r.network_id not in networks:
        v.append(f"{r.run_id}: unknown network {r.network_id}")
    if not r.independence_group:
        v.append(f"{r.run_id}: independence group missing")
    if r.label in LABEL_ONSET_REQUIRED and (r.label_onset_s is None or not np.isfinite(r.label_onset_s)):
        v.append(f"{r.run_id}: {r.label} requires a finite label onset")
    if r.label == "NORMAL" and r.label_onset_s is not None:
        v.append(f"{r.run_id}: NORMAL has no onset")
    if not r.composition:
        v.append(f"{r.run_id}: composition missing")
    for k in ("generator", "file_sha256"):
        if not r.provenance.get(k):
            v.append(f"{r.run_id}: provenance.{k} missing")
    if r.data_quality_status not in DATA_QUALITY:
        v.append(f"{r.run_id}: data_quality_status {r.data_quality_status!r}")
    if r.run_id in r.ancestry:
        v.append(f"{r.run_id}: run lists itself as ancestor")
    return v


def missing_is_not_zero(values, available) -> List[int]:
    """Indices where a sample marked unavailable carries a number instead of NaN (e.g. a fill with 0)."""
    x, a = np.asarray(values, float), np.asarray(available, bool)
    if x.shape != a.shape:
        raise ValueError("values and availability mask must have the same shape")
    return [int(i) for i in np.flatnonzero(~a & ~np.isnan(x))]


def check_partition_integrity(runs: Iterable[RunRecord], partition: Mapping[str, str]) -> List[str]:
    """partition: run_id -> partition name (e.g. TRAIN / CALIBRATION / TEST). A group, or a run and any ancestor,
    split across partitions is a leakage violation; unassigned runs are reported."""
    runs = list(runs)
    v, by_group = [], {}
    for r in runs:
        if r.run_id not in partition:
            v.append(f"{r.run_id}: not assigned to a partition")
            continue
        by_group.setdefault(r.independence_group, set()).add(partition[r.run_id])
        for a in r.ancestry:
            if a in partition and partition[a] != partition[r.run_id]:
                v.append(f"{r.run_id}: ancestor {a} is in {partition[a]}, run is in {partition[r.run_id]}")
    for g, parts in sorted(by_group.items()):
        if len(parts) > 1:
            v.append(f"group {g} spans partitions {sorted(parts)}")
    # shared ancestry that is not itself a run (e.g. a deterministic initial state "IS:<hash>", a shared load-profile
    # realization or warm-up prefix): every run listing the same ancestor must lie in one partition
    by_anc = {}
    for r in runs:
        if r.run_id in partition:
            for a in r.ancestry:
                if a not in partition:
                    by_anc.setdefault(a, set()).add(partition[r.run_id])
    for a, parts in sorted(by_anc.items()):
        if len(parts) > 1:
            v.append(f"shared ancestor {a} spans partitions {sorted(parts)}")
    return v
