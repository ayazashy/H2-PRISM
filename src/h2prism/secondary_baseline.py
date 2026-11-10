"""
H2-PRISM secondary Logistic Regression reference model (Task A14 -- Ahmed).

STATUS: IMPLEMENTED + TESTED (synthetic). Reuses the shared grouped runner in
baseline.py, so folds, inner selection, leakage assertions and the prediction schema
are identical to the primary Random Forest (F5). It does not replace F5 and no
superiority claim may be derived from it. Requires Faisal technical acceptance
(Ahmed plan A14 acceptance; Faisal plan F5 handoff).

Training-fold-only preprocessing: StandardScaler is inside the sklearn Pipeline, so
it is refit on each (inner or outer) training split and never sees held-out rows.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

import yaml
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .baseline import GroupedRunConfig, OuterFold, run_grouped_evaluation


def make_logistic_regression(params: Dict[str, object], seed: int) -> Pipeline:
    return Pipeline([
        ("scale", StandardScaler()),
        ("lr", LogisticRegression(
            C=float(params["C"]),
            class_weight=params.get("class_weight", "balanced"),
            max_iter=int(params.get("max_iter", 2000)),
            random_state=seed,
        )),
    ])


def load_config(path: Path) -> Dict[str, object]:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key in ("classes", "C_grid", "inner_n_splits", "seed", "status"):
        if key not in cfg:
            raise KeyError(f"secondary baseline config missing '{key}'")
    if len(cfg["C_grid"]) == 0:
        raise ValueError("C_grid must be non-empty and bounded (A14 step 2)")
    return cfg


def run_secondary_baseline(table, feature_cols: Sequence[str], outer_folds: Sequence[OuterFold],
                           cfg: Dict[str, object]):
    grid: List[Dict[str, object]] = [
        {"C": float(c), "class_weight": cfg.get("class_weight", "balanced"), "max_iter": cfg.get("max_iter", 2000)}
        for c in cfg["C_grid"]
    ]
    run_cfg = GroupedRunConfig(
        classes=list(cfg["classes"]),
        param_grid=grid,
        inner_n_splits=int(cfg["inner_n_splits"]),
        seed=int(cfg["seed"]),
        model_name="logistic_regression_secondary",
        run_status=str(cfg["status"]),
    )
    return run_grouped_evaluation(table, feature_cols, outer_folds, make_logistic_regression, run_cfg)
