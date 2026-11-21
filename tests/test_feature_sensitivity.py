"""Tests for A15 feature-sensitivity arms. SYNTHETIC fixtures only."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from h2prism.baseline import GroupedRunConfig, make_random_forest
from h2prism.experiments.feature_sensitivity import resolve_arm, run_sensitivity
from synthetic_fixtures import CLASSES, family_round_robin_folds, toy_feature_table

ROOT = Path(__file__).resolve().parents[1]


def _table():
    t = toy_feature_table(n_features=2)
    t["X0__slope"] = t["X0__mean"] * 0.1
    t["X1__range"] = t["X1__mean"].abs()
    return t


def test_arm_resolution_rules():
    t = _table()
    assert resolve_arm(t, {"rule": "offset_invariant"}) == ["X0__slope", "X1__range"]
    assert resolve_arm(t, {"rule": "explicit", "channels": ["X0"]}) == ["X0__mean", "X0__slope"]
    assert "Scenario_Family_ID" not in resolve_arm(t, {"rule": "all"})
    with pytest.raises(ValueError):
        resolve_arm(t, {"rule": "best_on_test"})


def test_config_arms_are_prespecified():
    cfg = yaml.safe_load((ROOT / "configs" / "feature_sensitivity.yaml").read_text(encoding="utf-8"))
    assert cfg["status"] != "FROZEN"
    assert {a["rule"] for a in cfg["arms"]} <= {"all", "offset_invariant", "explicit"}


def test_run_same_folds_and_reports_infeasible_arm():
    t = _table()
    folds = family_round_robin_folds(t, 3)
    base = GroupedRunConfig(classes=CLASSES, param_grid=[{"n_estimators": 15, "min_samples_leaf": 1,
                                                          "max_features": "sqrt"}],
                            inner_n_splits=2, seed=0, model_name="rf")
    arms = [{"name": "all", "rule": "all"}, {"name": "trend", "rule": "offset_invariant"},
            {"name": "none", "rule": "explicit", "channels": ["NOT_A_CHANNEL"]}]
    out = run_sensitivity(t, folds, arms, make_random_forest, base)
    man = out["arm_manifest"].set_index("arm")
    assert man.loc["none", "status"] == "NOT_SUPPORTED"
    assert man.loc["all", "status"] == "EXECUTED_EXPLORATORY"
    p = out["predictions"]
    rows_per_arm = p.groupby("arm")["window_id"].apply(lambda s: tuple(sorted(s)))
    assert rows_per_arm["all"] == rows_per_arm["trend"]  # identical evaluation population
    assert set(p["run_status"]) == {"EXPLORATORY_SECONDARY"}
    a2 = run_sensitivity(t, folds, arms, make_random_forest, base)
    pd.testing.assert_frame_equal(out["family_results"], a2["family_results"])
