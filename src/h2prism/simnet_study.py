"""H₂-SimNet archive qualification and physical-study entry points."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, replace
import hashlib
import json
import re
from pathlib import Path
import subprocess
from time import perf_counter

import numpy as np
import pandas as pd

from .certified_evidence import Channel, DiagnosticDecision, DecisionStatus, HypothesisModel, MeasurementContract, Record, diagnose
from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT, load_scenario
from .network_reference import Localization, localize
from .phase2 import DATA_HASH, checked_file, source_case
from .phase2_evaluation import EvaluationCase, summarize
from .phase3 import write_record
from .phase5 import ErrorBound, EvidenceBasis, physical_eligibility
from .phase6 import source_uncertainty
from .physical_reference import EvidenceCategory, EvidenceLedger

CATALOG_DIR = WORKSPACE_ROOT / "06_audit_preparation/protocol2"
CATALOG = "CANDIDATE_MANIFEST_V03.csv"
FOLDS = "CANDIDATE_OUTER_FOLDS_V03.csv"
ONTOLOGY = ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY")
CLASS_COLUMNS = dict(zip(ONTOLOGY[1:], ("Leak", "CompressorFault", "CompressorDelay")))
REGION_COLUMNS = ("leak_G3", "leak_G4", "leak_G5", "leak_G6")
GROUP_COLUMNS = ("Scenario_Family_ID", "family_extended_sensitivity",
                 "family_conservative_sensitivity", "independence_group")
SOURCE_REQUIREMENTS = {
    "runtime": "Authorized toolbox checkout and a checksum-bound, effective Center NORMAL run",
    "lineage": "Verified run/export identity and reconciliation to each admitted release trajectory",
    "gas": "Effective composition, gas block configuration, pressure reference and operating domain",
    "observations": "Resolved sensor mapping and units, signed flow, boundary and storage histories",
    "labels": "Approved event onset/offset and topology attribution bound to runtime, not filenames",
    "model": "Source-matched, verified adapter with deterministic instrument, state, model and numerical bounds",
    "normal_and_leak": "Matched NORMAL and signed leak mechanism, location, opening and timing",
    "compressor_and_delay": "Effective actuator commands, control law, response and fault intervention definitions",
    "localization": "Verified disjoint region ontology and exact attribution to physical topology",
    "evaluation": "Approved split disjoint by scenario, family, cross-topology group and duplicated source",
    "comparisons": "Freeze one observation definition, matched joint solver and predeclared robustness arms",
}


def catalog_tables():
    expected = json.loads((CATALOG_DIR / "CANDIDATE_MANIFEST_V03_CHECKS.json").read_text(encoding="utf-8"))
    return tuple(pd.read_csv(checked_file(CATALOG_DIR / name, expected["outputs"][name]),
                             dtype=str, keep_default_na=False) for name in (CATALOG, FOLDS))


def separation_issues(manifest, partitions: dict[str, str]):
    """Check known dependence across partitions. Window count never enters this check."""
    issues = []
    if not manifest.Scenario_ID.is_unique:
        return ["DUPLICATE_SCENARIO_ID"]
    selected = manifest[manifest.Scenario_ID.isin(partitions)].copy()
    if len(selected) != len(partitions):
        issues.append("UNKNOWN_SCENARIO")
    selected["partition"] = selected.Scenario_ID.map(partitions)
    for column in GROUP_COLUMNS:
        if (selected[column] == "").any():
            issues.append(f"{column}:MISSING")
        collisions = selected.groupby(column).partition.nunique()
        count = int((collisions > 1).sum())
        if count:
            issues.append(f"{column}:CROSS_PARTITION:{count}")
    hashes = selected.melt(id_vars="partition", value_vars=["sha256_clean", "sha256_noise_added"])
    if (hashes.value == "").any():
        issues.append("SOURCE_DIGEST:MISSING")
    duplicated = int((hashes.groupby("value").partition.nunique() > 1).sum())
    if duplicated:
        issues.append(f"SOURCE_DIGEST:CROSS_PARTITION:{duplicated}")
    return issues


def annotation(frame, record):
    """Verify archived binary annotations; does not attest physical ground truth."""
    columns = ["label_anomaly", *CLASS_COLUMNS.values(), *REGION_COLUMNS]
    if frame.index.name != "Timestamp" or not len(frame):
        return None, ("MISSING_STORED_CLOCK",)
    clock = frame.index.to_numpy(dtype=float)
    if not np.isfinite(clock).all() or not np.all(np.diff(clock) == 1):
        return None, ("INVALID_ARCHIVED_ONE_SECOND_GRID",)
    if not set(columns) <= set(frame) or not frame[columns].isin([0, 1]).to_numpy().all():
        return None, ("MISSING_OR_INVALID_BINARY_LABEL",)
    mask = frame[list(CLASS_COLUMNS.values())].astype(bool)
    locations = frame[list(REGION_COLUMNS)].astype(bool)
    anomaly = frame.label_anomaly.astype(bool)
    issues = []
    if not anomaly.equals(mask.any(axis=1)) or (mask.sum(axis=1) > 1).any():
        issues.append("COMPOUND_OR_INCONSISTENT_EVENT")
    if (locations.any(axis=1) & ~mask.Leak).any():
        issues.append("LOCATION_WITHOUT_LEAK")
    event = record.label_mapped
    expected = CLASS_COLUMNS.get(event)
    active = mask[expected] if expected else anomaly
    times = clock[active.to_numpy()]
    if event == "NORMAL":
        if len(times):
            issues.append("NORMAL_HAS_ACTIVE_EVENT")
    elif event not in CLASS_COLUMNS or not len(times):
        issues.append("DECLARED_EVENT_MISSING")
    else:
        if (not record.onset_s or times[0] != float(record.onset_s) or
                not np.all(np.diff(times) == 1) or
                (expected == "CompressorDelay" and (not record.delay_last_active_s or
                 times[-1] != float(record.delay_last_active_s)))):
            issues.append("DECLARED_EVENT_INTERVAL_MISMATCH")
        if not active.equals(anomaly):
            issues.append("UNDECLARED_EVENT_PRESENT")
    region_columns = tuple(c.removeprefix("leak_") for c in REGION_COLUMNS if locations[c].any())
    return {
        "onset_s": float(times[0]) if len(times) else None,
        "last_active_s": float(times[-1]) if len(times) else None,
        "release_region_annotations": region_columns,
        "region_eligible_from_archive": False,
        "region_metadata_permits_review": record.location_analysis_allowed == "True",
    }, tuple(issues)


def archive_path(record):
    rel = Path(record.file_clean).relative_to("H2-SimNet-Dataset")
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("invalid archive-relative path")
    return checked_file(RAW_DATASET_DIR / rel, record.sha256_clean)


def archive_observation(record, sensors, start: int, stop: int) -> MeasurementContract:
    """Load a fixed raw window with no resampling, conversion, or assumed bounds."""
    if record.eligible_primary != "True":
        raise ValueError("archive scenario is excluded")
    frame = load_scenario(archive_path(record))
    labels, issues = annotation(frame, record)
    if issues or not 0 <= start < stop <= len(frame):
        raise ValueError(f"archived window failed label/clock qualification: {issues}")
    clock = tuple(map(float, frame.index[start:stop]))
    if labels["onset_s"] is not None and (clock[0] < labels["onset_s"] or clock[-1] > labels["last_active_s"]):
        raise ValueError("window crosses the archived event boundary")
    if any(sensor.sensor_id not in frame or sensor.sensor_id in {*CLASS_COLUMNS.values(), *REGION_COLUMNS,
                                                                 "label_anomaly"} for sensor in sensors):
        raise ValueError("approved telemetry mapping does not resolve to observations")
    channels = tuple(Channel(s.sensor_id, s.unit, clock, "stored Parquet Timestamp index",
                             tuple(map(float, frame[s.sensor_id].iloc[start:stop])), ()) for s in sensors)
    return MeasurementContract(sensors, clock, channels, record.Scenario_ID, record.independence_group,
                               f"sha256:{record.sha256_clean}#rows={start}:{stop}", "SOURCE_BOUNDS_UNKNOWN")


def archive_cases(manifest):
    cases = []
    for row in manifest.itertuples(index=False):
        reasons = []
        labels = None
        if row.eligible_primary != "True":
            reasons.append("MANIFEST_EXCLUDED")
        else:
            try:
                labels, issues = annotation(load_scenario(archive_path(row)), row)
                reasons.extend(issues)
            except (OSError, ValueError) as exc:
                reasons.append(f"ARCHIVE_INPUT_UNVERIFIED: {exc}")
        cases.append({
            "scenario": row.Scenario_ID, "family": row.Scenario_Family_ID,
            "independence_group": row.independence_group, "topology_release": row.topology_release,
            "topology_candidate": row.topology_source_model, "topology_provenance": row.source_model_evidence,
            "event": row.label_mapped, "sha256_clean": row.sha256_clean,
            "annotation": labels, "archive_issues": reasons, "physically_eligible": False,
        })
    return cases


@dataclass(frozen=True)
class SourceQualification(Record):
    """Reviewed evidence binding an approved observation to a reproducible source model."""

    source_model: str
    observation_sha256: str
    adapter_sha256: str
    protocol_sha256: str
    allowed_hypotheses: tuple[str, ...]
    ledger: EvidenceLedger
    physical_bounds: tuple[ErrorBound, ...]
    sensor_error_bounds: tuple[ErrorBound, ...]


def measurement_digest(measurement: MeasurementContract):
    return hashlib.sha256(measurement.to_json().encode("utf-8")).hexdigest()


def activate_observation(measurement: MeasurementContract, approval: SourceQualification, adapter_path: Path,
                         protocol_path: Path):
    if (approval.observation_sha256 != measurement_digest(measurement) or not measurement.sensors or
            any(sensor.network_id != approval.source_model for sensor in measurement.sensors)):
        raise ValueError("source approval does not bind these measurements")
    checked_file(adapter_path, approval.adapter_sha256)
    checked_file(protocol_path, approval.protocol_sha256)
    for identifier in ("reproduced_source", "export_lineage", "effective_gas", "signed_sensor_map",
                       "source_model_validation", "ontology_approval"):
        evidence = approval.ledger.require(identifier, "record")
        if (evidence.scope != approval.source_model or evidence.category != EvidenceCategory.SOURCE or
                evidence.status != "VERIFIED"):
            raise ValueError(f"{identifier}: verified source evidence required")
    from .simnet_readiness import additional_physics_issues

    if problems := additional_physics_issues(measurement, approval):
        raise ValueError(f"source physics incomplete: {', '.join(problems)}")
    issues = physical_eligibility(approval.physical_bounds, approval.source_model)
    if issues:
        raise ValueError(f"physical uncertainty incomplete: {', '.join(issues)}")
    bounds = {b.name: b for b in approval.sensor_error_bounds}
    if len(bounds) != len(approval.sensor_error_bounds) or set(bounds) != {s.sensor_id for s in measurement.sensors}:
        raise ValueError("expected one bound for every approved sensor")
    channels = []
    for channel in measurement.channels:
        b = bounds[channel.sensor_id]
        if (b.interval is None or b.domain != approval.source_model or b.unit != channel.unit or not b.reference or
                b.basis not in (EvidenceBasis.CALIBRATED, EvidenceBasis.MEASURED, EvidenceBasis.MANUFACTURER) or
                not all(np.isfinite(b.interval)) or not b.interval[0] <= 0 <= b.interval[1]):
            raise ValueError(f"{channel.sensor_id}: invalid instrument uncertainty")
        channels.append(replace(channel, absolute_errors=(max(map(abs, b.interval)),) * len(channel.values)))
    result = replace(measurement, channels=tuple(channels), uncertainty_basis="verified source-bound uncertainty")
    if result.issues():
        raise ValueError(f"observation QC failed: {result.issues()}")
    return result


def evaluate_observation(measurement, approval, adapter_path, protocol_path,
                         models: tuple[HypothesisModel, ...]) -> DiagnosticDecision:
    if (tuple(model.name for model in models) != approval.allowed_hypotheses or
            approval.allowed_hypotheses not in (ONTOLOGY, ONTOLOGY[:2]) or
            any(model.adapter is None for model in models)):
        raise ValueError("the approved ontology requires every source-compatible adapter")
    observed = activate_observation(measurement, approval, adapter_path, protocol_path)
    pinned = json.loads(adapter_path.read_text(encoding="utf-8"))
    if pinned != adapter_spec(approval.source_model, models):
        raise ValueError("supplied hypothesis adapters differ from the approved model configuration")
    return diagnose(observed, models)


def adapter_spec(source_model, models):
    if any(not isinstance(model.adapter, Record) for model in models):
        raise ValueError("source adapters must expose serializable configuration")
    return {"source_model": source_model, "models": {
        model.name: {"type": type(model.adapter).__module__ + "." + type(model.adapter).__qualname__,
                     "configuration": json.loads(model.adapter.to_json()),
                     "assumptions": list(model.assumptions)}
        for model in models
    }}


@dataclass(frozen=True)
class SpatialPlan:
    approval: SourceQualification
    adapter_path: Path
    regions: tuple[str, ...]
    models: tuple[HypothesisModel, ...]


@dataclass(frozen=True)
class HeldOutCase:
    measurement: MeasurementContract
    approval: SourceQualification
    adapter_path: Path
    models: tuple[HypothesisModel, ...]
    spatial: SpatialPlan | None = None


def evaluate_regions(case: HeldOutCase, event: DiagnosticDecision, protocol_path):
    plan = case.spatial
    if plan is None:
        raise ValueError("missing predeclared spatial plan")
    alternatives = tuple(name for name in case.approval.allowed_hypotheses if name != "LEAK")
    expected = alternatives + plan.regions
    if (not plan.regions or len(set(expected)) != len(expected) or
            expected != plan.approval.allowed_hypotheses or
            expected != tuple(model.name for model in plan.models) or
            any(model.adapter is None for model in plan.models) or
            case.approval.protocol_sha256 != plan.approval.protocol_sha256):
        raise ValueError("spatial plan must preserve every required non-leak rival and region")
    ledger = plan.approval.ledger
    ontology = ledger.require("region_ontology", "record")
    truth = ledger.require("region_truth", "record")
    if (ontology.scope != case.approval.source_model or tuple(ontology.value) != plan.regions or
            truth.scope != case.measurement.run_id or truth.value not in plan.regions or
            any(item.status != "VERIFIED" or item.category != EvidenceCategory.SOURCE for item in (ontology, truth))):
        raise ValueError("missing verified region ontology or truth")
    observed = activate_observation(case.measurement, plan.approval, plan.adapter_path, protocol_path)
    if (observed != event.certificate.measurement or
            json.loads(plan.adapter_path.read_text(encoding="utf-8")) != adapter_spec(plan.approval.source_model, plan.models)):
        raise ValueError("spatial model is not pinned to the same approved observation/configuration")
    if event.status is not DecisionStatus.SPECIFIC or event.hypothesis != "LEAK":
        return Localization("L0", (), True, "NO_SPECIFIC_LEAK_ON_MATCHED_OBSERVATION"), truth.value, None
    decision = diagnose(observed, plan.models)
    return conditional_regions(event, decision, plan.regions), truth.value, json.loads(decision.to_json())


def evaluate_heldout(protocol_path: Path, protocol_sha256: str, cases: tuple[HeldOutCase, ...],
                     *, review_path: Path | None = None, review_sha256: str | None = None):
    """Evaluate the entire frozen held-out set, retaining abstentions in metrics.

    The conventional comparator uses the same checked joint result, so its
    hypothesis sets coincide wherever evidence is valid. This is not a solver race.
    """
    protocol = json.loads(checked_file(protocol_path, protocol_sha256).read_text(encoding="utf-8"))
    manifest, _ = catalog_tables()
    if protocol["study_version"] != "simnet-source-study/1" or protocol["manifest_sha256"] != hashlib.sha256(
            (CATALOG_DIR / CATALOG).read_bytes()).hexdigest():
        raise ValueError("wrong study or candidate manifest")
    partitions = protocol["partitions"]
    if not partitions or set(partitions.values()) != {"DEVELOPMENT", "MODEL_VALIDATION", "HELD_OUT"}:
        raise ValueError("all three partition roles are required")
    from .simnet_readiness import approved_partition

    groups = approved_partition(protocol, protocol_sha256, manifest, review_path, review_sha256)
    held = {name for name, split in partitions.items() if split == "HELD_OUT"}
    representatives = protocol.get("heldout_representatives", [])
    supplied = {case.measurement.run_id for case in cases}
    if (not held or not set(representatives) <= held or len(set(representatives)) != len(representatives) or
            supplied != set(representatives) or len(cases) != len(representatives)):
        raise ValueError("must evaluate every predeclared held-out representative exactly once")
    if {groups[name] for name in representatives} != {groups[name] for name in held} or len({
            groups[name] for name in representatives}) != len(representatives):
        raise ValueError("predeclare one representative for every held-out dependency component")
    catalog = manifest.set_index("Scenario_ID")
    if any(catalog.at[name, "eligible_primary"] != "True" for name in partitions):
        raise ValueError("partition contains excluded archive scenario")
    if any(catalog.loc[representatives, key].duplicated().any()
           for key in ("Scenario_Family_ID", "family_extended_sensitivity", "independence_group")):
        raise ValueError("held-out cases are repeated within a declared family")
    spatial_ids = set(protocol.get("localization_cases", []))
    if spatial_ids != {case.measurement.run_id for case in cases if case.spatial}:
        raise ValueError("supplied spatial cases differ from predeclared set")
    results, evaluation, localized = [], [], []
    for case in cases:
        name = case.measurement.run_id
        candidate = catalog.loc[name]
        # Separate run/event admission from the physics and sensor qualification.
        evidence = case.approval.ledger.require("event_truth", "record")
        if (evidence.category != EvidenceCategory.SOURCE or evidence.status != "VERIFIED" or
                evidence.scope != name or evidence.value != candidate.label_mapped or
                candidate.label_mapped not in case.approval.allowed_hypotheses or
                case.measurement.independence_group != candidate.independence_group or
                not case.measurement.source_id.startswith(f"sha256:{candidate.sha256_clean}#") or
                case.approval.protocol_sha256 != protocol_sha256 or
                list(case.approval.allowed_hypotheses) != protocol["event_ontology"] or
                protocol["observation_digests"].get(name) != measurement_digest(case.measurement)):
            raise ValueError(f"{name}: held-out label, group or observation not approved")
        window = re.fullmatch(r"sha256:[a-f0-9]{64}#rows=(\d+):(\d+)", case.measurement.source_id)
        original = manifest.loc[manifest.Scenario_ID == name].iloc[0]
        if not window or case.measurement != archive_observation(
                original, case.measurement.sensors, *map(int, window.groups())):
            raise ValueError(f"{name}: observation cannot be replayed from approved archive")
        started = perf_counter()
        decision = evaluate_observation(case.measurement, case.approval, case.adapter_path, protocol_path, case.models)
        elapsed = perf_counter() - started
        cert = decision.certificate
        results.append({"case": name, "joint_baseline": {"feasible": cert.feasible, "excluded": cert.excluded,
                                                        "indeterminate": cert.indeterminate},
                        "certified_policy": json.loads(decision.to_json()), "joint_and_policy_wall_s": elapsed})
        if case.spatial:
            if candidate.label_mapped != "LEAK" or candidate.location_analysis_allowed != "True":
                raise ValueError(f"{name}: not an admitted archive location case")
            location, truth, spatial_certificate = evaluate_regions(case, decision, protocol_path)
            results[-1]["localization"] = {"decision": json.loads(location.to_json()), "truth": truth,
                                             "certificate": spatial_certificate}
            localized.append((location, truth))
        evaluation.append(EvaluationCase(groups[name], "H2_SIMNET_SOURCE_SIMULATION",
                                         decision, candidate.label_mapped, True, True, runtime_s=elapsed))
    count = len(localized)
    return {"protocol_sha256": protocol_sha256, "claim": protocol["evaluation_claim"], "cases": results, "metrics": summarize(tuple(evaluation)),
            "location_metrics": {
                "eligible_families": count,
                "true_region_inclusion": sum(t in l.candidates for l, t in localized) / count if count else None,
                "unique_region_coverage": sum(l.level == "L2" for l, _ in localized) / count if count else None,
            }}


def conditional_regions(event: DiagnosticDecision, spatial: DiagnosticDecision, regions: tuple[str, ...]):
    if (event.status is not DecisionStatus.SPECIFIC or event.hypothesis != "LEAK" or
            event.certificate.measurement != spatial.certificate.measurement):
        return Localization("L0", (), True, "NO_SPECIFIC_LEAK_ON_MATCHED_OBSERVATION")
    return localize(spatial, regions)


def preflight():
    manifest, folds = catalog_tables()
    cases = archive_cases(manifest)
    fold_reports = []
    for fold, rows in folds.groupby("outer_fold_id"):
        issues = separation_issues(manifest, dict(zip(rows.Scenario_ID, rows.split_role)))
        fold_reports.append({"fold": fold, "issues": issues, "confirmatory": False})
    archived = [case for case in cases if not case["archive_issues"]]
    counts = Counter((case["topology_candidate"], case["event"]) for case in archived)
    center_measurement, evidence = source_case(RAW_DATASET_DIR)
    center_rows = manifest.loc[manifest.sha256_clean == DATA_HASH]
    if len(center_rows) != 1:
        raise ValueError("Center NORMAL does not uniquely resolve to the candidate manifest")
    measurement = archive_observation(center_rows.iloc[0], center_measurement.sensors, 0, 3)
    center = diagnose(measurement, tuple(HypothesisModel(h, None, ("SOURCE_EVIDENCE_MISSING",)) for h in ONTOLOGY))
    report = {
        "schema": "simnet-source-study/1", "tier": "ARCHIVAL_SOURCE_TRACE_ONLY",
        "verdict": "BLOCKED_PHYSICAL_CERTIFICATION_AND_CONFIRMATORY_SCORING",
        "catalog_sha256": hashlib.sha256((CATALOG_DIR / CATALOG).read_bytes()).hexdigest(),
        "source_requirements": SOURCE_REQUIREMENTS, "cases": cases, "legacy_fold_audit": fold_reports,
        "archive_annotation_counts": [{"topology_candidate": t, "event": e, "runs": n}
                                      for (t, e), n in sorted(counts.items())],
        "center_smoke": json.loads(center.to_json()), "center_evidence": evidence,
        "source_uncertainty": [json.loads(b.to_json()) for b in source_uncertainty()],
        "protocol": {
            "event_ontology": ONTOLOGY, "initial_scope": "NORMAL/LEAK only with signed source scope and both adapters",
            "unit": "one prespecified decision per verified independent family",
            "splits": "freeze scenario, extended/conservative families, cross-topology groups and digests before scoring",
            "observation": "same fixed sensor configuration, original clock and event/steady window across methods",
            "joint_baseline": "same source adapters, model, bounds, measurements, candidate hypotheses and solver",
            "localization": "specific LEAK then verified topology regions, exact same observation, all rivals retained",
            "robustness": ["clean versus noise-added as paired realizations", "prespecified sensor removal",
                           "verified uncertainty widening", "topology and family sensitivity"],
            "metrics": ["specific coverage", "selective risk when specific count > 0",
                        "true-hypothesis exclusion", "ambiguity and unresolved", "region inclusion and unique coverage",
                        "runtime and certificate replay"],
            "independent_metrics": summarize(tuple()),
        },
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True).strip(),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_record(args.output, preflight())


if __name__ == "__main__":
    main()
