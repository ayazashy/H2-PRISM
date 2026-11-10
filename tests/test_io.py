"""Tests for h2prism.io (F3). SYNTHETIC fixtures only."""

import numpy as np
import pandas as pd
import pytest

from h2prism.io import (TIME_SOURCE_ASSUMED, TIME_SOURCE_COLUMN, build_time_axis, find_invalid_intervals,
                        validate_scenario_frame)


def test_time_axis_requires_explicit_assumption():
    df = pd.DataFrame({"PS1": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError):
        build_time_axis(df)  # no silent universal sampling-rate assumption
    ax = build_time_axis(df, assumed_dt_s=1.0, assumption_source="dataset ReadME (REPORTED_UNVERIFIED)")
    assert ax.source == TIME_SOURCE_ASSUMED
    assert np.array_equal(ax.t, [0.0, 1.0, 2.0])


def test_time_axis_uses_column_without_repair():
    df = pd.DataFrame({"Timestamp": [0.0, 2.0, 1.0], "PS1": [1.0, 2.0, 3.0]})
    ax = build_time_axis(df, time_col="Timestamp")
    assert ax.source == TIME_SOURCE_COLUMN
    rep = validate_scenario_frame(df, channels=["PS1"], time_axis=ax)
    assert rep.monotonic_increasing is False
    assert not rep.ok
    assert list(df["Timestamp"]) == [0.0, 2.0, 1.0]  # input untouched


def test_duplicate_timestamps_detected():
    df = pd.DataFrame({"Timestamp": [0.0, 1.0, 1.0, 2.0], "PS1": [1.0] * 4})
    rep = validate_scenario_frame(df, ["PS1"], build_time_axis(df, time_col="Timestamp"))
    assert rep.n_duplicate_timestamps == 1 and not rep.ok


def test_irregular_sampling_flagged():
    df = pd.DataFrame({"Timestamp": [0.0, 1.0, 1.9, 3.0], "PS1": [1.0] * 4})
    rep = validate_scenario_frame(df, ["PS1"], build_time_axis(df, time_col="Timestamp"))
    assert rep.irregular_sampling is True
    assert rep.ok  # irregular sampling is a warning, not an error


def test_missing_values_reported_as_intervals():
    df = pd.DataFrame({"PS1": [1.0, np.nan, np.nan, 4.0, 5.0, np.inf], "MFS1": [0.0] * 6})
    assert find_invalid_intervals(df, ["PS1", "MFS1"]) == [(1, 2), (5, 5)]
    rep = validate_scenario_frame(df, ["PS1", "MFS1"])
    assert rep.missing_values_per_channel["PS1"] == 2
    assert rep.invalid_intervals == [(1, 2), (5, 5)]


def test_missing_and_non_numeric_channels_are_errors():
    df = pd.DataFrame({"PS1": ["a", "b"]})
    rep = validate_scenario_frame(df, ["PS1", "PS2"])
    assert "PS2" in rep.missing_channels and "PS1" in rep.non_numeric_channels and not rep.ok
