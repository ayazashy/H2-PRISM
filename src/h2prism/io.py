"""
H2-PRISM I/O validation layer (Task F3 -- preparation, Faisal ownership).

STATUS: IMPLEMENTED + TESTED on synthetic fixtures only. Not executed on the raw
H2-SimNet dataset in this branch (raw data absent). Requires Faisal technical
acceptance and Yazan review of loading assumptions (Gate 1).

Design rules enforced here (see 06_audit_preparation/MODEL_AND_EXPERIMENT_READINESS.md):
* Never modify the input frame; every function returns new objects.
* Never assume a sampling interval. If a file has no time column, the caller must
  pass an explicit ``assumed_dt_s`` together with its documented source; the
  resulting time axis is tagged ``INDEX_IMPLIED_ASSUMED`` and is never reported as
  verified.
* Never interpolate or forward-fill. Invalid rows are reported as intervals so the
  window generator can exclude affected windows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

PRESSURE_CHANNELS: Tuple[str, ...] = tuple(f"PS{i}" for i in range(1, 13))
FLOW_CHANNELS: Tuple[str, ...] = tuple(f"MFS{i}" for i in range(1, 5))
SENSOR_CHANNELS: Tuple[str, ...] = PRESSURE_CHANNELS + FLOW_CHANNELS

# Units are REPORTED in the dataset ReadME (Y1 status VERIFIED_FROM_DOCS); they are
# not derivable from the numeric values and must not be re-inferred here.
CHANNEL_UNITS: Dict[str, str] = {**{c: "MPa" for c in PRESSURE_CHANNELS}, **{c: "kg/s" for c in FLOW_CHANNELS}}

RAW_LABEL_COLUMNS: Tuple[str, ...] = (
    "label_anomaly", "Leak", "CompressorFault", "CompressorDelay",
    "leak_G3", "leak_G4", "leak_G5", "leak_G6",
)

TIME_SOURCE_COLUMN = "TIME_COLUMN"
TIME_SOURCE_INDEX = "TIME_INDEX"
TIME_SOURCE_ASSUMED = "INDEX_IMPLIED_ASSUMED"


@dataclass
class TimeAxis:
    """Time axis in seconds together with its provenance."""

    t: np.ndarray
    source: str  # TIME_COLUMN or INDEX_IMPLIED_ASSUMED
    column: Optional[str] = None
    assumption_note: Optional[str] = None


@dataclass
class ValidationReport:
    """Read-only schema/time/missingness report for one scenario frame."""

    n_rows: int
    missing_channels: List[str]
    non_numeric_channels: List[str]
    missing_values_per_channel: Dict[str, int]
    time_source: Optional[str]
    monotonic_increasing: Optional[bool]
    n_duplicate_timestamps: Optional[int]
    dt_median: Optional[float]
    dt_min: Optional[float]
    dt_max: Optional[float]
    irregular_sampling: Optional[bool]
    invalid_intervals: List[Tuple[int, int]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def build_time_axis(
    df: pd.DataFrame,
    time_col: Optional[str] = None,
    assumed_dt_s: Optional[float] = None,
    assumption_source: Optional[str] = None,
) -> TimeAxis:
    """Return the time axis of ``df``.

    If ``time_col`` exists in the frame it is used as-is (no sorting, no repair).
    Otherwise an explicit ``assumed_dt_s`` *and* a documented ``assumption_source``
    are required; this prevents a silent universal-sampling-rate assumption.
    """
    if time_col is not None and time_col in df.columns:
        t = pd.to_numeric(df[time_col], errors="coerce").to_numpy(dtype=float)
        return TimeAxis(t=t, source=TIME_SOURCE_COLUMN, column=time_col)
    if time_col is not None and df.index.name == time_col:
        # H2-SimNet Parquet files store time as an index named "Timestamp" (verified in
        # 06_audit_preparation/raw_verification/TIME_AXIS_AUDIT.csv)
        t = pd.to_numeric(pd.Series(df.index), errors="coerce").to_numpy(dtype=float)
        return TimeAxis(t=t, source=TIME_SOURCE_INDEX, column=time_col)
    if time_col is not None:
        raise KeyError(f"time column '{time_col}' not found in frame (neither column nor index name)")
    if assumed_dt_s is None or not assumption_source:
        raise ValueError(
            "No time column available: pass assumed_dt_s AND assumption_source "
            "(e.g. 'dataset ReadME, REPORTED_UNVERIFIED'). Sampling is never assumed silently."
        )
    if not np.isfinite(assumed_dt_s) or assumed_dt_s <= 0:
        raise ValueError("assumed_dt_s must be a positive finite number")
    t = np.arange(len(df), dtype=float) * float(assumed_dt_s)
    return TimeAxis(t=t, source=TIME_SOURCE_ASSUMED, assumption_note=assumption_source)


def find_invalid_intervals(df: pd.DataFrame, channels: Sequence[str]) -> List[Tuple[int, int]]:
    """Return inclusive [start_row, end_row] runs where any channel is NaN/inf/non-numeric."""
    present = [c for c in channels if c in df.columns]
    if not present:
        return [(0, len(df) - 1)] if len(df) else []
    vals = df[present].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    bad = ~np.isfinite(vals).all(axis=1)
    return _runs(bad)


def _runs(mask: np.ndarray) -> List[Tuple[int, int]]:
    out: List[Tuple[int, int]] = []
    if mask.size == 0:
        return out
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return out
    start = prev = int(idx[0])
    for i in idx[1:]:
        i = int(i)
        if i != prev + 1:
            out.append((start, prev))
            start = i
        prev = i
    out.append((start, prev))
    return out


def validate_scenario_frame(
    df: pd.DataFrame,
    channels: Sequence[str] = SENSOR_CHANNELS,
    time_axis: Optional[TimeAxis] = None,
    dt_rel_tolerance: float = 1e-6,
) -> ValidationReport:
    """Validate one scenario frame without modifying it.

    Errors: missing channels, non-numeric channels, non-monotonic or duplicate time.
    Warnings: missing values, irregular sampling, assumed time axis.
    """
    errors: List[str] = []
    warnings: List[str] = []
    missing = [c for c in channels if c not in df.columns]
    if missing:
        errors.append(f"missing channels: {missing}")
    non_numeric = [c for c in channels if c in df.columns and not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        errors.append(f"non-numeric channels: {non_numeric}")
    miss_counts = {
        c: int(pd.to_numeric(df[c], errors="coerce").isna().sum()) for c in channels if c in df.columns
    }
    if any(miss_counts.values()):
        warnings.append(f"missing values present in {sum(1 for v in miss_counts.values() if v)} channel(s)")

    mono = dup = dmed = dmin = dmax = irregular = None
    src = None
    if time_axis is not None:
        src = time_axis.source
        t = time_axis.t
        if src == TIME_SOURCE_ASSUMED:
            warnings.append(f"time axis is index-implied under an ASSUMED dt ({time_axis.assumption_note})")
        if len(t) != len(df):
            errors.append("time axis length differs from frame length")
        elif len(t) >= 2:
            if not np.isfinite(t).all():
                errors.append("time axis contains non-finite values")
            d = np.diff(t)
            mono = bool(np.all(d > 0))
            dup = int(np.sum(d == 0))
            if not mono:
                errors.append("time axis is not strictly increasing (non-monotonic or duplicate timestamps)")
            finite_d = d[np.isfinite(d)]
            if finite_d.size:
                dmed, dmin, dmax = float(np.median(finite_d)), float(finite_d.min()), float(finite_d.max())
                irregular = bool(dmed > 0 and (dmax - dmin) > dt_rel_tolerance * dmed)
                if irregular:
                    warnings.append(f"irregular sampling: dt in [{dmin:g}, {dmax:g}] s")

    return ValidationReport(
        n_rows=int(len(df)),
        missing_channels=missing,
        non_numeric_channels=non_numeric,
        missing_values_per_channel=miss_counts,
        time_source=src,
        monotonic_increasing=mono,
        n_duplicate_timestamps=dup,
        dt_median=dmed,
        dt_min=dmin,
        dt_max=dmax,
        irregular_sampling=irregular,
        invalid_intervals=find_invalid_intervals(df, channels),
        errors=errors,
        warnings=warnings,
    )


def read_table(path: Path) -> pd.DataFrame:
    """Read a CSV or Parquet file without any transformation."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"unsupported file type: {path.suffix}")
