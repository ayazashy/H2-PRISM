"""Synthetic contract fixtures only. These tests exercise no physical benchmark."""
from dataclasses import replace
import hashlib

import pytest

from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.data_contracts import NetworkRecord, SensorRecord
from h2prism.experimental_data import ExperimentManifest, PhysicsApproval, SensorInput, check_splits, ingest_csv
from h2prism.phase5 import ErrorBound, EvidenceBasis, UNCERTAINTY
from h2prism.phase7 import CLEAN_CSV, archive_lineage, qualification
from h2prism.physical_reference import Evidence, EvidenceCategory, EvidenceLedger


@pytest.fixture
def case(tmp_path):
    source = tmp_path / "fixture.csv"
    source.write_text("time,P_read,F_read\n0.0,110000,0.02\n1.0,105000,-0.02\n2.0,104000,0.03\n", encoding="utf-8")
    network_id = "fixture-rig"
    geometry_ref = "fixture geometry"
    network = NetworkRecord(network_id, ("A", "B"), (("P01", "A", "B"),), "fixture geometry",
                            {"gas": "fixture gas"})

    def bound(name, unit, width=0.01):
        return ErrorBound(name, unit, (-width, width), EvidenceBasis.CALIBRATED, "fixture record", network_id)

    sensors = (
        SensorInput(SensorRecord("P", network_id, "node", "A", "pressure", "Pa", 1), "P_read",
                    "fixture converter", "fixture calibration", bound("P", "Pa", 5), "absolute"),
        SensorInput(SensorRecord("F", network_id, "edge", "P01", "mass_flow", "kg/s", 1), "F_read",
                    "fixture converter", "fixture calibration", bound("F", "kg/s"), "A->B"),
    )
    evidence = EvidenceLedger(tuple(
        Evidence(key, "synthetic data", "mixed", geometry_ref if key == "geometry" else "fixture trace",
                 EvidenceCategory.SOURCE, "FIXTURE", network_id, network_id)
        for key in ("geometry", "operating_conditions", "initial_state", "boundary_inputs", "gas_composition")
    ))
    manifest = ExperimentManifest(
        "fixture", "run-1", "family-1", ("origin-1",), "fixture run ledger", "T1", "fixture source",
        "fixture rights", "fixture permission", hashlib.sha256(source.read_bytes()).hexdigest(),
        "time", "fixture clock", network, sensors, "fixture gas", 300, "LEAK", 1, "R-A", "fixture event",
        evidence, tuple(bound(name, unit) for name, unit in UNCERTAINTY.items()),
    )
    approval = PhysicsApproval("fixture-model", network_id, geometry_ref, "fixture gas", (100000, 120000),
                               (298, 302), ("NORMAL", "LEAK"), ("P", "F"), ("R-A",), "fixture review")
    return source, manifest, approval


def test_ingests_original_clock_missing_scope_is_not_experimental(case):
    source, record, approval = case
    result = ingest_csv(source, record, approval)
    assert result.measurement.timestamps_s == (0, 1, 2)
    assert result.original_timestamps_s == ("0.0", "1.0", "2.0")
    assert result.measurement.channels[1].values[1] == -0.02
    assert result.eligibility.physics_compatible
    assert not result.eligibility.diagnostic_eligible and not result.eligibility.localization_eligible
    assert result.eligibility.reasons == ("NOT_AN_INDEPENDENT_PHYSICAL_EXPERIMENT",)
    assert any("ineligible held-out" in msg for msg in check_splits((result,), {"run-1": "HELD_OUT"}))


