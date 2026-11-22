"""Preflight for an independently measured, controlled NORMAL/LEAK study."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

from .certified_evidence import Record
from .data_contracts import NetworkRecord, SensorRecord, validate_network, validate_sensors
from .experimental_data import ExperimentManifest, IngestedExperiment, PhysicsApproval, check_splits, ingest_csv

FATAL = {
    "raw_observations": "Original timestamped pressure and signed mass flow with verified integrity",
    "rights": "Documented research reuse and permission for planned reporting",
    "ancestry": "Whole-run identifiers and confirmed independent acquisition ancestry",
    "event_truth": "Independent event logs, including onset and verified region for LEAK",
    "processing_lineage": "Trace from acquisition through the exact ingested bytes",
}
RECOVERABLE = {
    "gas_and_operating_conditions": "Measured records or independently reviewed applicable ranges",
    "geometry_and_sensor_locations": "Original engineering records or independently surveyed geometry",
    "calibration_and_measurement_error": "Instrument records or independent calibration and justified bounds",
    "leak_mechanism_and_opening": "Traceable device records or independently characterized opening bounds",
}
PHYSICS = (
    "fluid_properties", "pressure_flow_equations", "leak_discharge", "operating_dynamics",
    "measurement_uncertainty", "model_discrepancy",
)


@dataclass(frozen=True)
class EvidenceReference(Record):
    name: str
    reference: str
    basis: str  # ORIGINAL, INDEPENDENTLY_RECOVERED, INDEPENDENTLY_BOUNDED


@dataclass(frozen=True)
class RigMapping(Record):
    approval: PhysicsApproval
    model_network: NetworkRecord
    model_sensors: tuple[SensorRecord, ...]
    nodes: tuple[tuple[str, str], ...]   # rig -> model
    edges: tuple[tuple[str, str], ...]
    sensors: tuple[tuple[str, str], ...]
    physics: tuple[EvidenceReference, ...]
    model_sha256: str


@dataclass(frozen=True)
class Intake:
    run: IngestedExperiment | None
    reasons: tuple[str, ...]
    configuration_sha256: str | None
    rig_sha256: str | None = None


@dataclass(frozen=True)
class Protocol(Record):
    version: str = "independent-hydrogen-normal-leak/1"
    ontology: tuple[str, ...] = ("NORMAL", "LEAK")
    evaluation_unit: str = "one whole, independently acquired family"
    split_rule: str = "Separate model-validation and held-out families. Development only for fitting."
    calibration_rule: str = "Freeze model, settings, bounds, and splits before inspecting held-out outcomes."
    uncertainty_rule: str = "Keep deterministic instrument, clock, boundary, parameter, discrepancy, and numerical bounds separate."
    comparator: str = "Conventional joint set membership on identical model, data, uncertainty and solver settings."
    policy: str = "Same joint evidence with validity gates and indeterminate handling. No accuracy advantage assumed."
    localization: str = "Require specific LEAK evidence and verified region truth for scoring. L2 needs all rival regions excluded."
    primary_metrics: tuple[str, ...] = ("specific decisions / eligible families", "incorrect specific decisions / specific decisions")
    secondary_metrics: tuple[str, ...] = ("false exclusions", "candidate inclusion", "ambiguity and abstention",
                                          "true-region inclusion", "unique-region coverage", "certificate replay", "runtime")
    statistics: str = ("Report paired method differences over the same families. If adequacy supports inference, "
                       "resample whole families jointly for paired bootstrap intervals. Pin confidence level, "
                       "replicates, seed, adequacy rule and handling of zero denominators before held-out reveal.")
    undefined: str = "Report null for unavailable metrics and for selective risk with no specific decisions."


def evidence_issues(records, required, allowed):
    indexed = {entry.name: entry for entry in records}
    issues = []
    if len(indexed) != len(records):
        issues.append("DUPLICATE_EVIDENCE")
    for key in required:
        entry = indexed.get(key)
        if entry is None or not entry.reference.strip() or entry.basis not in allowed[key]:
            issues.append(f"{key}:MISSING_OR_UNSUPPORTED_EVIDENCE")
    return issues


def acquisition_issues(records):
    allowed = {key: {"ORIGINAL", "INDEPENDENTLY_RECOVERED"} for key in (*FATAL, *RECOVERABLE)}
    for key in ("gas_and_operating_conditions", "calibration_and_measurement_error", "leak_mechanism_and_opening"):
        allowed[key].add("INDEPENDENTLY_BOUNDED")
    return evidence_issues(records, (*FATAL, *RECOVERABLE), allowed)


def _bijection(pairs, source, target):
    mapping = dict(pairs)
    if len(mapping) != len(pairs) or mapping.keys() != set(source) or set(mapping.values()) != set(target):
        return None
    return mapping if len(mapping) == len(set(mapping.values())) else None


def compatibility_issues(manifest: ExperimentManifest, rig: RigMapping):
    issues = evidence_issues(rig.physics, PHYSICS, {
        name: {"ORIGINAL", "INDEPENDENTLY_RECOVERED", "INDEPENDENTLY_BOUNDED"} for name in PHYSICS
    })
    model = rig.model_network
    if (not re.fullmatch(r"[a-f0-9]{64}", rig.model_sha256) or not rig.approval.review_reference.strip() or
            rig.approval.network_id != manifest.network.network_id or
            validate_network(model) or validate_sensors(rig.model_sensors, {model.network_id: model})):
        issues.append("UNPINNED_OR_UNREVIEWED_MODEL")
    if model.composition != manifest.network.composition or rig.approval.gas != manifest.gas:
        issues.append("GAS_MISMATCH")
    nodes = _bijection(rig.nodes, manifest.network.nodes, model.nodes)
    instrumented = {item.sensor.sensor_id: item.sensor for item in manifest.sensors}
    model_sensors = {sensor.sensor_id: sensor for sensor in rig.model_sensors}
    sensors = _bijection(rig.sensors, instrumented, model_sensors)
    model_edges = {name: (origin, end) for name, origin, end in model.edges}
    edges = _bijection(rig.edges, (name for name, _, _ in manifest.network.edges), model_edges)
    if nodes is None or edges is None or any(
            (nodes.get(u), nodes.get(v)) != model_edges[edges[name]] for name, u, v in manifest.network.edges):
        issues.append("RIG_TOPOLOGY_OR_ORIENTATION_MISMATCH")
    if nodes is None or edges is None or sensors is None:
        issues.append("SENSOR_MAPPING_INCOMPLETE")
    else:
        for name, model_name in sensors.items():
            a, b = instrumented[name], model_sensors[model_name]
            location = (nodes if a.location_kind == "node" else edges).get(a.location_id)
            if (a.quantity, a.unit, a.location_kind, location) != (b.quantity, b.unit, b.location_kind, b.location_id):
                issues.append(f"{name}:SENSOR_LOCATION_OR_UNIT_MISMATCH")
    return issues


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def accept(path: Path, manifest: ExperimentManifest, records: tuple[EvidenceReference, ...],
           rig: RigMapping | None, model_path: Path | None = None) -> Intake:
    issues = acquisition_issues(records)
    physics = compatibility_issues(manifest, rig) if rig else ["RIG_MODEL_MAPPING_MISSING"]
    if rig:
        try:
            if model_path is None or hashlib.sha256(model_path.read_bytes()).hexdigest() != rig.model_sha256:
                physics.append("MODEL_ARTIFACT_CHECKSUM_UNVERIFIED")
        except OSError:
            physics.append("MODEL_ARTIFACT_CHECKSUM_UNVERIFIED")
    try:
        run = ingest_csv(path, manifest, rig.approval if rig and not physics else None)
    except (OSError, ValueError, ArithmeticError) as exc:
        return Intake(None, tuple(sorted(set(issues + physics + [f"INGESTION_REJECTED: {exc}"]))), None)
    issues += physics + list(run.eligibility.reasons)
    if manifest.event == "LEAK" and not run.eligibility.localization_eligible:
        issues.append("CONTROLLED_LEAK_REGION_NOT_VERIFIED")
    configuration = None if issues else _digest({
        "manifest": json.loads(manifest.to_json()), "rig": json.loads(rig.to_json()),
        "acquisition": [json.loads(entry.to_json()) for entry in sorted(records, key=lambda item: item.name)],
    })
    return Intake(run, tuple(sorted(set(issues))), configuration,
                  _digest(json.loads(rig.to_json())) if configuration else None)


def protocol_preflight(intakes: tuple[Intake, ...], partitions: dict[str, str],
                       locked_sha256: str | None = None, *, analysis_plan_sha256: str | None = None):
    protocol = Protocol()
    reasons = set()
    for item in intakes:
        reasons.update(item.reasons)
        if (item.run is None or not item.run.eligibility.diagnostic_eligible or
                not item.configuration_sha256 or not item.rig_sha256):
            reasons.add("UNQUALIFIED_INTAKE")
    runs = tuple(item.run for item in intakes if item.run is not None)
    if len({item.rig_sha256 for item in intakes if item.rig_sha256}) > 1:
        reasons.add("NONMATCHED_RIG_MODEL_CONFIGURATIONS")
    if not runs:
        reasons.add("NO_EXPERIMENTAL_RUNS")
    if set(partitions) != {run.manifest.run_id for run in runs}:
        reasons.add("PARTITION_MEMBERSHIP_MISMATCH")
    reasons.update(check_splits(runs, partitions))
    for split in ("MODEL_VALIDATION", "HELD_OUT"):
        events = {run.manifest.event for run in runs if partitions.get(run.manifest.run_id) == split}
        if not set(protocol.ontology) <= events:
            reasons.add(f"{split}:INSUFFICIENT_EVENT_SUPPORT")
    if not analysis_plan_sha256 or not re.fullmatch(r"[a-f0-9]{64}", analysis_plan_sha256):
        reasons.add("ANALYSIS_PLAN_NOT_PINNED")
    configuration = _digest({"protocol": json.loads(protocol.to_json()), "partitions": partitions,
                             "intakes": sorted(item.configuration_sha256 or "" for item in intakes),
                             "analysis_plan_sha256": analysis_plan_sha256})
    if locked_sha256 != configuration:
        reasons.add("PROTOCOL_NOT_LOCKED_OR_CHANGED")
    return {"status": "READY_FOR_APPROVED_EXECUTION" if not reasons else "BLOCKED",
            "configuration_sha256": configuration, "reasons": sorted(reasons), "independent_metrics": None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = {
        "schema": "validation-activation/1", "fatal_acquisition_requirements": FATAL,
        "independently_recoverable_requirements": RECOVERABLE, "required_physics_review": PHYSICS,
        "protocol": json.loads(Protocol().to_json()), "preflight": protocol_preflight((), {}),
    }
    with args.output.open("x", encoding="utf-8") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")


if __name__ == "__main__":
    main()
