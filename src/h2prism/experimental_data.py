"""Checksum-bound ingestion and independent experimental eligibility checks."""
from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import re

import pandas as pd

from .certified_evidence import Channel, MeasurementContract, Record
from .data_contracts import NetworkRecord, RunRecord, SensorRecord, check_partition_integrity, validate_network, validate_sensors
from .phase5 import ErrorBound, EvidenceBasis, clock_index, physical_eligibility
from .physical_reference import EvidenceLedger, EvidenceCategory

SUPPORTED_UNITS = {"pressure": "Pa", "mass_flow": "kg/s", "temperature": "K"}


@dataclass(frozen=True)
class SensorInput(Record):
    sensor: SensorRecord
    column: str
    unit_reference: str
    calibration_reference: str
    error: ErrorBound | None
    reference_convention: str


@dataclass(frozen=True)
class ExperimentManifest(Record):
    dataset_id: str
    run_id: str
    family: str
    ancestry: tuple[str, ...]
    ancestry_reference: str
    tier: str
    source_reference: str
    license_reference: str
    use_authorization_reference: str
    sha256: str
    clock_column: str
    clock_reference: str
    network: NetworkRecord
    sensors: tuple[SensorInput, ...]
    gas: str
    temperature_k: float | None
    event: str | None
    onset_s: float | None
    location: str | None
    truth_reference: str
    evidence: EvidenceLedger
    uncertainty: tuple[ErrorBound, ...]


@dataclass(frozen=True)
class PhysicsApproval(Record):
    """Independent review for a pinned adapter and a specific experimental regime."""

    model_id: str
    network_id: str
    geometry_reference: str
    gas: str
    pressure_pa: tuple[float, float]
    temperature_k: tuple[float, float]
    events: tuple[str, ...]
    required_sensors: tuple[str, ...]
    regions: tuple[str, ...]
    review_reference: str


@dataclass(frozen=True)
class Eligibility(Record):
    dataset_id: str
    experiment_id: str
    independent_unit: str
    evidence_tier: str
    ground_truth_available: bool
    physics_compatible: bool
    uncertainty_available: bool
    sensors_compatible: bool
    diagnostic_eligible: bool
    localization_eligible: bool
    localization_exclusion_reason: str | None
    reasons: tuple[str, ...]
    source_reference: str
    source_sha256: str


@dataclass(frozen=True)
class IngestedExperiment:
    manifest: ExperimentManifest
    measurement: MeasurementContract
    eligibility: Eligibility
    trajectory_sha256: str
    missing_samples: tuple[tuple[str, tuple[int, ...]], ...]
    original_timestamps_s: tuple[str, ...]


