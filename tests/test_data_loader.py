"""
H2-PRISM Stage 2 Test Suite — Data Access & Loader Verification
Owner: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)
Verifies that the data loader module loads real scenarios and folds accurately.
"""

from pathlib import Path
import pandas as pd
import pytest

from h2prism.data import (
    load_scenario,
    load_fold,
    list_scenarios,
    get_dataset_dir,
    get_dataset_summary,
    is_raw_dataset_available,
)


def test_dataset_summary():
    """Verifies that dataset summary returns all expected metadata keys."""
    summary = get_dataset_summary()
    assert "raw_dataset_available" in summary
    assert "sample_dataset_available" in summary
    assert "primary_classes" in summary
    assert len(summary["primary_classes"]) == 4
    assert len(summary["sensor_channels"]["pressure"]) == 12
    assert len(summary["sensor_channels"]["mass_flow"]) == 4
    assert len(summary["sensor_channels"]["temperature"]) == 0


def test_list_scenarios():
    """Verifies that list_scenarios returns eligible 4-class scenarios."""
    df_scen = list_scenarios(eligible_only=True)
    assert isinstance(df_scen, pd.DataFrame)
    assert len(df_scen) > 0
    assert "Scenario_ID" in df_scen.columns
    assert "target_class" in df_scen.columns
    assert set(df_scen["target_class"].unique()).issubset(
        {"NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"}
    )


def test_load_scenario_by_short_name():
    """Verifies direct one-line loading of a scenario by short name."""
    df = load_scenario("leakG4")
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 20000
    assert "PS1" in df.columns
    assert "PS12" in df.columns
    assert "MFS1" in df.columns
    assert "MFS4" in df.columns
    assert "label_anomaly" in df.columns


def test_load_scenario_by_id():
    """Verifies loading a scenario by formal Scenario_ID."""
    df = load_scenario("SCEN_CENTER_STEADY_STATE_BROKENC1_STRONG")
    assert isinstance(df, pd.DataFrame)
    assert df.shape[0] == 20000
    assert "CompressorFault" in df.columns


def test_load_fold():
    """Verifies loading outer fold 1 train and test splits."""
    train_list, test_list = load_fold(fold_id=1)
    assert len(train_list) > 0
    assert len(test_list) > 0
    assert "data" in train_list[0]
    assert isinstance(train_list[0]["data"], pd.DataFrame)
    assert train_list[0]["data"].shape[0] == 20000
