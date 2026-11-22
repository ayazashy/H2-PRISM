"""
H2-PRISM Stage 2 Test Suite — Dataset Audit & Readiness Verification
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)
"""

from pathlib import Path
import yaml
import pandas as pd
import pytest

AUDIT_DIR = Path("01_dataset_audit")
PROV_DIR = AUDIT_DIR / "provisional"
CONFIGS_DIR = Path("configs")


def test_audit_deliverables_exist():
    """Verifies that all core Task Y1-Y8 deliverables exist in 01_dataset_audit/."""
    expected_files = [
        "raw_checksums.sha256",
        "FILE_LEVEL_AUDIT.csv",
        "SENSOR_CHANNEL_AUDIT.csv",
        "DUPLICATE_EXPORT_AUDIT.csv",
        "DATASET_INVENTORY.md",
        "DATASET_SCENARIO_MAP.csv",
        "SCENARIO_RELATIONSHIP_EDGES.csv",
        "SCENARIO_FAMILY_REPORT.md",
        "OPERATING_CONDITIONS_AUDIT.csv",
        "EVENT_TIMING_AUDIT.csv",
        "PHASE_CONFOUNDING_REPORT.md",
        "ORIGINAL_LABEL_INVENTORY.csv",
        "LABEL_OVERLAP_MATRIX.csv",
        "LABEL_MAPPING_SPEC.md",
        "class_mapping.yaml",
        "FAMILY_CLASS_DISTRIBUTION.csv",
        "SPLIT_FEASIBILITY_REPORT.md",
        "DATA_LEAKAGE_ASSESSMENT.md",
        "PROPOSED_GROUPED_EVALUATION_DESIGN.md",
        "folds.csv",
        "DATASET_READINESS_REPORT.md",
    ]
    for fn in expected_files:
        p = AUDIT_DIR / fn
        assert p.exists(), f"Missing audit deliverable: {p}"
        assert p.stat().st_size > 0, f"Empty audit deliverable: {p}"


def test_provisional_freeze_bundle():
    """Verifies Task Y8 provisional freeze package for Faisal."""
    expected_prov = [
        "PROVISIONAL_DATA_FREEZE_MANIFEST.csv",
        "PROVISIONAL_LABEL_MAPPING.yaml",
        "PROVISIONAL_DATA_FREEZE_NOTES.md",
        "PROVISIONAL_DATA_FREEZE_VERSION.txt",
    ]
    for fn in expected_prov:
        p = PROV_DIR / fn
        assert p.exists(), f"Missing provisional file: {p}"
        assert p.stat().st_size > 0, f"Empty provisional file: {p}"


def test_no_temperature_channels_in_dataset():
    """Forensic verification: confirms that zero temperature channels exist in H2-SimNet."""
    df_channels = pd.read_csv(AUDIT_DIR / "SENSOR_CHANNEL_AUDIT.csv")
    temp_channels = df_channels[df_channels["channel_name"].str.lower().str.contains("temp|t1|t2|kelvin|degc")]
    assert len(temp_channels) == 0, f"Unexpected temperature channels found: {temp_channels}"


def test_folds_zero_leakage():
    """Verifies that folds.csv has zero scenario and topology leakage between train and test."""
    df_folds = pd.read_csv(AUDIT_DIR / "folds.csv")
    assert len(df_folds) > 0, "folds.csv is empty"

    for fold_id, grp in df_folds.groupby("outer_fold_id"):
        train_scens = set(grp[grp["split_role"] == "train"]["Scenario_ID"])
        test_scens = set(grp[grp["split_role"] == "test"]["Scenario_ID"])
        leakage = train_scens.intersection(test_scens)
        assert len(leakage) == 0, f"Fold {fold_id} has scenario leakage: {leakage}"

        train_topologies = set(grp[grp["split_role"] == "train"]["topology"])
        test_topologies = set(grp[grp["split_role"] == "test"]["topology"])
        top_leakage = train_topologies.intersection(test_topologies)
        assert len(top_leakage) == 0, f"Fold {fold_id} has topology leakage: {top_leakage}"


def test_all_classes_present_in_all_folds():
    """Verifies that every fold has all 4 target classes present in both train and test."""
    df_folds = pd.read_csv(AUDIT_DIR / "folds.csv")
    expected_classes = {"NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"}

    for fold_id, grp in df_folds.groupby("outer_fold_id"):
        train_classes = set(grp[grp["split_role"] == "train"]["target_class"])
        test_classes = set(grp[grp["split_role"] == "test"]["target_class"])

        missing_train = expected_classes - train_classes
        missing_test = expected_classes - test_classes
        assert len(missing_train) == 0, f"Fold {fold_id} missing classes in train: {missing_train}"
        assert len(missing_test) == 0, f"Fold {fold_id} missing classes in test: {missing_test}"


def test_class_mapping_yaml():
    """Verifies that class_mapping.yaml is well-formed and valid YAML."""
    p = AUDIT_DIR / "class_mapping.yaml"
    with open(p, "r") as f:
        data = yaml.safe_load(f)
    assert "primary_4_class_target" in data
    assert "fallback_3_class_target" in data
    classes = data["primary_4_class_target"]["classes"]
    class_names = [c["class_name"] for c in classes]
    assert "NORMAL" in class_names
    assert "LEAK" in class_names
    assert "COMPRESSOR_FAULT" in class_names
    assert "COMPRESSOR_DELAY" in class_names


def test_interface_contracts():
    """Verifies that configs/interface_contracts.yaml exists and defines required schemas."""
    p = CONFIGS_DIR / "interface_contracts.yaml"
    assert p.exists()
    with open(p, "r") as f:
        data = yaml.safe_load(f)
    assert "contracts" in data
    assert "manifest_schema" in data["contracts"]
    assert "window_manifest_schema" in data["contracts"]
    assert "feature_table_schema" in data["contracts"]
    assert "prediction_table_schema" in data["contracts"]
