"""
Schema-level compatibility of the candidate manifest with the F3 pipeline on REAL files.
No model is trained, no threshold is selected, no metric is computed: only loading,
validation, windowing and feature extraction of single scenarios (interface checks).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from h2prism.features import assert_no_metadata_features, extract_features, feature_register, model_feature_columns
from h2prism.io import SENSOR_CHANNELS, TIME_SOURCE_INDEX, build_time_axis, find_invalid_intervals, read_table, validate_scenario_frame
from h2prism.windows import WindowConfig, check_window_manifest, generate_windows

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PKG = ROOT / "06_audit_preparation" / "pre_experiment_review"
pytestmark = pytest.mark.skipif(not (RAW / "H2-SimNet-Dataset").exists() or not (PKG / "CANDIDATE_SCENARIO_MANIFEST.csv").exists(),
                                reason="raw dataset or candidate manifest absent")
CFG = WindowConfig(window_s=60, stride_s=30, min_samples=60, label_mode="row_level", pre_event_policy="exclude")  # interface test values only


def _scenario(row):
    return {"file": row.canonical_clean_file, "Scenario_ID": row.Scenario_ID, "Scenario_Family_ID": row.family_primary,
            "label_raw": row.raw_active_label_columns if isinstance(row.raw_active_label_columns, str) else "",
            "label_mapped": row.candidate_primary_class, "phase": "NOT_AUTHORITATIVE", "topology": row.topology,
            "eligible_primary": bool(row.eligible_primary_candidate)}


@pytest.mark.parametrize("stem", ["leakG4_weak", "startdelayC1", "normality", "brokenC1G5_weak"])
def test_manifest_to_windows_to_features(stem):
    man = pd.read_csv(PKG / "CANDIDATE_SCENARIO_MANIFEST.csv")
    row = man[man.run_stem == stem].sort_values("Scenario_ID").iloc[0]
    df = read_table(RAW / row.canonical_clean_file)
    ax = build_time_axis(df, time_col="Timestamp")
    assert ax.source == TIME_SOURCE_INDEX and np.allclose(np.diff(ax.t), 1.0)
    rep = validate_scenario_frame(df, SENSOR_CHANNELS, ax)
    assert rep.ok and not rep.invalid_intervals
    wm = generate_windows(df, ax, _scenario(row), CFG, find_invalid_intervals(df, SENSOR_CHANNELS))
    assert check_window_manifest(wm) == []
    assert wm.window_id.str.startswith(row.Scenario_ID).all()
    if stem == "startdelayC1":  # label active 25-1000 s: during-event windows exist, post-event excluded by policy
        assert set(wm.loc[wm.eligible_primary, "label_mapped"]) == {"COMPRESSOR_DELAY"}
        assert wm.exclusion_reason.str.contains("POST_EVENT").any()
    if stem == "brokenC1G5_weak":  # scenario excluded pending review: no eligible windows
        assert not wm.eligible_primary.any()
    if stem == "normality":
        assert wm.eligible_primary.all()
    ft = extract_features(df, ax, wm, list(SENSOR_CHANNELS), ["mean", "std", "slope", "last_minus_first"])
    cols = model_feature_columns(ft)
    assert_no_metadata_features(cols)
    assert len(cols) == 64 and len(ft) == int(wm.eligible_primary.sum())
    assert set(feature_register(SENSOR_CHANNELS, ["mean", "std", "slope", "last_minus_first"]).feature_name) == set(cols)
