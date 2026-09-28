"""
Unit tests for H2-PRISM Step 6 Data Quality Control.
"""

import numpy as np
import pandas as pd

from src.quality import QualityController


def _native_dataframe(n=30):
    """Create a small H2-SimNet-like wide dataframe."""
    data = {
        "timestamp": np.arange(n, dtype=float),
    }

    for i in range(1, 13):
        data[f"PS{i}"] = 5.0 + (i * 0.01)

    for i in range(1, 5):
        data[f"MFS{i}"] = 10.0 + (i * 0.1)

    return pd.DataFrame(data)


def test_native_h2simnet_channels_are_detected():
    df = _native_dataframe()

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert len(result["measurement_channels"]) == 16
    assert "PS1" in result["measurement_channels"]
    assert "PS12" in result["measurement_channels"]
    assert "MFS1" in result["measurement_channels"]
    assert "MFS4" in result["measurement_channels"]


def test_missing_values_are_flagged_without_deletion():
    df = _native_dataframe()
    df.loc[5, "PS3"] = np.nan

    original_length = len(df)

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert len(df) == original_length
    assert result["channel_flags"]["PS3"].value == "MISSING"
    assert result["quality_flags"]["PS3"].iloc[5] == "MISSING"
    assert result["data_was_modified"] is False


def test_duplicate_timestamp_is_detected():
    df = _native_dataframe()
    df.loc[10, "timestamp"] = df.loc[9, "timestamp"]

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert result["timestamp_checks"]["duplicate_timestamps"] is True
    assert result["timestamp_checks"]["non_positive_intervals"] is True


def test_non_monotonic_timestamp_is_detected():
    df = _native_dataframe()
    df.loc[10, "timestamp"] = 5.0

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert result["timestamp_checks"]["non_monotonic_timestamps"] is True


def test_irregular_sampling_is_detected():
    df = _native_dataframe()
    df.loc[10:, "timestamp"] += 2.0

    qc = QualityController(expected_sampling_interval=1.0)
    result = qc.inspect_dataframe(df)

    assert result["sampling_checks"]["irregular_sampling"] is True
    assert result["sampling_checks"]["off_expected_interval_count"] > 0


def test_stuck_segment_is_detected():
    df = _native_dataframe()

    # 20 consecutive identical samples.
    df.loc[5:24, "PS4"] = 5.0

    qc = QualityController(stuck_window_size=15)
    result = qc.inspect_dataframe(df)

    assert result["sensor_checks"]["PS4"]["stuck"]["detected"] is True
    assert result["channel_flags"]["PS4"].value == "STUCK"


def test_sudden_discontinuity_is_detected_when_configured():
    df = _native_dataframe()

    df.loc[15:, "PS5"] += 5.0

    qc = QualityController(discontinuity_threshold=1.0)
    result = qc.inspect_dataframe(df)

    assert result["sensor_checks"]["PS5"]["discontinuity"]["detected"] is True
    assert result["channel_flags"]["PS5"].value == "DISCONTINUITY"


def test_impossible_numeric_value_is_flagged():
    df = _native_dataframe()

    df.loc[7, "PS6"] = -1.0

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert result["numeric_checks"]["PS6"]["out_of_range_count"] > 0
    assert result["channel_flags"]["PS6"].value == "INVALID"


def test_communication_gap_is_detected():
    df = _native_dataframe()

    df.loc[15:, "timestamp"] += 20.0

    qc = QualityController(communication_gap_threshold=10.0)
    result = qc.inspect_dataframe(df)

    assert result["communication_checks"]["PS1"]["detected"] is True
    assert result["communication_checks"]["PS1"]["count"] > 0


def test_station_ordering_is_not_assumed():
    df = _native_dataframe()

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert result["station_ordering"]["verified"] is False
    assert result["station_ordering"]["status"] == "UNKNOWN"


def test_wide_form_timestamp_alignment_is_reported():
    df = _native_dataframe()

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert (
        result["timestamp_alignment"]["status"]
        == "ALIGNED_BY_SHARED_DATAFRAME_INDEX"
    )


def test_native_units_are_recognized():
    df = _native_dataframe()

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    units = result["unit_checks"]["channel_units"]

    assert units["PS1"] == "MPa"
    assert units["PS12"] == "MPa"
    assert units["MFS1"] == "kg/s"
    assert units["MFS4"] == "kg/s"

    assert result["unit_checks"]["inconsistent_units"] is False


def test_no_data_are_deleted_by_qc():
    df = _native_dataframe()
    original = df.copy(deep=True)

    df.loc[4, "PS7"] = np.nan
    df.loc[8, "PS8"] = -10.0

    qc = QualityController()
    result = qc.inspect_dataframe(df)

    assert len(df) == len(original)
    assert result["data_was_modified"] is False
    assert pd.isna(df.loc[4, "PS7"])
    assert df.loc[8, "PS8"] == -10.0