@pytest.mark.parametrize("field,value,reason", [
    ("license_reference", "", "DATA_USE_UNVERIFIED"),
    ("use_authorization_reference", "", "DATA_USE_UNVERIFIED"),
    ("ancestry", (), "RUN_ANCESTRY_UNVERIFIED"),
    ("onset_s", 5, "EVENT_GROUND_TRUTH_UNVERIFIED"),
    ("truth_reference", "", "EVENT_GROUND_TRUTH_UNVERIFIED"),
    ("temperature_k", 302, "NO_MATCHED_PHYSICAL_APPROVAL"),
    ("gas", "different gas", "NO_MATCHED_PHYSICAL_APPROVAL"),
    ("uncertainty", (), "PHYSICAL_UNCERTAINTY_INCOMPLETE"),
])
def test_missing_or_domain_incompatible_metadata_fails_closed(case, field, value, reason):
    path, record, approval = case
    ingested = ingest_csv(path, replace(record, **{field: value}), approval)
    assert reason in ingested.eligibility.reasons


def test_bad_pressure_unit_calibration_and_bound_are_rejected(case):
    path, record, review = case
    p, f = record.sensors
    p = replace(p, sensor=replace(p.sensor, unit="MPa"), calibration_reference="",
                error=replace(p.error, interval=(0, -1)))
    f = replace(f, reference_convention="B->A")
    reasons = ingest_csv(path, replace(record, sensors=(p, f)), review).eligibility.reasons
    assert "PRESSURE_OR_FLOW_REFERENCE_UNVERIFIED" in reasons
    assert {"CALIBRATION_MISSING", "UNVERIFIED_OR_NON_SI_UNIT", "INSTRUMENT_BOUND_MISSING_OR_INVALID"} <= set(reasons)


def test_missing_samples_checksum_and_holdout_leakage(case, tmp_path):
    path, record, approval = case
    original = ingest_csv(path, record, approval)
    copy = tmp_path / "copy.csv"
    copy.write_text(path.read_text().replace("0.0,", "0.00,").replace("105000", ""), encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        ingest_csv(copy, record, approval)
    modified = replace(record, run_id="run-2", family="family-2", sha256=hashlib.sha256(copy.read_bytes()).hexdigest())
    altered = ingest_csv(copy, modified, approval)
    assert altered.missing_samples[0] == ("P", (1,))
    issues = check_splits((original, altered), {"run-1": "DEVELOPMENT", "run-2": "HELD_OUT"})
    assert any("shared ancestor" in detail for detail in issues)
    assert any("ineligible held-out" in detail for detail in issues)
    assert any("repeated held-out ancestry" in detail for detail in check_splits(
        (original, altered), {"run-1": "HELD_OUT", "run-2": "HELD_OUT"}))
    copy.write_text(path.read_text().replace("0.0,", "0.00,"), encoding="utf-8")
    same_trajectory = ingest_csv(copy, replace(modified, sha256=hashlib.sha256(copy.read_bytes()).hexdigest()), approval)
    assert same_trajectory.trajectory_sha256 == original.trajectory_sha256
    assert any("duplicate source or trajectory" in item for item in
               check_splits((original, same_trajectory), {"run-1": "DEVELOPMENT", "run-2": "MODEL_VALIDATION"}))


def test_source_lineage_and_candidate_gate():
    if not (RAW_DATASET_DIR / CLEAN_CSV).exists():
        pytest.skip("official archive unavailable")
    result = archive_lineage()
    assert result["shared_timestamps"] == 5000
    assert result["clean_release_timestamps"] == 20000
    assert result["clean_csv_vs_parquet_max"] < 1e-9
    assert result["archival_residual_peaks"]["PS1"]["time_s"] == "28"
    assert result["archival_residual_peaks"]["MFS3"]["signed"] == pytest.approx(0.05302821566)
    outcomes = {row["hypothesis"]: row["outcome"] for row in result["hypotheses"]}
    assert outcomes["Published resampling alone"] == "REJECTED"
    assert outcomes["Different runs"] == "UNRESOLVED"
    options = qualification()
    assert options["candidate_register"][0]["decision"] == "ACCESS_REQUIRED"
    assert options["eligible_physical_families"] == 0 and options["independent_metrics"] is None
