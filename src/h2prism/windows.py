"""
H2-PRISM window generation and eligibility (Task F3 -- preparation, Faisal ownership).

STATUS: IMPLEMENTED + TESTED on synthetic fixtures only. Window length/stride are
NOT chosen here: the 60 s / 30 s pair in the Faisal plan is an *initial candidate*
that Faisal must justify (plan F3 step 23). All decision-bearing parameters are
required arguments so that no scientific choice is made silently.

Guarantees
* Windows never span two files/scenarios: one call == one scenario frame.
* Windows are defined on the time axis (seconds), so irregular sampling does not
  silently change window duration; the sample count is recorded and checked.
* Windows touching an invalid interval (NaN/inf) are excluded, never imputed.
* Boundary handling depends on timing knowledge:
    - row-level labels  -> PRE_EVENT / DURING_EVENT / POST_EVENT / BOUNDARY_CROSSING
    - file-level labels -> UNKNOWN_TIMING (no boundary-exclusion claim is possible)
* window_id = f"{Scenario_ID}_w{index:04d}" (configs/interface_contracts.yaml) and is
  stable under re-generation with identical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from .io import SENSOR_CHANNELS, TimeAxis

PRIMARY_CLASSES = ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY")

# Row-level outcomes that are never primary training targets.
ROW_COMPOUND = "COMPOUND_EVENT"
ROW_ANOMALY_UNTYPED = "ANOMALY_WITHOUT_TYPE"
ROW_UNLABELED = "UNLABELED"

BOUNDARY_NO_EVENT = "NO_EVENT"
BOUNDARY_PRE = "PRE_EVENT"
BOUNDARY_DURING = "DURING_EVENT"
BOUNDARY_POST = "POST_EVENT"
BOUNDARY_CROSSING = "BOUNDARY_CROSSING"
BOUNDARY_UNKNOWN = "UNKNOWN_TIMING"

PRE_EVENT_POLICIES = ("exclude", "label_normal")
LABEL_MODES = ("row_level", "file_level")


@dataclass(frozen=True)
class WindowConfig:
    window_s: float
    stride_s: float
    min_samples: int
    label_mode: str  # "row_level" | "file_level"
    pre_event_policy: str  # "exclude" | "label_normal"  (DECISION REQUIRED: Yazan + Faisal)

    def __post_init__(self) -> None:
        if not (self.window_s > 0 and self.stride_s > 0):
            raise ValueError("window_s and stride_s must be positive")
        if self.min_samples < 2:
            raise ValueError("min_samples must be >= 2 (slope/diff features need two samples)")
        if self.label_mode not in LABEL_MODES:
            raise ValueError(f"label_mode must be one of {LABEL_MODES}")
        if self.pre_event_policy not in PRE_EVENT_POLICIES:
            raise ValueError(f"pre_event_policy must be one of {PRE_EVENT_POLICIES}")


def map_rows_to_primary(df: pd.DataFrame) -> np.ndarray:
    """Map row-level binary label columns to the primary 4-class target.

    Interpretation of 01_dataset_audit/class_mapping.yaml (PENDING Yazan confirmation,
    because the YAML NORMAL rule "label_anomaly == 0 or all fault columns == 0" is not
    mutually exclusive with the fault rules as written):
      * exactly one of Leak / CompressorFault / CompressorDelay == 1 -> that class
      * more than one fault indicator == 1 -> COMPOUND_EVENT (excluded from primary)
      * no fault indicator but label_anomaly == 1 -> ANOMALY_WITHOUT_TYPE (excluded)
      * no fault indicator and label_anomaly == 0 -> NORMAL
    Location columns (leak_G3..G6) are not used: the primary target does not localise.
    """
    needed = ["Leak", "CompressorFault", "CompressorDelay"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"row-level label columns missing: {missing}")
    leak = df["Leak"].to_numpy() == 1
    cf = df["CompressorFault"].to_numpy() == 1
    cd = df["CompressorDelay"].to_numpy() == 1
    anom = df["label_anomaly"].to_numpy() == 1 if "label_anomaly" in df.columns else np.zeros(len(df), bool)
    n_fault = leak.astype(int) + cf.astype(int) + cd.astype(int)
    out = np.full(len(df), "NORMAL", dtype=object)
    out[anom & (n_fault == 0)] = ROW_ANOMALY_UNTYPED
    out[(n_fault == 1) & leak] = "LEAK"
    out[(n_fault == 1) & cf] = "COMPRESSOR_FAULT"
    out[(n_fault == 1) & cd] = "COMPRESSOR_DELAY"
    out[n_fault > 1] = ROW_COMPOUND
    return out


def _window_starts(t: np.ndarray, window_s: float, stride_s: float) -> np.ndarray:
    if len(t) < 2:
        return np.array([], dtype=float)
    dt_med = float(np.median(np.diff(t)))
    t_end_excl = float(t[-1]) + dt_med  # the last sample covers one sampling interval
    span = t_end_excl - float(t[0])
    if span < window_s:
        return np.array([], dtype=float)
    n = int(np.floor((span - window_s) / stride_s + 1e-9)) + 1
    return float(t[0]) + stride_s * np.arange(n, dtype=float)


def generate_windows(
    df: pd.DataFrame,
    time_axis: TimeAxis,
    scenario: Dict[str, object],
    config: WindowConfig,
    invalid_intervals: Sequence[tuple] = (),
) -> pd.DataFrame:
    """Generate the window manifest for ONE scenario frame.

    ``scenario`` must contain: file, Scenario_ID, Scenario_Family_ID, label_raw,
    label_mapped (scenario-level), phase, topology, eligible_primary.
    """
    required = ["file", "Scenario_ID", "Scenario_Family_ID", "label_raw", "label_mapped",
                "phase", "topology", "eligible_primary"]
    miss = [k for k in required if k not in scenario]
    if miss:
        raise KeyError(f"scenario metadata missing keys: {miss}")
    t = np.asarray(time_axis.t, dtype=float)
    if len(t) != len(df):
        raise ValueError("time axis length differs from frame length")
    if len(t) >= 2 and not np.all(np.diff(t) > 0):
        raise ValueError("time axis must be strictly increasing; repair is not performed here")

    invalid = np.zeros(len(df), dtype=bool)
    for a, b in invalid_intervals:
        invalid[int(a): int(b) + 1] = True

    row_labels = map_rows_to_primary(df) if config.label_mode == "row_level" else None
    scen_label = str(scenario["label_mapped"])
    event_rows = None
    if row_labels is not None:
        event_rows = np.flatnonzero(row_labels != "NORMAL")

    starts = _window_starts(t, config.window_s, config.stride_s)
    if len(starts) > 10000:
        raise ValueError("more than 9999 windows: contract window_id format {:04d} would overflow")

    recs: List[Dict[str, object]] = []
    for j, s in enumerate(starts):
        e = s + config.window_s
        lo = int(np.searchsorted(t, s, side="left"))
        hi = int(np.searchsorted(t, e, side="left"))  # rows in [s, e)
        n = hi - lo
        reasons: List[str] = []
        if n < config.min_samples:
            reasons.append("INSUFFICIENT_SAMPLES")
        if n > 0 and invalid[lo:hi].any():
            reasons.append("INVALID_VALUES_IN_WINDOW")

        if row_labels is None:
            label = scen_label
            boundary = BOUNDARY_UNKNOWN if scen_label != "NORMAL" else BOUNDARY_NO_EVENT
        else:
            labs = set(row_labels[lo:hi].tolist()) if n > 0 else set()
            if len(labs) != 1:
                label, boundary = "MIXED", BOUNDARY_CROSSING
                reasons.append("BOUNDARY_CROSSING")
            else:
                label = labs.pop()
                if event_rows is None or event_rows.size == 0:
                    boundary = BOUNDARY_NO_EVENT
                elif label == "NORMAL":
                    boundary = BOUNDARY_PRE if hi <= int(event_rows[0]) else BOUNDARY_POST
                    if config.pre_event_policy == "exclude":
                        reasons.append(f"{boundary}_NORMAL_EXCLUDED_BY_POLICY")
                else:
                    boundary = BOUNDARY_DURING
            if label in (ROW_COMPOUND, ROW_ANOMALY_UNTYPED):
                reasons.append(label)

        if not bool(scenario["eligible_primary"]):
            reasons.append("SCENARIO_NOT_ELIGIBLE_PRIMARY")
        if label not in PRIMARY_CLASSES and "BOUNDARY_CROSSING" not in reasons:
            reasons.append("LABEL_NOT_IN_PRIMARY_TARGET")

        recs.append({
            "window_id": f"{scenario['Scenario_ID']}_w{j:04d}",
            "file_id": scenario["file"],
            "Scenario_ID": scenario["Scenario_ID"],
            "Scenario_Family_ID": scenario["Scenario_Family_ID"],
            "start_time": float(s),
            "end_time": float(e),
            "start_row": lo,
            "end_row_exclusive": hi,
            "n_samples": n,
            "label_raw": scenario["label_raw"],
            "label_mapped": label,
            "phase": scenario["phase"],
            "topology": scenario["topology"],
            "boundary_status": boundary,
            "label_mode": config.label_mode,
            "time_source": time_axis.source,
            "eligible_primary": not reasons,
            "exclusion_reason": ";".join(reasons),
        })
    cols = ["window_id", "file_id", "Scenario_ID", "Scenario_Family_ID", "start_time", "end_time",
            "start_row", "end_row_exclusive", "n_samples", "label_raw", "label_mapped", "phase",
            "topology", "boundary_status", "label_mode", "time_source", "eligible_primary",
            "exclusion_reason"]
    return pd.DataFrame(recs, columns=cols)


def check_window_manifest(manifest: pd.DataFrame) -> List[str]:
    """Structural assertions on a (possibly multi-scenario) window manifest.

    Returns a list of violations (empty == pass). Checks: unique window_id, each
    window maps to exactly one scenario and family, and no window row range overlaps
    another scenario (windows are per-scenario by construction).
    """
    problems: List[str] = []
    if manifest["window_id"].duplicated().any():
        problems.append("duplicate window_id values")
    per_w = manifest.groupby("window_id")[["Scenario_ID", "Scenario_Family_ID"]].nunique()
    if (per_w > 1).any().any():
        problems.append("a window maps to more than one scenario/family")
    fam_per_scen = manifest.groupby("Scenario_ID")["Scenario_Family_ID"].nunique()
    if (fam_per_scen > 1).any():
        problems.append("a scenario maps to more than one family")
    files_per_scen = manifest.groupby("Scenario_ID")["file_id"].nunique()
    if (files_per_scen > 1).any():
        problems.append("a Scenario_ID has windows from more than one file (duplicate exports would be double-counted)")
    return problems
