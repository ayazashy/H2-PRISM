"""
H2-PRISM manifest-driven window and feature table builder (F3 completion; Phase 6).

STATUS: IMPLEMENTED + TESTED (synthetic). Every decision-bearing parameter is a REQUIRED
argument (realization, family column, window configuration, statistics): nothing defaults
to a choice that still needs human sign-off (F-D01, Y-D04, F-D04, F-D05, F-D06).
One run contributes exactly one realization; windows never cross runs; metadata never
become features. Output is deterministic (sorted runs, stable window IDs, content hash).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Sequence

import pandas as pd

from .features import extract_features, feature_register, table_sha256
from .io import SENSOR_CHANNELS, build_time_axis, find_invalid_intervals, read_table, validate_scenario_frame
from .windows import WindowConfig, check_window_manifest, generate_windows

REALIZATION_COLUMNS = {"clean": "canonical_clean_file", "noise_added": "canonical_noise_added_file"}

# Phase 8 fix: manifest v0.2 (tools/dataset/build_manifest_v02.py) uses different column names than the
# Phase-3 candidate manifest this builder was first written against. Map v0.2 names explicitly.
V02_TO_INTERNAL = {"label_mapped": "candidate_primary_class", "eligible_primary": "eligible_primary_candidate",
                   "file_noise_added": "canonical_noise_added_file", "file_clean": "canonical_clean_file",
                   "raw_label_columns": "raw_active_label_columns"}


def normalize_manifest_columns(manifest: pd.DataFrame) -> pd.DataFrame:
    """Accept both manifest schemas; refuse an ambiguous mix of old and new names."""
    clash = [new for old, new in V02_TO_INTERNAL.items() if old in manifest.columns and new in manifest.columns]
    if clash:
        raise ValueError(f"manifest has both v0.2 and Phase-3 names for {clash}")
    return manifest.rename(columns={k: v for k, v in V02_TO_INTERNAL.items() if k in manifest.columns})


def build_feature_table(manifest: pd.DataFrame, raw_parent: Path, realization: str, family_column: str,
                        window_config: WindowConfig, statistics: Sequence[str],
                        channels: Sequence[str] = SENSOR_CHANNELS) -> Dict[str, object]:
    manifest = normalize_manifest_columns(manifest)
    if realization not in REALIZATION_COLUMNS:
        raise ValueError(f"realization must be one of {sorted(REALIZATION_COLUMNS)}")
    col = REALIZATION_COLUMNS[realization]
    need = ["Scenario_ID", "topology", "candidate_primary_class", "eligible_primary_candidate", col, family_column]
    miss = [c for c in need if c not in manifest.columns]
    if miss:
        raise KeyError(f"manifest missing columns: {miss}")
    wms, fts, problems = [], [], []
    for _, r in manifest.sort_values("Scenario_ID", kind="mergesort").iterrows():
        if not bool(r["eligible_primary_candidate"]):
            continue
        f = r[col]
        if not isinstance(f, str) or not f:
            raise ValueError(f"{r['Scenario_ID']}: no {realization} realization file")
        df = read_table(Path(raw_parent) / f)
        ax = build_time_axis(df, time_col="Timestamp")
        rep = validate_scenario_frame(df, channels, ax)
        if not rep.ok:
            raise ValueError(f"{r['Scenario_ID']}: validation failed: {rep.errors}")
        scen = {"file": f, "Scenario_ID": r["Scenario_ID"], "Scenario_Family_ID": r[family_column],
                "label_raw": str(r.get("raw_active_label_columns", "")), "label_mapped": r["candidate_primary_class"],
                "phase": "NOT_AUTHORITATIVE", "topology": r["topology"], "eligible_primary": True}
        wm = generate_windows(df, ax, scen, window_config, find_invalid_intervals(df, channels))
        wms.append(wm)
        fts.append(extract_features(df, ax, wm, list(channels), list(statistics)))
    window_manifest = pd.concat(wms, ignore_index=True)
    features = pd.concat(fts, ignore_index=True)
    problems = check_window_manifest(window_manifest)
    if problems:
        raise AssertionError(f"window manifest invalid: {problems}")
    features = features.merge(window_manifest[["window_id", "topology"]], on="window_id", how="left")
    features = features[["window_id", "Scenario_ID", "Scenario_Family_ID", "topology", "label_mapped"]
                        + [c for c in features.columns if "__" in c]]
    return {"window_manifest": window_manifest, "features": features,
            "register": feature_register(channels, statistics),
            "feature_table_sha256": table_sha256(features), "window_manifest_sha256": table_sha256(window_manifest),
            "realization": realization, "family_column": family_column}
