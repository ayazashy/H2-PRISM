"""Tests for the grouped runner, RF factory and calibration (F5/F6). SYNTHETIC fixtures only."""

import numpy as np
import pytest

from h2prism.baseline import (GroupedRunConfig, OuterFold, make_random_forest, rf_param_grid,
                              run_grouped_evaluation)
from h2prism.calibration import fit_calibrator, select_calibration
from synthetic_fixtures import CLASSES, family_round_robin_folds, toy_feature_table

FEATS = [f"X{j}__mean" for j in range(4)]
SMALL_GRID = [{"n_estimators": 20, "min_samples_leaf": 1, "max_features": "sqrt"},
              {"n_estimators": 20, "min_samples_leaf": 5, "max_features": 0.3}]


def _cfg(**kw):
    base = dict(classes=CLASSES, param_grid=SMALL_GRID, inner_n_splits=2, seed=0, model_name="rf_test")
    base.update(kw)
    return GroupedRunConfig(**base)


def test_rf_grid_matches_plan():
    g = rf_param_grid()
    assert len(g) == 8
    assert {p["n_estimators"] for p in g} == {300, 500} and {p["max_features"] for p in g} == {"sqrt", 0.3}
    rf = make_random_forest(g[0], seed=1)
    assert rf.class_weight == "balanced_subsample" and rf.random_state == 1


def test_grouped_run_outputs_schema_and_is_deterministic():
    t = toy_feature_table()
    folds = family_round_robin_folds(t, 3)
    a = run_grouped_evaluation(t, FEATS, folds, make_random_forest, _cfg())
    b = run_grouped_evaluation(t, FEATS, folds, make_random_forest, _cfg())
    p = a["predictions"]
    for c in ["window_id", "Scenario_ID", "Scenario_Family_ID", "outer_fold", "y_true", "y_pred",
              *[f"p_raw_{c}" for c in CLASSES], "run_status"]:
        assert c in p.columns
    assert np.allclose(p[[f"p_raw_{c}" for c in CLASSES]].sum(axis=1), 1.0)
    assert set(p["run_status"]) == {"DEVELOPMENT_ONLY"}
    assert p.equals(b["predictions"])
    assert len(p) == len(t)  # every window predicted exactly once across outer folds
    assert a["selection"].groupby("outer_fold")["selected"].sum().eq(1).all()


def test_runner_refuses_family_leakage():
    t = toy_feature_table()
    scen = sorted(t["Scenario_ID"].unique())
    fam_of = dict(zip(t["Scenario_ID"], t["Scenario_Family_ID"]))
    # put the two scenarios of one family on opposite sides
    s0 = [s for s in scen if fam_of[s] == fam_of[scen[0]]]
    bad = OuterFold(1, [s0[0]] + [s for s in scen if fam_of[s] != fam_of[scen[0]]][:10], [s0[1]])
    with pytest.raises(AssertionError, match="LEAKAGE"):
        run_grouped_evaluation(t, FEATS, [bad], make_random_forest, _cfg())


def test_runner_refuses_metadata_features():
    t = toy_feature_table()
    with pytest.raises(ValueError):
        run_grouped_evaluation(t, FEATS + ["Scenario_Family_ID"], family_round_robin_folds(t), make_random_forest, _cfg())


def test_outer_test_rows_do_not_influence_selection():
    t = toy_feature_table()
    folds = family_round_robin_folds(t, 3)
    a = run_grouped_evaluation(t, FEATS, folds[:1], make_random_forest, _cfg())
    t2 = t.copy()
    test_mask = t2["Scenario_ID"].isin(folds[0].test_scenarios)
    t2.loc[test_mask, FEATS] = t2.loc[test_mask, FEATS] * -50  # perturb outer-test features only
    b = run_grouped_evaluation(t2, FEATS, folds[:1], make_random_forest, _cfg())
    assert a["selection"].equals(b["selection"])
    assert a["inner_oof"].equals(b["inner_oof"])


def test_missing_training_class_is_recorded():
    t = toy_feature_table()
    folds = family_round_robin_folds(t, 3)
    t2 = t[~((t["label_mapped"] == "COMPRESSOR_DELAY") & t["Scenario_ID"].isin(folds[0].train_scenarios))]
    out = run_grouped_evaluation(t2, FEATS, folds[:1], make_random_forest, _cfg())
    assert set(out["predictions"]["missing_train_classes"]) == {"COMPRESSOR_DELAY"}
    assert (out["predictions"]["p_raw_COMPRESSOR_DELAY"] == 0).all()


def test_calibration_selection_keeps_none_unless_better():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 300)
    P = np.full((300, 3), 0.05)
    P[np.arange(300), y] = 0.9  # already well-separated, near-calibrated
    groups = np.repeat(np.arange(30), 10)
    res = select_calibration(P / P.sum(1, keepdims=True), y, groups, 3, n_splits=3)
    assert res["selected_method"] in ("none", "sigmoid", "isotonic")
    assert set(res["table"]["method"]) == {"none", "sigmoid", "isotonic"}
    tbl = res["table"].set_index("method")
    if res["selected_method"] != "none":
        assert tbl.loc[res["selected_method"], "log_loss"] < tbl.loc["none", "log_loss"]


def test_calibrator_outputs_simplex_and_handles_absent_class():
    rng = np.random.default_rng(1)
    P = rng.dirichlet(np.ones(3), size=100)
    y = rng.integers(0, 2, 100)  # class 2 never observed
    for m in ("sigmoid", "isotonic"):
        cal = fit_calibrator(m, P, y, 3)
        Q = cal.transform(P)
        assert np.allclose(Q.sum(axis=1), 1.0) and 2 in cal.raw_classes
