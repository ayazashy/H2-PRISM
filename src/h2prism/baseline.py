"""
H2-PRISM grouped nested evaluation runner and primary Random Forest factory
(Task F5 -- preparation, Faisal ownership). Shared by A14 (secondary baseline) and
A15 (feature sensitivity) so that no second pipeline exists.

STATUS: IMPLEMENTED + TESTED on a synthetic multi-family fixture. NOT executed on
project data: there is no frozen feature table, and the current folds.csv fails the
family-disjointness assertion this runner enforces (see SCIENTIFIC_AND_TECHNICAL_ISSUES.md).
All outputs carry ``run_status`` (default DEVELOPMENT_ONLY) and must never be reported
as primary results before the F4 freeze.

Procedure per outer fold (Faisal plan F5 steps 43-48):
  1. hard assertion: no independence group (default Scenario_Family_ID) in train and test
  2. inner grouped K-fold on outer-train groups -> inner OOF probabilities per setting
  3. select setting by macro-F1 (tie -> lower log loss -> grid order); outer test unused
  4. refit selected setting on all outer-train rows; predict outer-test rows
  5. emit raw probabilities aligned to the global class list (absent classes -> 0 and
     recorded in ``missing_train_classes``)
"""

from __future__ import annotations

import itertools
import json
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

from .features import assert_no_metadata_features
from .metrics import log_loss
from .splits import assert_group_disjoint, inner_group_splits

EstimatorFactory = Callable[[Dict[str, object], int], object]


@dataclass
class OuterFold:
    fold_id: object
    train_scenarios: Sequence[str]
    test_scenarios: Sequence[str]


@dataclass
class GroupedRunConfig:
    classes: List[str]
    param_grid: List[Dict[str, object]]
    inner_n_splits: int
    seed: int
    model_name: str
    independence_col: str = "Scenario_Family_ID"
    run_status: str = "DEVELOPMENT_ONLY"
    notes: Dict[str, str] = field(default_factory=dict)


def rf_param_grid() -> List[Dict[str, object]]:
    """The fixed RF search space stated in the Faisal plan (F5)."""
    grid = itertools.product([300, 500], [1, 5], ["sqrt", 0.3])
    return [{"n_estimators": a, "min_samples_leaf": b, "max_features": c} for a, b, c in grid]


def make_random_forest(params: Dict[str, object], seed: int) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=int(params["n_estimators"]),
        min_samples_leaf=int(params["min_samples_leaf"]),
        max_features=params["max_features"],
        class_weight="balanced_subsample",
        random_state=seed,
        n_jobs=1,
    )


def _aligned_proba(est, X, classes: Sequence[str]) -> np.ndarray:
    raw = est.predict_proba(X)
    est_classes = list(getattr(est, "classes_", []))
    out = np.zeros((len(X), len(classes)))
    for j, c in enumerate(est_classes):
        out[:, list(classes).index(c)] = raw[:, j]
    return out


def select_on_development(Xtr: np.ndarray, ytr: np.ndarray, gtr: np.ndarray, factory: EstimatorFactory,
                          config: "GroupedRunConfig"):
    """Development-only grid selection (shared by run_grouped_evaluation and the primary runner).

    Inner grouped K-fold over ``gtr``; each setting gets out-of-fold probabilities; selection by
    macro-F1 over present classes, tie -> lower log loss -> grid order. Uses training rows only.
    Returns (best_index, best_params, best_oof_probabilities, selection_rows).
    """
    splits, warns = inner_group_splits(gtr, ytr, config.inner_n_splits, required_classes=config.classes)
    rows, best = [], None
    yidx = np.array([config.classes.index(v) for v in ytr])
    present = sorted(set(ytr.tolist()))
    for pi, params in enumerate(config.param_grid):
        oof = np.zeros((len(ytr), len(config.classes)))
        for itr, ite in splits:
            est = factory(params, config.seed)
            est.fit(Xtr[itr], ytr[itr])
            oof[ite] = _aligned_proba(est, Xtr[ite], config.classes)
        ypred = np.array(config.classes, dtype=object)[oof.argmax(axis=1)]
        mf1 = float(f1_score(ytr, ypred, labels=present, average="macro", zero_division=0))
        ll = log_loss(oof, yidx)
        rows.append({"param_index": pi, "params": json.dumps(params, sort_keys=True), "inner_macro_f1": mf1,
                     "inner_log_loss": ll, "inner_warnings": " | ".join(warns)})
        key = (-mf1, ll, pi)
        if best is None or key < best[0]:
            best = (key, pi, params, oof)
    _, best_pi, best_params, best_oof = best
    for r in rows:
        r["selected"] = r["param_index"] == best_pi
    return best_pi, best_params, best_oof, rows


