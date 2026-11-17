"""Consolidated H₂-SimNet independence, source and evaluation gates."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .data.loader import WORKSPACE_ROOT
from .phase2 import checked_file
from .phase3 import write_record
from .physical_reference import EvidenceCategory
from .simnet_independence import (build_graph, candidate_splits, crossing_legacy, historical_exposure,
                                   split_issues, support)
from .simnet_study import ONTOLOGY, catalog_tables, preflight

GRAPH = "06_audit_preparation/simulation/h2net_v1/candidate/RELEASED_NETWORK_GRAPH.json"
MECHANISMS = {
    "NORMAL": ("normal_boundary_history", "stored_mass_initialization"),
    "LEAK": ("matched_normal_ancestry", "leak_mechanism_and_opening", "leak_onset_and_region"),
    "COMPRESSOR_FAULT": ("compressor_telemetry", "compressor_fault_injection"),
    "COMPRESSOR_DELAY": ("delay_command_history", "delay_response_and_offset"),
}


def additional_physics_issues(measurement, approval):
    """Check signed native mapping and hypothesis-specific evidence at activation."""
    issues = []
    for key in ("operating_domain", "storage_history", "numerical_error_enclosure",
                *(key for event in approval.allowed_hypotheses for key in MECHANISMS.get(event, ()))):
        try:
            item = approval.ledger.require(key, "record")
            if (item.scope != approval.source_model or item.category != EvidenceCategory.SOURCE or
                    item.status != "VERIFIED"):
                issues.append(f"{key}:SOURCE_EVIDENCE_UNVERIFIED")
        except ValueError:
            issues.append(f"{key}:SOURCE_EVIDENCE_MISSING")
    try:
        gas = approval.ledger.require("effective_gas", "record").value
        if (not isinstance(gas, dict) or not all(gas.get(key) for key in (
                "composition", "property_model", "runtime_reference", "domain_reference"))):
            issues.append("EFFECTIVE_GAS_CONFIGURATION_UNSUPPORTED")
    except ValueError:
        issues.append("EFFECTIVE_GAS_CONFIGURATION_UNSUPPORTED")
    try:
        mapping = approval.ledger.require("signed_sensor_map", "record").value
        for sensor in measurement.sensors:
            row = mapping.get(sensor.sensor_id, {}) if isinstance(mapping, dict) else {}
            row = row if isinstance(row, dict) else {}
            signed = (row.get("pressure_reference") == "ABSOLUTE" if sensor.quantity == "pressure" else
                      bool(row.get("from_port") and row.get("to_port") and
                           row["from_port"] != row["to_port"] and row.get("positive") == "FROM_TO"))
            if (not signed or row.get("unit") != sensor.unit or row.get("location_id") != sensor.location_id):
                issues.append(f"{sensor.sensor_id}:SIGNED_SENSOR_MAPPING_UNSUPPORTED")
    except ValueError:
        issues.append("SIGNED_SENSOR_MAPPING_UNSUPPORTED")
    if not {"pressure", "mass_flow"} <= {sensor.quantity for sensor in measurement.sensors}:
        issues.append("MISSING_PRESSURE_OR_MASS_FLOW")
    return sorted(set(issues))


def approved_partition(protocol, protocol_sha256, manifest, review_path, review_sha256):
    if review_path is None or review_sha256 is None:
        raise ValueError("a separately supplied frozen scientific review is required")
    review = json.loads(checked_file(Path(review_path), review_sha256).read_text(encoding="utf-8"))
    if (review.get("status") != "APPROVED_AND_FROZEN" or not review.get("approval_reference") or
            review.get("protocol_sha256") != protocol_sha256):
        raise ValueError("scientific review does not approve this exact protocol")
    exposure = historical_exposure(manifest)
    # This V03 catalog is historically inspected. A new confirmatory collection
    # needs a different, independently reviewed generating-run manifest.
    if protocol.get("evaluation_claim") != "RETROSPECTIVE_DESCRIPTIVE_ONLY":
        raise ValueError(f"V03 cannot support a confirmatory claim: {exposure['confirmatory_status']}")
    graph = build_graph(manifest)
    if graph["trajectory_cases_unchecked"] or protocol.get("independence_graph_sha256") != graph["sha256"]:
        raise ValueError("dependency graph is incomplete or differs from the frozen protocol")
    if issues := split_issues(graph, protocol["partitions"]):
        raise ValueError(f"ancestry leakage: {issues}")
    return {case: group for group, members in graph["conservative_components"].items() for case in members}


def location_inventory(cases):
    graph_path = WORKSPACE_ROOT / GRAPH
    document = json.loads(graph_path.read_text(encoding="utf-8"))
    models = document["models"]
    suffix = {"Center": "center", "Upstream": "up", "Downstream": "down"}
    result = []
    for row in cases:
        if row["event"] != "LEAK" or row["annotation"] is None:
            continue
        labels = list(row["annotation"]["release_region_annotations"])
        model_name = f"Anomalous_HNetwork_gest_{suffix[row['topology_candidate']]}"
        model = models[model_name]
        checked_file(WORKSPACE_ROOT / model["file"], model["sha256"])
        matches = {label: [{"sid": b["sid"], "nets": b["nets"], "parameters": b["params"]}
                           for b in model["components"] if b["name"] == f"Local Restriction (G){label[1:]}"]
                   for label in labels}
        # A label for multiple simultaneous sites cannot score single-region truth.
        issues = ["RUNTIME_LEAK_ACTUATION_AND_SENSOR_TRANSFER_UNVERIFIED"]
        if len(labels) != 1:
            issues.append("SINGLE_REGION_TRUTH_MISSING_OR_MULTISITE")
        if any(len(items) != 1 for items in matches.values()):
            issues.append("UNSUPPORTED_STATIC_COMPONENT_MAPPING")
        if not row["annotation"]["region_metadata_permits_review"]:
            issues.append("MANIFEST_LOCATION_REVIEW_EXCLUDED")
        if row["topology_release"] != row["topology_candidate"]:
            issues.append("RELEASE_AND_CANDIDATE_TOPOLOGY_CONFLICT")
        result.append({"case": row["scenario"], "archive_labels": labels, "onset_s": row["annotation"]["onset_s"],
                       "model_candidate": model_name, "model_sha256": model["sha256"],
                       "static_restriction_candidates": matches, "review_flags": issues,
                       "event_to_verified_region": None, "localization_eligible": False})
    return {"reference": GRAPH, "sha256": hashlib.sha256(graph_path.read_bytes()).hexdigest(),
            "eligible": 0, "cases": result}


def run():
    archive = preflight()
    manifest, folds = catalog_tables()
    graph = build_graph(manifest)
    eligible = {row["scenario"] for row in archive["cases"] if not row["archive_issues"]}
    proposals = candidate_splits(graph, eligible, archive["catalog_sha256"])
    crossings = crossing_legacy(manifest, folds, graph)
    exposure = historical_exposure(manifest)
    regions = location_inventory(archive["cases"])
    conservative = support(graph, graph["conservative_components"], eligible)
    confirmed = support(graph, graph["confirmed_components"], eligible)
    hypothesis_readiness = {
        event: {"status": "CONDITIONAL" if event in ("NORMAL", "LEAK") else "BLOCKED",
                "archived_label_checked_runs": conservative["runs_by_class"].get(event, 0),
                "conservative_components": conservative["components_by_class"][event],
                "required_native_observations": ["time-synchronized absolute pressure", "signed mass flow"],
                "required_source_mechanisms": MECHANISMS[event],
                "source_physics_gate": "BLOCKED", "deterministic_uncertainty_gate": "BLOCKED",
                "confirmatory_units": 0}
        for event in ONTOLOGY
    }
    return {
        "schema": "simnet-readiness/1", "commit": archive["commit"],
        "archive": archive, "independence_graph": graph, "historical_crossings": crossings,
        "crossings_by_fold": dict(Counter(row["fold"] for row in crossings)),
        "historical_exposure": exposure, "proposed_partitions": proposals,
        "population_counts": {"unique_clean_and_noise_assets_referenced": len({
                                      path for row in graph["nodes"].values()
                                      for path in (row["clean"], row["noise_added"]) if path}),
                              "candidate_runs": len(graph["nodes"]), "archive_label_checked_runs": len(eligible),
                              "confirmed_edge_components": confirmed, "conservative_components": conservative,
                              "verified_independent_generating_units": 0, "physically_qualified_runs": 0,
                              "confirmatory_units": 0},
        "hypothesis_readiness": hypothesis_readiness, "localization": regions,
        "protocol": {"version": "simnet-source-study/1", "claim": "RETROSPECTIVE_DESCRIPTIVE_ONLY",
                     "activation": "evaluate_heldout requires separate checksum-bound scientific approval",
                     "analysis_unit": "one conservative component",
                     "statistical_plan": "Descriptive only in V03; no confidence intervals or significance claims",
                     "robustness": [*archive["protocol"]["robustness"], "prespecified operating-point/window variation",
                                    "numerical tolerance and model discrepancy checks"],
                     "frozen": False, "metrics": None},
        "matlab": {"new_authorized_startup_evidence": False, "launched": False,
                   "latest": "5202 before model loading in Phase 6", "source_execution": "BLOCKED"},
        "verdicts": {"data_integrity": "PASS" if not graph["trajectory_cases_unchecked"] and len(eligible) == 51 else "BLOCKED",
                     "scenario_independence": "CONDITIONAL", "physical_model_validity": "BLOCKED",
                     "certified_diagnostic_readiness": "BLOCKED", "final_experimental_readiness": "BLOCKED"},
    }


def figure(report, output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    counts = report["population_counts"]
    classes = ("Normal", "Leak", "Compressor fault", "Delay")
    x = range(len(ONTOLOGY))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    for index, (key, text) in enumerate((("confirmed_edge_components", "Confirmed edges only"),
                                         ("conservative_components", "Including potential edges"))):
        point = [n + 0.30 * index for n in x]
        data = counts[key]["components_by_class"]
        axes[0].bar(point, [data[k] for k in ONTOLOGY], width=0.28, label=text)
    axes[0].set_xticks([n + .15 for n in x], classes, rotation=15)
    axes[0].set(ylabel="Dependency components", title="Archive class support")
    axes[0].legend()
    folds = report["crossings_by_fold"]
    axes[1].bar(list(folds), list(folds.values()), color="#d18c37",
                label="Declared group crossings")
    confirmed = Counter(row["fold"] for row in report["historical_crossings"] if row["confirmed_crossing"])
    axes[1].scatter(list(folds), [confirmed[f] for f in folds], color="#2e4459", zorder=3,
                    label="Confirmed edges crossing within flagged groups")
    axes[1].set(xlabel="Legacy fold", ylabel="Crossing groups", title="Legacy topology-held-out splits", ylim=(-1, 16))
    axes[1].legend(loc="upper center", fontsize=8)
    fig.suptitle(f"H2-SimNet archive readiness | {report['independence_graph']['sha256'][:12]}")
    with output.open("xb") as file:
        fig.savefig(file, format="png", dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--figure", type=Path)
    args = parser.parse_args()
    result = run()
    write_record(args.output, result)
    if args.figure:
        figure(result, args.figure)


if __name__ == "__main__":
    main()
