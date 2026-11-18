"""Deterministic event-window extraction for the H2-SimNet benchmark."""

from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import numpy as np
import pandas as pd


SENSOR_CHANNELS = tuple(
    [f"PS{i}" for i in range(1, 13)] + [f"MFS{i}" for i in range(1, 5)]
)
TARGET_CLASSES = ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY")
LABEL_MAP = {
    "NORMAL": "NORMAL",
    "LEAKG3": "LEAK",
    "LEAKG4": "LEAK",
    "LEAKG5": "LEAK",
    "LEAKG6": "LEAK",
    "LEAKG3G4": "LEAK",
    "LEAKG3G5": "LEAK",
    "LEAKG3G6": "LEAK",
    "LEAKG5G6": "LEAK",
    "COMPRESSORFAULT": "COMPRESSOR_FAULT",
    "COMPRESSORDELAY": "COMPRESSOR_DELAY",
    "COMBINEDCOMPRESSORFAULTLEAKG5": "UNKNOWN",
    "COMBINEDLEAKG4COMPRESSORFAULT": "UNKNOWN",
}


def map_target_class(raw_label: str) -> str:
    """Map a frozen manifest label to the primary four-class target."""
    normalized = str(raw_label).replace("_", "").replace(" ", "").upper()
    try:
        return LABEL_MAP[normalized]
    except KeyError as exc:
        raise ValueError(f"Unrecognized primary event label: {raw_label!r}") from exc


def _as_bool(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, np.integer)):
        return bool(value)
    return str(value).strip().lower() in {"true", "1", "yes"}


def _scenario_time(data: pd.DataFrame) -> np.ndarray:
    if "Timestamp" in data.columns:
        values = pd.to_numeric(data["Timestamp"], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all() or np.any(np.diff(values) <= 0):
            raise ValueError("Timestamp must be finite and strictly increasing.")
        if len(values) > 1 and not np.allclose(np.diff(values), 1.0, atol=1e-6):
            raise ValueError("Timestamp sampling must match the audited 1 Hz rate.")
        return values
    return np.arange(len(data), dtype=float)


def _summarize_window(data: pd.DataFrame, start: int, stop: int) -> Dict[str, float]:
    result: Dict[str, float] = {}
    window = data.iloc[start:stop]
    for channel in SENSOR_CHANNELS:
        values = pd.to_numeric(window[channel], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"Non-finite sensor value in channel {channel}.")
        differences = np.diff(values)
        result[f"{channel}__mean"] = float(np.mean(values))
        result[f"{channel}__std"] = float(np.std(values))
        result[f"{channel}__q05_q95_range"] = float(
            np.quantile(values, 0.95) - np.quantile(values, 0.05)
        )
        result[f"{channel}__diff_mean"] = (
            float(np.mean(differences)) if differences.size else 0.0
        )
        result[f"{channel}__diff_std"] = (
            float(np.std(differences)) if differences.size else 0.0
        )
    return result


def build_window_dataset(
    scenarios: Iterable[Tuple[pd.Series, pd.DataFrame]],
    window_size: int = 60,
    stride: int = 60,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return a window manifest and sensor-only feature table.

    Anomaly windows are eligible only when fully inside the manifest's annotated
    event interval. Normal scenarios contribute complete baseline windows.
    Pre-event, post-event, boundary-crossing, and excluded compound windows are
    recorded in the manifest but not emitted as model features.
    """
    if window_size < 2:
        raise ValueError("window_size must be at least 2 samples.")
    if stride < 1:
        raise ValueError("stride must be positive.")

    manifest_rows: List[Dict[str, object]] = []
    feature_rows: List[Dict[str, object]] = []
    for metadata, data in scenarios:
        missing = sorted(set(SENSOR_CHANNELS) - set(data.columns))
        if missing:
            raise ValueError(
                f"{metadata['Scenario_ID']} is missing sensor channels: {missing}"
            )
        if len(data) < window_size:
            raise ValueError(
                f"{metadata['Scenario_ID']} has {len(data)} samples; "
                f"at least {window_size} are required."
            )

        scenario_id = str(metadata["Scenario_ID"])
        family_id = str(metadata["Scenario_Family_ID"])
        raw_label = str(metadata["event_label_raw"])
        target_class = map_target_class(raw_label)
        primary_eligible = _as_bool(metadata["eligible_primary"])
        exclusion_reason = str(metadata.get("exclusion_reason", ""))
        if target_class not in TARGET_CLASSES:
            primary_eligible = False
            exclusion_reason = exclusion_reason or "UNSUPPORTED_PRIMARY_LABEL"
        times = _scenario_time(data)

        onset_value = pd.to_numeric(
            pd.Series([metadata.get("event_onset_s")]), errors="coerce"
        ).iloc[0]
        offset_value = pd.to_numeric(
            pd.Series([metadata.get("event_offset_s")]), errors="coerce"
        ).iloc[0]
        if target_class != "NORMAL" and (
            not np.isfinite(onset_value) or not np.isfinite(offset_value)
        ):
            primary_eligible = False
            exclusion_reason = "MISSING_EVENT_TIMING"

        last_start = ((len(data) - window_size) // stride) * stride
        tail_samples_omitted = len(data) - (last_start + window_size)
        starts = range(0, len(data) - window_size + 1, stride)
        for window_index, start in enumerate(starts):
            stop = start + window_size
            start_time = float(times[start])
            end_time = float(times[stop - 1])
            if target_class == "NORMAL":
                boundary_status = "DURING_EVENT"
                eligible = primary_eligible
                reason = exclusion_reason if not eligible else ""
            elif not primary_eligible:
                boundary_status = "DURING_EVENT"
                eligible = False
                reason = exclusion_reason or "NOT_ELIGIBLE_PRIMARY"
            elif end_time < onset_value:
                boundary_status = "PRE_EVENT"
                eligible = False
                reason = "PRE_EVENT"
            elif start_time > offset_value:
                boundary_status = "POST_EVENT"
                eligible = False
                reason = "POST_EVENT"
            elif start_time < onset_value or end_time > offset_value:
                boundary_status = "BOUNDARY_CROSSING"
                eligible = False
                reason = "BOUNDARY_CROSSING"
            else:
                boundary_status = "DURING_EVENT"
                eligible = True
                reason = ""

            window_id = f"{scenario_id}_w{window_index:04d}"
            manifest_rows.append(
                {
                    "window_id": window_id,
                    "Scenario_ID": scenario_id,
                    "Scenario_Family_ID": family_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "label_raw": raw_label,
                    "label_mapped": target_class,
                    "phase": str(metadata.get("phase", "Unknown")),
                    "topology": str(metadata.get("topology", "Unknown")),
                    "boundary_status": boundary_status,
                    "eligible_primary": bool(eligible),
                    "exclusion_reason": reason,
                    "tail_samples_omitted": tail_samples_omitted,
                }
            )
            if eligible:
                feature_rows.append(
                    {
                        "window_id": window_id,
                        "Scenario_ID": scenario_id,
                        "Scenario_Family_ID": family_id,
                        "label_mapped": target_class,
                        "topology": str(metadata.get("topology", "Unknown")),
                        **_summarize_window(data, start, stop),
                    }
                )

    manifest = pd.DataFrame(manifest_rows)
    features = pd.DataFrame(feature_rows)
    if manifest.empty:
        raise ValueError("No complete windows were generated.")
    if not features.empty and features["window_id"].duplicated().any():
        raise ValueError("Generated window IDs are not unique.")
    return manifest, features