def outer_folds_from_table(folds: pd.DataFrame, fold_col: str = "outer_fold_id",
                           role_col: str = "split_role") -> List[OuterFold]:
    """Build OuterFold objects from a folds.csv-style table (roles train/test)."""
    out = []
    for k, d in folds.groupby(fold_col, sort=True):
        out.append(OuterFold(k, sorted(set(d.loc[d[role_col] == "train", "Scenario_ID"])),
                             sorted(set(d.loc[d[role_col] == "test", "Scenario_ID"]))))
    return out


def run_grouped_evaluation(
    table: pd.DataFrame,
    feature_cols: Sequence[str],
    outer_folds: Sequence[OuterFold],
    factory: EstimatorFactory,
    config: GroupedRunConfig,
    label_col: str = "label_mapped",
) -> Dict[str, pd.DataFrame]:
    assert_no_metadata_features(feature_cols)
    need = ["window_id", "Scenario_ID", config.independence_col, label_col]
    miss = [c for c in need if c not in table.columns]
    if miss:
        raise KeyError(f"table missing columns: {miss}")
    unknown = set(table[label_col]) - set(config.classes)
    if unknown:
        raise ValueError(f"labels outside class list: {sorted(map(str, unknown))}")
    X_all = table[list(feature_cols)].to_numpy(dtype=float)
    if not np.isfinite(X_all).all():
        raise ValueError("feature table contains non-finite values")

    preds, sel_rows, inner_rows = [], [], []
    for fold in outer_folds:
        tr_mask = table["Scenario_ID"].isin(fold.train_scenarios).to_numpy()
        te_mask = table["Scenario_ID"].isin(fold.test_scenarios).to_numpy()
        if (tr_mask & te_mask).any():
            raise AssertionError("LEAKAGE: a row is both train and test")
        assert_group_disjoint(table.loc[tr_mask, config.independence_col],
                              table.loc[te_mask, config.independence_col], config.independence_col)
        tr = table[tr_mask]
        te = table[te_mask]
        Xtr, ytr, gtr = X_all[tr_mask], tr[label_col].to_numpy(), tr[config.independence_col].to_numpy()
        missing_train = sorted(set(config.classes) - set(ytr.tolist()))
        best_pi, best_params, best_oof, rows = select_on_development(Xtr, ytr, gtr, factory, config)
        for r in rows:
            r["outer_fold"] = fold.fold_id
        sel_rows += rows

        inner = tr[["window_id", "Scenario_ID", config.independence_col]].copy()
        inner["outer_fold"] = fold.fold_id
        inner["y_true"] = ytr
        for j, c in enumerate(config.classes):
            inner[f"p_raw_{c}"] = best_oof[:, j]
        inner_rows.append(inner)

        est = factory(best_params, config.seed)
        est.fit(Xtr, ytr)
        P = _aligned_proba(est, X_all[te_mask], config.classes)
        out = te[["window_id", "Scenario_ID", config.independence_col]].copy()
        out["outer_fold"] = fold.fold_id
        out["y_true"] = te[label_col].to_numpy()
        out["y_pred"] = np.array(config.classes, dtype=object)[P.argmax(axis=1)]
        for j, c in enumerate(config.classes):
            out[f"p_raw_{c}"] = P[:, j]
        out["model_name"] = config.model_name
        out["params"] = json.dumps(best_params, sort_keys=True)
        out["seed"] = config.seed
        out["missing_train_classes"] = ";".join(missing_train)
        out["run_status"] = config.run_status
        preds.append(out)

    return {
        "predictions": pd.concat(preds, ignore_index=True) if preds else pd.DataFrame(),
        "selection": pd.DataFrame(sel_rows),
        "inner_oof": pd.concat(inner_rows, ignore_index=True) if inner_rows else pd.DataFrame(),
    }
