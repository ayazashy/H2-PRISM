"""
H2-PRISM Step 7: Temporal synchronization and sampling verification.

This module provides non-destructive temporal verification for H2-SimNet
and related tabular time-series data.

Scientific principles:
- Preserve source timestamps whenever available.
- Distinguish explicit timestamps from audit-derived time axes.
- Verify a common sampling interval before any resampling.
- Do not upsample or create artificial high-frequency information.
- Do not resample automatically.
- Preserve the original input DataFrame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


DEFAULT_SAMPLING_INTERVAL_S = 1.0


@dataclass(frozen=True)
class SynchronizationReport:
    """Structured report describing temporal synchronization status."""

    sampling_interval_s: Optional[float]
    sampling_frequency_hz: Optional[float]
    sample_count: int

    timestamp_source: str
    timestamp_is_derived: bool

    monotonic: bool
    duplicate_timestamps: bool
    regular_sampling: bool

    common_grid_interval_s: Optional[float]
    resampling_required: bool
    resampling_performed: bool

    interpolation_used: bool
    upsampling_performed: bool

    temporal_resolution_s: Optional[float]
    status: str


def _extract_timestamp(
    df: pd.DataFrame,
) -> tuple[pd.Series, bool, str]:
    """
    Extract an explicit timestamp column or use a numeric index.

    Returns:
        timestamp,
        timestamp_is_derived,
        timestamp_source
    """

    candidates = [
        column
        for column in df.columns
        if str(column).lower()
        in {"timestamp", "time", "datetime"}
    ]

    if candidates:
        return (
            pd.to_numeric(
                df[candidates[0]],
                errors="coerce",
            ),
            False,
            "EXPLICIT_COLUMN",
        )

    if (
        df.index.name is not None
        and str(df.index.name).lower()
        in {"timestamp", "time", "datetime"}
    ):
        return (
            pd.Series(
                pd.to_numeric(
                    df.index,
                    errors="coerce",
                ),
                index=df.index,
                name="timestamp",
            ),
            False,
            "EXPLICIT_INDEX",
        )

    return (
        pd.Series(
            np.arange(
                len(df),
                dtype=float,
            ),
            index=df.index,
            name="timestamp",
        ),
        True,
        "AUDIT_DERIVED_INDEX",
    )


def inspect_synchronization(
    df: pd.DataFrame,
    expected_interval_s: float = DEFAULT_SAMPLING_INTERVAL_S,
    tolerance_s: float = 1e-9,
) -> SynchronizationReport:
    """
    Verify temporal synchronization without modifying the input DataFrame.

    No resampling or interpolation is performed.
    """

    if expected_interval_s <= 0:
        raise ValueError(
            "expected_interval_s must be positive."
        )

    timestamp, timestamp_is_derived, timestamp_source = (
        _extract_timestamp(df)
    )

    values = pd.to_numeric(
        timestamp,
        errors="coerce",
    ).to_numpy(dtype=float)

    finite = np.isfinite(values)

    if len(values) < 2 or not finite.all():
        return SynchronizationReport(
            sampling_interval_s=None,
            sampling_frequency_hz=None,
            sample_count=len(values),
            timestamp_source=timestamp_source,
            timestamp_is_derived=timestamp_is_derived,
            monotonic=False,
            duplicate_timestamps=False,
            regular_sampling=False,
            common_grid_interval_s=expected_interval_s,
            resampling_required=True,
            resampling_performed=False,
            interpolation_used=False,
            upsampling_performed=False,
            temporal_resolution_s=None,
            status="INSUFFICIENT_OR_INVALID_TIMESTAMP_DATA",
        )

    differences = np.diff(values)

    monotonic = bool(
        np.all(differences > 0)
    )

    duplicate_timestamps = bool(
        np.any(differences == 0)
    )

    sampling_interval_s = float(
        np.median(differences)
    )

    regular_sampling = bool(
        np.all(
            np.isclose(
                differences,
                sampling_interval_s,
                atol=tolerance_s,
                rtol=0.0,
            )
        )
    )

    sampling_frequency_hz = (
        1.0 / sampling_interval_s
        if sampling_interval_s > 0
        else None
    )

    resampling_required = not bool(
        regular_sampling
        and np.isclose(
            sampling_interval_s,
            expected_interval_s,
            atol=tolerance_s,
            rtol=0.0,
        )
    )

    if (
        monotonic
        and not duplicate_timestamps
        and regular_sampling
        and not resampling_required
    ):
        status = "SYNCHRONIZED_NO_RESAMPLING_REQUIRED"
    elif monotonic and regular_sampling:
        status = "REGULAR_GRID_REQUIRES_REVIEW"
    else:
        status = "TEMPORAL_ALIGNMENT_REQUIRES_REVIEW"

    return SynchronizationReport(
        sampling_interval_s=sampling_interval_s,
        sampling_frequency_hz=sampling_frequency_hz,
        sample_count=len(values),
        timestamp_source=timestamp_source,
        timestamp_is_derived=timestamp_is_derived,
        monotonic=monotonic,
        duplicate_timestamps=duplicate_timestamps,
        regular_sampling=regular_sampling,
        common_grid_interval_s=expected_interval_s,
        resampling_required=resampling_required,
        resampling_performed=False,
        interpolation_used=False,
        upsampling_performed=False,
        temporal_resolution_s=sampling_interval_s,
        status=status,
    )


def synchronize_to_common_grid(
    df: pd.DataFrame,
    target_interval_s: float = DEFAULT_SAMPLING_INTERVAL_S,
    *,
    allow_resampling: bool = False,
) -> pd.DataFrame:
    """
    Return a temporally aligned copy only when explicitly requested.

    By default, this function refuses to resample.

    Upsampling is never permitted because it would create artificial
    high-frequency information unsupported by the native measurements.
    """

    if target_interval_s <= 0:
        raise ValueError(
            "target_interval_s must be positive."
        )

    report = inspect_synchronization(
        df,
        expected_interval_s=target_interval_s,
    )

    if not report.resampling_required:
        return df.copy(deep=True)

    if not allow_resampling:
        raise ValueError(
            "Resampling is required by the requested target grid, "
            "but allow_resampling=False. "
            "No interpolation or resampling was performed."
        )

    if (
        report.sampling_interval_s is not None
        and target_interval_s < report.sampling_interval_s
    ):
        raise ValueError(
            "Upsampling is prohibited because it would create "
            "artificial high-frequency information."
        )

    raise NotImplementedError(
        "Downsampling/interpolation requires an explicit, "
        "documented scientific policy and is not enabled by default."
    )