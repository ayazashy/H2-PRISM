"""Tests for h2prism.windows (F3). SYNTHETIC fixtures only."""

import numpy as np
import pandas as pd
import pytest

from h2prism.io import build_time_axis, find_invalid_intervals
from h2prism.windows import (BOUNDARY_CROSSING, BOUNDARY_DURING, BOUNDARY_PRE, BOUNDARY_UNKNOWN, WindowConfig,
                             check_window_manifest, generate_windows, map_rows_to_primary)
from synthetic_fixtures import toy_scenario_frame

SCEN = {"file": "syn/a.parquet", "Scenario_ID": "SYN_A", "Scenario_Family_ID": "SYN_FAM_A", "label_raw": "Leak_G4",
        "label_mapped": "LEAK", "phase": "Steady State", "topology": "Center", "eligible_primary": True}


def _ax(df):
    return build_time_axis(df, assumed_dt_s=1.0, assumption_source="synthetic test")


def test_toy_window_count_and_boundaries():
    df = toy_scenario_frame(10, "NORMAL", None, seed=0)
    cfg = WindowConfig(window_s=4, stride_s=2, min_samples=4, label_mode="file_level", pre_event_policy="exclude")
    wm = generate_windows(df, _ax(df), {**SCEN, "label_mapped": "NORMAL"}, cfg)
    assert len(wm) == 4
    assert wm["start_time"].tolist() == [0.0, 2.0, 4.0, 6.0]
    assert wm["end_time"].tolist() == [4.0, 6.0, 8.0, 10.0]
    assert (wm["n_samples"] == 4).all()
    assert wm["window_id"].tolist() == [f"SYN_A_w{i:04d}" for i in range(4)]


def test_file_level_labels_never_claim_boundaries():
    df = toy_scenario_frame(20, "LEAK", 10, seed=1)
    cfg = WindowConfig(4, 4, 4, "file_level", "exclude")
    wm = generate_windows(df, _ax(df), SCEN, cfg)
    assert set(wm["boundary_status"]) == {BOUNDARY_UNKNOWN}
    assert set(wm["label_mapped"]) == {"LEAK"}


def test_row_level_boundary_crossing_and_pre_event_policy():
    df = toy_scenario_frame(20, "LEAK", 10, seed=1)
    ex = generate_windows(df, _ax(df), SCEN, WindowConfig(4, 2, 4, "row_level", "exclude"))
    cross = ex[ex["start_time"] == 8.0].iloc[0]  # rows 8-11 straddle onset at 10
    assert cross["boundary_status"] == BOUNDARY_CROSSING and not cross["eligible_primary"]
    pre = ex[ex["start_time"] == 0.0].iloc[0]
    assert pre["boundary_status"] == BOUNDARY_PRE and not pre["eligible_primary"]
    during = ex[ex["start_time"] == 12.0].iloc[0]
    assert during["boundary_status"] == BOUNDARY_DURING and during["label_mapped"] == "LEAK" and during["eligible_primary"]
    keep = generate_windows(df, _ax(df), SCEN, WindowConfig(4, 2, 4, "row_level", "label_normal"))
    pre2 = keep[keep["start_time"] == 0.0].iloc[0]
    assert pre2["label_mapped"] == "NORMAL" and pre2["eligible_primary"]


def test_invalid_values_exclude_window_without_imputation():
    df = toy_scenario_frame(12, "NORMAL", None, seed=2)
    df.loc[5, "PS1"] = np.nan
    wm = generate_windows(df, _ax(df), {**SCEN, "label_mapped": "NORMAL"}, WindowConfig(4, 4, 4, "file_level", "exclude"),
                          invalid_intervals=find_invalid_intervals(df, ["PS1", "MFS1"]))
    assert wm["eligible_primary"].tolist() == [True, False, True]
    assert "INVALID_VALUES_IN_WINDOW" in wm.loc[1, "exclusion_reason"]
    assert np.isnan(df.loc[5, "PS1"])


def test_irregular_sampling_uses_time_not_counts():
    df = pd.DataFrame({"PS1": np.arange(8.0), "Timestamp": [0, 1, 2, 3, 3.5, 4, 4.5, 5.0]})
    ax = build_time_axis(df, time_col="Timestamp")
    wm = generate_windows(df, ax, {**SCEN, "label_mapped": "NORMAL"}, WindowConfig(2, 2, 2, "file_level", "exclude"))
    assert wm["start_time"].tolist() == [0.0, 2.0]
    assert wm["n_samples"].tolist() == [2, 3]  # [0,2) holds t=0,1; [2,4) holds t=2,3,3.5


def test_non_monotonic_time_rejected():
    df = pd.DataFrame({"PS1": [1.0, 2.0, 3.0], "Timestamp": [0.0, 2.0, 1.0]})
    with pytest.raises(ValueError):
        generate_windows(df, build_time_axis(df, time_col="Timestamp"), SCEN, WindowConfig(1, 1, 2, "file_level", "exclude"))


def test_family_metadata_propagates_and_no_cross_scenario_windows():
    a = toy_scenario_frame(12, "NORMAL", None, seed=3)
    b = toy_scenario_frame(12, "LEAK", 0, seed=4)
    cfg = WindowConfig(4, 4, 4, "file_level", "exclude")
    wa = generate_windows(a, _ax(a), {**SCEN, "Scenario_ID": "SA", "Scenario_Family_ID": "FA", "label_mapped": "NORMAL"}, cfg)
    wb = generate_windows(b, _ax(b), {**SCEN, "Scenario_ID": "SB", "Scenario_Family_ID": "FB", "file": "syn/b.parquet"}, cfg)
    man = pd.concat([wa, wb], ignore_index=True)
    assert check_window_manifest(man) == []
    assert (wa["Scenario_Family_ID"] == "FA").all() and (wb["Scenario_Family_ID"] == "FB").all()
    assert (man["end_row_exclusive"] <= 12).all()


def test_manifest_check_flags_double_counted_exports():
    a = toy_scenario_frame(8, "NORMAL", None, seed=3)
    cfg = WindowConfig(4, 4, 4, "file_level", "exclude")
    s = {**SCEN, "label_mapped": "NORMAL"}
    w1 = generate_windows(a, _ax(a), s, cfg)
    w2 = generate_windows(a, _ax(a), {**s, "file": "syn/a_mirror.csv"}, cfg)
    probs = check_window_manifest(pd.concat([w1, w2]))
    assert any("duplicate window_id" in p for p in probs)
    assert any("more than one file" in p for p in probs)


def test_row_mapping_compound_and_untyped():
    df = pd.DataFrame({"label_anomaly": [0, 1, 1, 1], "Leak": [0, 0, 1, 1], "CompressorFault": [0, 0, 0, 1],
                       "CompressorDelay": [0, 0, 0, 0]})
    assert map_rows_to_primary(df).tolist() == ["NORMAL", "ANOMALY_WITHOUT_TYPE", "LEAK", "COMPOUND_EVENT"]


def test_deterministic_regeneration():
    df = toy_scenario_frame(50, "LEAK", 20, seed=9)
    cfg = WindowConfig(10, 5, 10, "row_level", "exclude")
    a = generate_windows(df, _ax(df), SCEN, cfg)
    b = generate_windows(df, _ax(df), SCEN, cfg)
    pd.testing.assert_frame_equal(a, b)


def test_config_validation():
    with pytest.raises(ValueError):
        WindowConfig(60, 30, 2, "row_level", "maybe")
    with pytest.raises(ValueError):
        WindowConfig(60, 30, 1, "row_level", "exclude")
