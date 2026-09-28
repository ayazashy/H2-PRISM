import pandas as pd
import pytest

from src.synchronization import (
    inspect_synchronization,
    synchronize_to_common_grid,
)


def test_regular_one_second_sampling_is_synchronized():
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 3, 4],
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    report = inspect_synchronization(df)

    assert report.sampling_interval_s == 1.0
    assert report.sampling_frequency_hz == 1.0
    assert report.monotonic is True
    assert report.duplicate_timestamps is False
    assert report.regular_sampling is True
    assert report.resampling_required is False
    assert report.resampling_performed is False
    assert report.interpolation_used is False
    assert report.temporal_resolution_s == 1.0
    assert report.status == "SYNCHRONIZED_NO_RESAMPLING_REQUIRED"


def test_irregular_sampling_requires_review():
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 4, 5],
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    report = inspect_synchronization(df)

    assert report.regular_sampling is False
    assert report.resampling_required is True
    assert report.resampling_performed is False
    assert report.interpolation_used is False
    assert report.status == "TEMPORAL_ALIGNMENT_REQUIRES_REVIEW"


def test_audit_derived_timestamp_is_explicitly_flagged():
    df = pd.DataFrame(
        {
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    report = inspect_synchronization(df)

    assert report.timestamp_source == "AUDIT_DERIVED_INDEX"
    assert report.timestamp_is_derived is True
    assert report.sampling_interval_s == 1.0
    assert report.sampling_frequency_hz == 1.0


def test_explicit_timestamp_column_is_preserved():
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 3, 4],
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    report = inspect_synchronization(df)

    assert report.timestamp_source == "EXPLICIT_COLUMN"
    assert report.timestamp_is_derived is False


def test_explicit_timestamp_index_is_detected():
    df = pd.DataFrame(
        {
            "PS1": [1, 2, 3, 4, 5],
        },
        index=pd.Index(
            [0, 1, 2, 3, 4],
            name="Timestamp",
        ),
    )

    report = inspect_synchronization(df)

    assert report.timestamp_source == "EXPLICIT_INDEX"
    assert report.timestamp_is_derived is False
    assert report.sampling_interval_s == 1.0
    assert report.sampling_frequency_hz == 1.0


def test_no_resampling_is_performed_by_default():
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 3, 4],
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    result = synchronize_to_common_grid(df)

    pd.testing.assert_frame_equal(result, df)
    assert result is not df


def test_upsampling_is_prohibited():
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 3, 4],
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    with pytest.raises(
        ValueError,
        match="Upsampling is prohibited",
    ):
        synchronize_to_common_grid(
            df,
            target_interval_s=0.1,
            allow_resampling=True,
        )


def test_resampling_is_not_automatically_enabled():
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 4, 5],
            "PS1": [1, 2, 3, 4, 5],
        }
    )

    with pytest.raises(
        ValueError,
        match="allow_resampling=False",
    ):
        synchronize_to_common_grid(
            df,
            target_interval_s=1.0,
        )