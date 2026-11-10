"""
H2-PRISM time-domain feature extraction (Task F3 -- preparation, Faisal ownership).

STATUS: IMPLEMENTED + TESTED on synthetic fixtures only. Candidate per-channel
features follow the Faisal plan (F3 "Features and Leakage Prevention"):
mean, std, min, max, range, last-minus-first, linear slope, mean absolute first
difference. Which of these enter the primary feature set is a Faisal decision;
no cross-channel (e.g. mass-balance) features are produced because inlet/outlet
roles are not verified.

Leakage rules enforced here
* Feature extraction is purely per-window: no statistic is fitted across windows,
  so it cannot leak outer-test information. Scaling is fitted later, inside
  training folds only (see baseline.py / distinguishability.py).
* Identifier and metadata columns can never be selected as model features
  (``assert_no_metadata_features``).
"""

from __future__ import annotations

import hashlib
from typing import Callable, Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd

from .io import CHANNEL_UNITS, TimeAxis

METADATA_COLUMNS = (
    "window_id", "file_id", "Scenario_ID", "Scenario_Family_ID", "label_raw", "label_mapped",
    "phase", "topology", "boundary_status", "eligible_primary", "exclusion_reason", "outer_fold",
    "start_time", "end_time", "start_row", "end_row_exclusive", "n_samples", "label_mode",
    "time_source", "y_true",
)

# Features invariant to a constant per-channel offset (used by A15 delta/trend arm).
OFFSET_INVARIANT_FEATURES = ("std", "range", "last_minus_first", "slope", "mean_abs_diff")


def _slope(v: np.ndarray, t: np.ndarray) -> float:
    tc = t - t.mean()
    den = float(np.dot(tc, tc))
    return float(np.dot(tc, v - v.mean()) / den) if den > 0 else float("nan")


FEATURE_FUNCTIONS: Dict[str, Callable[[np.ndarray, np.ndarray], float]] = {
    "mean": lambda v, t: float(np.mean(v)),
    "std": lambda v, t: float(np.std(v, ddof=0)),
    "min": lambda v, t: float(np.min(v)),
    "max": lambda v, t: float(np.max(v)),
    "range": lambda v, t: float(np.max(v) - np.min(v)),
    "last_minus_first": lambda v, t: float(v[-1] - v[0]),
    "slope": _slope,
    "mean_abs_diff": lambda v, t: float(np.mean(np.abs(np.diff(v)))),
}

FEATURE_DEFINITIONS: Dict[str, str] = {
    "mean": "arithmetic mean of samples in window",
    "std": "population standard deviation (ddof=0) of samples in window",
    "min": "minimum sample in window",
    "max": "maximum sample in window",
    "range": "max - min within window",
    "last_minus_first": "last sample minus first sample in window",
    "slope": "ordinary least-squares slope of value on time (seconds) within window",
    "mean_abs_diff": "mean of |x[i+1]-x[i]| over consecutive samples in window (per sample, not per second)",
}

UNIT_RULE = {
    "mean": "{u}", "std": "{u}", "min": "{u}", "max": "{u}", "range": "{u}",
    "last_minus_first": "{u}", "slope": "{u}/s", "mean_abs_diff": "{u} per sample",
}


def feature_name(channel: str, feat: str) -> str:
    return f"{channel}__{feat}"


def assert_no_metadata_features(columns: Iterable[str]) -> None:
    bad = [c for c in columns if c in METADATA_COLUMNS]
    if bad:
        raise ValueError(f"metadata/identifier columns may not be model features: {bad}")


def feature_register(channels: Sequence[str], features: Sequence[str]) -> pd.DataFrame:
    """FEATURE_DEFINITION_REGISTER rows for the requested channel x feature grid."""
    rows = []
    for c in channels:
        unit = CHANNEL_UNITS.get(c, "UNKNOWN")
        for f in features:
            if f not in FEATURE_FUNCTIONS:
                raise KeyError(f"unknown feature '{f}'")
            rows.append({
                "feature_name": feature_name(c, f),
                "source_channel": c,
                "statistic": f,
                "definition": FEATURE_DEFINITIONS[f],
                "unit": UNIT_RULE[f].format(u=unit) if unit != "UNKNOWN" else "UNKNOWN",
                "unit_status": "REPORTED_IN_DATASET_DOCS" if unit != "UNKNOWN" else "UNKNOWN",
                "dtype": "float64",
                "missing_convention": "window excluded upstream if any source sample is non-finite",
                "offset_invariant": f in OFFSET_INVARIANT_FEATURES,
                "status": "SPECIFIED_CANDIDATE",
            })
    return pd.DataFrame(rows)


def extract_features(
    df: pd.DataFrame,
    time_axis: TimeAxis,
    window_manifest: pd.DataFrame,
    channels: Sequence[str],
    features: Sequence[str],
    eligible_only: bool = True,
) -> pd.DataFrame:
    """Compute the feature table for the windows of ONE scenario frame.

    Output columns: window_id, Scenario_ID, Scenario_Family_ID, label_mapped, then
    ``{channel}__{feature}`` in register order (deterministic).
    """
    for f in features:
        if f not in FEATURE_FUNCTIONS:
            raise KeyError(f"unknown feature '{f}'")
    missing = [c for c in channels if c not in df.columns]
    if missing:
        raise KeyError(f"channels missing from frame: {missing}")
    if window_manifest["Scenario_ID"].nunique() > 1:
        raise ValueError("extract_features operates on one scenario at a time")
    wm = window_manifest[window_manifest["eligible_primary"]] if eligible_only else window_manifest
    vals = df[list(channels)].to_numpy(dtype=float)
    t = np.asarray(time_axis.t, dtype=float)
    out: List[Dict[str, object]] = []
    for _, w in wm.iterrows():
        lo, hi = int(w["start_row"]), int(w["end_row_exclusive"])
        seg, tt = vals[lo:hi], t[lo:hi]
        rec: Dict[str, object] = {
            "window_id": w["window_id"],
            "Scenario_ID": w["Scenario_ID"],
            "Scenario_Family_ID": w["Scenario_Family_ID"],
            "label_mapped": w["label_mapped"],
        }
        for ci, c in enumerate(channels):
            v = seg[:, ci]
            for f in features:
                rec[feature_name(c, f)] = FEATURE_FUNCTIONS[f](v, tt) if len(v) >= 2 else float("nan")
        out.append(rec)
    cols = ["window_id", "Scenario_ID", "Scenario_Family_ID", "label_mapped"] + [
        feature_name(c, f) for c in channels for f in features
    ]
    return pd.DataFrame(out, columns=cols)


def model_feature_columns(table: pd.DataFrame) -> List[str]:
    """Return the feature columns (everything that is not metadata), validated."""
    cols = [c for c in table.columns if c not in METADATA_COLUMNS]
    assert_no_metadata_features(cols)
    return cols


def table_sha256(table: pd.DataFrame, float_format: str = "%.12g") -> str:
    """Deterministic content hash of a table (column order and row order matter)."""
    csv = table.to_csv(index=False, float_format=float_format, lineterminator="\n")
    return hashlib.sha256(csv.encode("utf-8")).hexdigest()