def ingest_csv(path: Path, manifest: ExperimentManifest, approval: PhysicsApproval | None = None) -> IngestedExperiment:
    contents = path.read_bytes()
    actual = hashlib.sha256(contents).hexdigest()
    if not re.fullmatch(r"[a-f0-9]{64}", manifest.sha256) or actual != manifest.sha256:
        raise ValueError("experimental source checksum mismatch")
    header = next(csv.reader(io.StringIO(contents.decode("utf-8-sig"))), None)
    if not header or len(set(header)) != len(header):
        raise ValueError("invalid or duplicate source columns")
    frame = pd.read_csv(io.BytesIO(contents), dtype={manifest.clock_column: str})
    if manifest.clock_column not in frame or not manifest.sensors:
        raise ValueError("missing source clock or sensor mapping")
    original_timestamps = tuple(frame[manifest.clock_column])
    times = tuple(map(float, clock_index(original_timestamps)))
    reasons = set()
    if not manifest.license_reference.strip() or not manifest.use_authorization_reference.strip():
        reasons.add("DATA_USE_UNVERIFIED")
    if not all(x.strip() for x in (manifest.dataset_id, manifest.run_id, manifest.family,
                                   manifest.source_reference, manifest.ancestry_reference)) or not manifest.ancestry or any(not a.strip() or a == manifest.run_id for a in manifest.ancestry):
        reasons.add("RUN_ANCESTRY_UNVERIFIED")
    if manifest.tier != "T4":
        reasons.add("NOT_AN_INDEPENDENT_PHYSICAL_EXPERIMENT")
    sensors = tuple(item.sensor for item in manifest.sensors)
    if validate_network(manifest.network) or validate_sensors(sensors, {manifest.network.network_id: manifest.network}):
        reasons.add("INVALID_NETWORK_OR_SENSOR_MAPPING")
    if len({item.column for item in manifest.sensors}) != len(sensors) or any(
            item.column == manifest.clock_column for item in manifest.sensors):
        reasons.add("INVALID_NETWORK_OR_SENSOR_MAPPING")
    quantities = {sensor.quantity for sensor in sensors}
    if not {"pressure", "mass_flow"} <= quantities:
        reasons.add("MISSING_PRESSURE_OR_FLOW_SENSOR")

    orientations = {edge: f'{origin}->{destination}' for edge, origin, destination in manifest.network.edges}
    channels, missing = [], []
    for item in manifest.sensors:
        s = item.sensor
        if not item.unit_reference or SUPPORTED_UNITS.get(s.quantity) != s.unit:
            reasons.add("UNVERIFIED_OR_NON_SI_UNIT")
        if ((s.quantity == "pressure" and item.reference_convention != "absolute") or
                (s.quantity == "mass_flow" and item.reference_convention != orientations.get(s.location_id))):
            reasons.add("PRESSURE_OR_FLOW_REFERENCE_UNVERIFIED")
        if not item.calibration_reference.strip():
            reasons.add("CALIBRATION_MISSING")
        if item.column not in frame:
            reasons.add("MISSING_MAPPED_COLUMN")
            continue
        values = tuple(pd.to_numeric(frame[item.column], errors="raise").astype(float))
        gaps = tuple(i for i, value in enumerate(values) if not math.isfinite(value))
        missing.append((s.sensor_id, gaps))
        if gaps:
            reasons.add("MISSING_SENSOR_SAMPLES")
        error = item.error
        valid_error = (error is not None and error.name == s.sensor_id and error.unit == s.unit and
                       error.domain == manifest.network.network_id and bool(error.reference.strip()) and
                       isinstance(error.basis, EvidenceBasis) and error.basis in (EvidenceBasis.CALIBRATED, EvidenceBasis.MANUFACTURER, EvidenceBasis.MEASURED) and
                       error.interval is not None and all(map(math.isfinite, error.interval)) and
                       error.interval[0] <= 0 <= error.interval[1])
        errors = (max(map(abs, error.interval)),) * len(times) if valid_error else ()
        if not valid_error:
            reasons.add("INSTRUMENT_BOUND_MISSING_OR_INVALID")
        channels.append(Channel(s.sensor_id, s.unit, times, manifest.clock_reference, values, errors))
    if physical_eligibility(manifest.uncertainty, manifest.network.network_id):
        reasons.add("PHYSICAL_UNCERTAINTY_INCOMPLETE")
    ledger_ok = True
    for name in ("geometry", "operating_conditions", "initial_state", "boundary_inputs", "gas_composition"):
        try:
            item = manifest.evidence.require(name, "mixed")
            if (item.scope != manifest.network.network_id or item.domain != manifest.network.network_id or
                    item.category in (EvidenceCategory.ENGINEERING, EvidenceCategory.UNKNOWN)):
                ledger_ok = False
        except ValueError:
            ledger_ok = False
    if not ledger_ok:
        reasons.add("PHYSICS_METADATA_INCOMPLETE")
    truth = bool(manifest.truth_reference.strip()) and (
        (manifest.event == "NORMAL" and manifest.onset_s is None) or
        (manifest.event == "LEAK" and manifest.onset_s is not None and
         math.isfinite(manifest.onset_s) and times[0] <= manifest.onset_s <= times[-1]))
    if not truth:
        reasons.add("EVENT_GROUND_TRUTH_UNVERIFIED")
    measurement = MeasurementContract(sensors, times, tuple(channels), manifest.run_id, manifest.family,
                                      f"sha256:{actual}", "sensor-specific deterministic instrument bounds")
    qc = measurement.issues()
    reasons.update(qc)
    pressure_bounds = [(v-e, v+e) for c in channels if c.unit == "Pa"
                       for v, e in zip(c.values, c.absolute_errors)]
    temperature_bounds = [b.interval for b in manifest.uncertainty if b.name == "temperature"
                          and b.interval is not None and b.unit == "K"]
    temperature_error = (max(map(abs, temperature_bounds[0]))
                         if len(temperature_bounds) == 1 else math.inf)
    model_ok = bool(
        approval and approval.review_reference and approval.geometry_reference and approval.model_id and ledger_ok and
        all(math.isfinite(v) and v > 0 for v in (*approval.pressure_pa, *approval.temperature_k)) and
        approval.network_id == manifest.network.network_id and approval.gas and approval.gas == manifest.gas and
        approval.geometry_reference == manifest.evidence.require("geometry", "mixed").reference and
        manifest.event in approval.events and set(approval.required_sensors) <= {s.sensor_id for s in sensors} and
        manifest.temperature_k is not None and approval.temperature_k[0] <= manifest.temperature_k - temperature_error
        <= manifest.temperature_k + temperature_error <= approval.temperature_k[1]
        and pressure_bounds and all(approval.pressure_pa[0] <= lo <= hi <= approval.pressure_pa[1]
                                    for lo, hi in pressure_bounds) and
        all(approval.temperature_k[0] <= v-e <= v+e <= approval.temperature_k[1]
            for c in channels if c.unit == "K" for v, e in zip(c.values, c.absolute_errors)))
    if not model_ok:
        reasons.add("NO_MATCHED_PHYSICAL_APPROVAL")
    diagnostic = not reasons
    localization = bool(diagnostic and manifest.event == "LEAK" and manifest.location in approval.regions)
    # Detect a byte-independent copy of the same observed samples even if
    # dataset labels, units metadata, columns or clock origin are changed.
    trajectory = sorted(tuple(float(v).hex() for v in c.values) for c in channels)
    signature = hashlib.sha256(json.dumps(trajectory, separators=(",", ":")).encode()).hexdigest()
    return IngestedExperiment(
        manifest, measurement,
        Eligibility(manifest.dataset_id, manifest.run_id, manifest.family, manifest.tier, truth, model_ok,
                    not any("BOUND" in r or "UNCERTAINTY" in r for r in reasons),
                    not qc and not reasons.intersection({"INVALID_NETWORK_OR_SENSOR_MAPPING", "UNVERIFIED_OR_NON_SI_UNIT",
                                                        "MISSING_PRESSURE_OR_FLOW_SENSOR", "CALIBRATION_MISSING",
                                                        "PRESSURE_OR_FLOW_REFERENCE_UNVERIFIED"}),
                    diagnostic, localization,
                    None if localization else ("DIAGNOSIS_INELIGIBLE" if not diagnostic else
                                               "NO_QUALIFIED_LEAK_REGION_TRUTH"),
                    tuple(sorted(reasons)), manifest.source_reference, actual),
        signature, tuple(missing), original_timestamps,
    )


