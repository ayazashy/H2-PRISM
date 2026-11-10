"""Tests for the A14 secondary Logistic Regression reference. SYNTHETIC fixtures only."""

from pathlib import Path

import numpy as np
import pytest

from h2prism.secondary_baseline import load_config, make_logistic_regression, run_secondary_baseline
from synthetic_fixtures import family_round_robin_folds, toy_feature_table

ROOT = Path(__file__).resolve().parents[1]
FEATS = [f"X{j}__mean" for j in range(4)]


def _cfg():
    c = load_config(ROOT / "configs" / "secondary_baseline.yaml")
    c["C_grid"] = [0.1, 1.0]
    c["inner_n_splits"] = 2
    return c


def test_config_is_bounded_and_not_frozen():
    c = load_config(ROOT / "configs" / "secondary_baseline.yaml")
    assert c["status"] != "FROZEN" and 0 < len(c["C_grid"]) <= 10


def test_scaler_fit_on_training_rows_only():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(40, 2))
    y = np.array(["A", "B"] * 20)
    pipe = make_logistic_regression({"C": 1.0}, seed=0).fit(X[:20], y[:20])
    assert np.allclose(pipe.named_steps["scale"].mean_, X[:20].mean(axis=0))


def test_schema_compatible_with_primary_and_deterministic():
    t = toy_feature_table()
    folds = family_round_robin_folds(t, 3)
    a = run_secondary_baseline(t, FEATS, folds, _cfg())
    b = run_secondary_baseline(t, FEATS, folds, _cfg())
    p = a["predictions"]
    assert p.equals(b["predictions"])
    assert set(p["model_name"]) == {"logistic_regression_secondary"}
    assert {"outer_fold", "Scenario_Family_ID", "p_raw_NORMAL", "y_true", "y_pred"} <= set(p.columns)


def test_feature_order_invariance_of_predictions():
    t = toy_feature_table()
    folds = family_round_robin_folds(t, 3)
    a = run_secondary_baseline(t, FEATS, folds, _cfg())["predictions"]
    b = run_secondary_baseline(t, list(reversed(FEATS)), folds, _cfg())["predictions"]
    assert (a["y_pred"] == b["y_pred"]).mean() > 0.99


def test_leakage_refused():
    t = toy_feature_table()
    from h2prism.baseline import OuterFold
    s = sorted(t["Scenario_ID"].unique())
    with pytest.raises(AssertionError):
        run_secondary_baseline(t, FEATS, [OuterFold(1, s[:-1], [s[-2]])], _cfg())
