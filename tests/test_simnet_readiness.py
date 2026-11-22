from dataclasses import replace
from hashlib import sha256
import json

import pytest

from h2prism.data.loader import RAW_DATASET_DIR, load_scenario
from h2prism.phase2 import DATA_HASH, PARQUET, source_case
from h2prism.phase6 import source_uncertainty
from h2prism.phase5 import physical_eligibility
from h2prism.physical_reference import Evidence, EvidenceCategory, EvidenceLedger
from h2prism.simnet_independence import (
    CONFIRMED, POTENTIAL, edge, groups, split_issues, digest,
)
from h2prism.simnet_readiness import additional_physics_issues, approved_partition, run
from h2prism.simnet_study import (
    ONTOLOGY, SourceQualification, annotation, archive_path, catalog_tables, measurement_digest,
)


def test_component_policy_keeps_transitive_histories_across_topologies():
    nodes = ("center", "downstream", "upstream", "isolated")
    links = [
        edge("center", "downstream", CONFIRMED, "verified shared prefix", "test", "prefix"),
        edge("downstream", "upstream", POTENTIAL, "matching design", "test", "no parent identity"),
    ]
    confirmed = groups(nodes, links)
    assert sorted(map(len, confirmed.values())) == [1, 1, 2]
    conservative = groups(nodes, links, True)
    assert sorted(map(len, conservative.values())) == [1, 3]
    assert groups(reversed(nodes), reversed(links), True) == conservative
    graph = {"nodes": dict.fromkeys(nodes), "conservative_components": conservative}
    assert split_issues(graph, {"center": "train", "upstream": "test"})
    assert not split_issues(graph, {"center": "train", "upstream": "train", "isolated": "test"})


@pytest.fixture(scope="module")
def readiness():
    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("official archive unavailable")
    return run()


def test_archive_reconstructs_13_flags_per_fold_without_claiming_proven_crossings(readiness):
    report = readiness
    graph = report["independence_graph"]
    assert graph["sha256"] == digest({key: value for key, value in graph.items() if key != "sha256"})
    assert graph["trajectory_cases_checked"] == graph["noise_assets_checked"] == 57
    assert len(graph["confirmed_components"]) == 45
    assert len(graph["conservative_components"]) == 11
    assert report["crossings_by_fold"] == {"1": 13, "2": 13, "3": 13}
    assert not any(row["confirmed_crossing"] for row in report["historical_crossings"])
    assert all(len({m["partition"] for m in row["members"]}) > 1 for row in report["historical_crossings"])


def test_group_safe_candidates_and_sparse_classes_are_retrospective(readiness):
    report = readiness
    graph = report["independence_graph"]
    totals = report["population_counts"]["conservative_components"]
    assert totals["components"] == 10
    assert totals["components_by_class"] == dict(zip(ONTOLOGY, (1, 8, 1, 1)))
    assert len(report["historical_exposure"]["inspection_cases"]) == 57
    proposals = report["proposed_partitions"]
    assert {p["strategy"] for p in proposals} == {
        "DETERMINISTIC_THREE_WAY", "NORMAL_LEAK_DESCRIPTIVE_HOLDOUT", "LEAVE_ONE_COMPONENT_OUT"}
    for item in proposals:
        assert item["status"] == "PROPOSED" and item["claim"] == "RETROSPECTIVE_DESCRIPTIVE_ONLY"
        assert len(item["assignments"]) == 51
        assert not split_issues(graph, item["assignments"])
    assert report["protocol"]["metrics"] is None
    assert report["archive"]["protocol"]["independent_metrics"]["specific_coverage"] is None


def test_static_site_candidates_do_not_establish_runtime_region_truth(readiness):
    cases = readiness["localization"]["cases"]
    assert len(cases) == 39 and readiness["localization"]["eligible"] == 0
    assert any("SINGLE_REGION_TRUTH_MISSING_OR_MULTISITE" in c["review_flags"] for c in cases)
    assert any("RELEASE_AND_CANDIDATE_TOPOLOGY_CONFLICT" in c["review_flags"] for c in cases)
    assert all(c["event_to_verified_region"] is None for c in cases)


def test_physics_gate_rejects_missing_gas_sign_mechanisms_and_error_bounds():
    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("official archive unavailable")
    observation, _ = source_case(RAW_DATASET_DIR)
    model = observation.sensors[0].network_id
    flow = next(s for s in observation.sensors if s.quantity == "mass_flow")
    map_entry = Evidence("signed_sensor_map", {flow.sensor_id: {
        "from_port": "A", "to_port": "B", "positive": "TO_FROM", "unit": flow.unit,
        "location_id": flow.location_id}}, "record", "contract test", EvidenceCategory.SOURCE,
        "VERIFIED", model, model)
    approval = SourceQualification(model, measurement_digest(observation), "", "", ONTOLOGY,
                                   EvidenceLedger((map_entry,)), source_uncertainty(), ())
    issues = additional_physics_issues(observation, approval)
    assert f"{flow.sensor_id}:SIGNED_SENSOR_MAPPING_UNSUPPORTED" in issues
    assert "EFFECTIVE_GAS_CONFIGURATION_UNSUPPORTED" in issues
    assert "compressor_telemetry:SOURCE_EVIDENCE_MISSING" in issues
    assert "delay_command_history:SOURCE_EVIDENCE_MISSING" in issues
    assert "leak_mechanism_and_opening:SOURCE_EVIDENCE_MISSING" in issues
    assert "model_discrepancy:MISSING" in physical_eligibility(approval.physical_bounds, model)
    assert "MISSING_PRESSURE_OR_MASS_FLOW" in additional_physics_issues(
        replace(observation, sensors=(flow,)), approval)


def test_invalid_onset_in_actual_archive_metadata_is_rejected():
    manifest, _ = catalog_tables()
    specimen = manifest[manifest.label_mapped.eq("LEAK")].iloc[0].copy()
    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("official archive unavailable")
    frame = load_scenario(archive_path(specimen))
    specimen.onset_s = ""
    assert "DECLARED_EVENT_INTERVAL_MISMATCH" in annotation(frame, specimen)[1]


def test_separate_protocol_approval_and_exposure_are_hard_gates(tmp_path):
    manifest, _ = catalog_tables()
    with pytest.raises(ValueError, match="scientific review"):
        approved_partition({}, "pinned", manifest, None, None)
    review = tmp_path / "review-test.json"
    review.write_text(json.dumps({"status": "APPROVED_AND_FROZEN", "protocol_sha256": "pinned",
                                 "approval_reference": "test record"}), encoding="utf-8")
    with pytest.raises(ValueError, match="cannot support a confirmatory claim"):
        approved_partition({"evaluation_claim": "CONFIRMATORY"}, "pinned", manifest,
                           review, sha256(review.read_bytes()).hexdigest())