def check_splits(runs: tuple[IngestedExperiment, ...], partitions: dict[str, str]) -> tuple[str, ...]:
    """Validate one whole-run record per unit and forbid ancestry/trajectory leakage."""
    issues = set()
    seen_ids, signatures, held_out_units = set(), {}, {}
    records = []
    for experiment in runs:
        m = experiment.manifest
        if m.run_id in seen_ids:
            issues.add(f"{m.run_id}: repeated run or window")
        seen_ids.add(m.run_id)
        for token in (m.sha256, experiment.trajectory_sha256):
            if token in signatures and signatures[token] != m.run_id:
                issues.add(f"{m.run_id}: duplicate source or trajectory")
            signatures[token] = m.run_id
        split = partitions.get(m.run_id)
        if split not in {"DEVELOPMENT", "MODEL_VALIDATION", "HELD_OUT"}:
            issues.add(f"{m.run_id}: invalid or absent partition")
        if split == "HELD_OUT" and not experiment.eligibility.diagnostic_eligible:
            issues.add(f"{m.run_id}: ineligible held-out case")
        if split == "HELD_OUT":
            for token in (m.family, m.run_id, *m.ancestry):
                if token in held_out_units and held_out_units[token] != m.run_id:
                    issues.add(f"{m.run_id}: repeated held-out ancestry or unit")
                held_out_units[token] = m.run_id
        records.append(RunRecord(m.run_id, m.network.network_id, m.family, m.event or "UNKNOWN", m.onset_s,
                                 m.network.composition, {"generator": m.source_reference, "file_sha256": m.sha256},
                                 m.ancestry))
    issues.update(check_partition_integrity(records, partitions))
    return tuple(sorted(issues))
