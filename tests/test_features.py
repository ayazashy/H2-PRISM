"""Tests for h2prism.features (F3). SYNTHETIC fixtures only."""

import numpy as np
import pandas as pd
import pytest

from h2prism.features import (assert_no_metadata_features, extract_features, feature_register,
                              model_feature_columns, table_sha256)
from h2prism.io import build_time_axis
from h2prism.windows import WindowConfig, generate_windows

SCEN = {"file": "syn/a", "Scenario_ID": "SA", "Scenario_Family_ID": "FA", "label_raw": "NORMAL",
        "label_mapped": "NORMAL", "phase": "x", "topology": "y", "eligible_primary": True}
FEATS = ["mean", "std", "min", "max", "range", "last_minus_first", "slope", "mean_abs_diff"]


def _setup(values):
    df = pd.DataFrame({"PS1": values})
    ax = build_time_axis(df, assumed_dt_s=1.0, assumption_source="synthetic")
    wm = generate_windows(df, ax, SCEN, WindowConfig(4, 4, 4, "file_level", "exclude"))
    return df, ax, wm


def test_hand_calculated_features():
    df, ax, wm = _setup([1.0, 3.0, 2.0, 6.0])
    ft = extract_features(df, ax, wm, ["PS1"], FEATS)
    r = ft.iloc[0]
    assert r["PS1__mean"] == pytest.approx(3.0)
    assert r["PS1__std"] == pytest.approx(np.std([1, 3, 2, 6]))
    assert r["PS1__range"] == pytest.approx(5.0)
    assert r["PS1__last_minus_first"] == pytest.approx(5.0)
    assert r["PS1__mean_abs_diff"] == pytest.approx((2 + 1 + 4) / 3)
    assert r["PS1__slope"] == pytest.approx(np.polyfit([0, 1, 2, 3], [1, 3, 2, 6], 1)[0])


def test_offset_invariant_features_unchanged_by_offset():
    df, ax, wm = _setup([1.0, 3.0, 2.0, 6.0])
    df2, ax2, wm2 = _setup([101.0, 103.0, 102.0, 106.0])
    a = extract_features(df, ax, wm, ["PS1"], ["std", "range", "last_minus_first", "slope", "mean_abs_diff"])
    b = extract_features(df2, ax2, wm2, ["PS1"], ["std", "range", "last_minus_first", "slope", "mean_abs_diff"])
    pd.testing.assert_frame_equal(a, b)


def test_metadata_never_model_features():
    with pytest.raises(ValueError):
        assert_no_metadata_features(["PS1__mean", "Scenario_Family_ID"])
    df, ax, wm = _setup([1.0, 2.0, 3.0, 4.0])
    ft = extract_features(df, ax, wm, ["PS1"], ["mean"])
    assert model_feature_columns(ft) == ["PS1__mean"]


def test_register_units_and_flags():
    reg = feature_register(["PS1", "MFS1"], ["mean", "slope"])
    u = dict(zip(reg["feature_name"], reg["unit"]))
    assert u["PS1__mean"] == "MPa" and u["MFS1__slope"] == "kg/s/s"
    assert set(reg["status"]) == {"SPECIFIED_CANDIDATE"}


def test_deterministic_hash():
    df, ax, wm = _setup(list(np.linspace(0, 1, 12)))
    h1 = table_sha256(extract_features(df, ax, wm, ["PS1"], FEATS))
    h2 = table_sha256(extract_features(df, ax, wm, ["PS1"], FEATS))
    assert h1 == h2 and len(h1) == 64
