from dataclasses import replace
import hashlib

import pytest

from h2prism.certified_evidence import DecisionStatus
from h2prism.data.loader import RAW_DATASET_DIR
from h2prism.phase2 import DATA_HASH, PARQUET, source_case
from h2prism.physical_reference import EvidenceLedger
from h2prism.simnet_study import (
    ONTOLOGY, SourceQualification, activate_observation, archive_observation, catalog_tables,
    conditional_regions, measurement_digest, preflight, separation_issues,
)


def test_legacy_loto_is_not_family_independent():
    manifest, folds = catalog_tables()
    for _, rows in folds.groupby("outer_fold_id"):
        issues = separation_issues(manifest, dict(zip(rows.Scenario_ID, rows.split_role)))
        assert "independence_group:CROSS_PARTITION:13" in issues
    first, second = manifest.Scenario_ID.iloc[:2]
    altered = manifest.copy()
    altered.loc[1, "sha256_noise_added"] = altered.loc[0, "sha256_clean"]
    assert "SOURCE_DIGEST:CROSS_PARTITION:1" in separation_issues(altered, {first: "train", second: "test"})


@pytest.fixture(scope="module")
def simnet():
    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("official archive unavailable")
    return preflight()


def test_actual_archive_qc_gates_without_fabricating_physics(simnet):
    report = simnet
    assert len(report["cases"]) == 57
    assert sum(case["runs"] for case in report["archive_annotation_counts"]) == 51
    assert not any(case["physically_eligible"] for case in report["cases"])
    diagnostic = report["center_smoke"]
    assert diagnostic["status"] == DecisionStatus.UNRESOLVED.value
    assert tuple(diagnostic["certificate"]["indeterminate"]) == ONTOLOGY
    assert diagnostic["certificate"]["measurement"]["run_id"].startswith("CS_CENTER_")
    assert report["protocol"]["independent_metrics"]["selective_risk"] is None


def test_delay_window_cannot_include_onset_or_offset_boundary():
    manifest, _ = catalog_tables()
    delay = manifest.loc[manifest.label_mapped == "COMPRESSOR_DELAY"].iloc[0]
    if not (RAW_DATASET_DIR / "H2-SimNet-clean").exists():
        pytest.skip("official archive unavailable")
    for start, stop in ((24, 27), (999, 1002)):
        with pytest.raises(ValueError, match="event boundary"):
            archive_observation(delay, (), start, stop)


def test_unverified_source_evidence_cannot_activate_actual_observation(tmp_path):
    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("official archive unavailable")
    manifest, _ = catalog_tables()
    preliminary, _ = source_case(RAW_DATASET_DIR)
    row = manifest.loc[manifest.sha256_clean == DATA_HASH].iloc[0]
    m = archive_observation(row, preliminary.sensors, 0, 3)
    artifact = tmp_path / "manifest.json"
    artifact.write_text("{}", encoding="utf-8")
    sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    approval = SourceQualification(m.sensors[0].network_id, measurement_digest(m), sha, sha,
                                   ONTOLOGY[:2], EvidenceLedger(()), (), ())
    with pytest.raises(ValueError, match="reproduced_source"):
        activate_observation(m, approval, artifact, artifact)
    with pytest.raises(ValueError, match="does not bind"):
        activate_observation(replace(m, source_id="changed"), approval, artifact, artifact)
    assert all(not c.absolute_errors for c in m.channels)


def test_no_localization_without_leak_evidence():
    from h2prism.certified_evidence import HypothesisModel, diagnose

    if not (RAW_DATASET_DIR / PARQUET).exists():
        pytest.skip("official archive unavailable")
    measurement, _ = source_case(RAW_DATASET_DIR)
    decision = diagnose(measurement, (HypothesisModel("NORMAL", None, ()), HypothesisModel("LEAK", None, ())))
    assert conditional_regions(decision, decision, ("LEAK_A",)).level == "L0"
