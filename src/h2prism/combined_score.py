"""
H2-PRISM combined acceptance scores s_C and s_{C-D} (F-D10; Faisal plan F10).

    s_C(x)     = P(correct | logit C(x), M(x), -H(x), D(x))     logistic model
    s_{C-D}(x) = P(correct | logit C(x), M(x), -H(x))           same model without D

STATUS: IMPLEMENTED + TESTED (synthetic). The correctness meta-model is fitted ONLY on
development predictions with cross-fitting by independence group: every development score
is produced by a model that never saw that group (plan F10 step 83: no in-sample
correctness model). Outer-test rows are only *scored* by the model fitted on all
development rows. Rows with undefined D (invalid features / no reference) get a NaN score
for s_C, which the policy maps to UNRESOLVED (INVALID_SCORE); they are excluded from fitting
and counted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .comparators import compute_comparators, logit
from .splits import inner_group_splits

FEATURES_WITH_D = ("logit_C", "M", "neg_H", "D")
FEATURES_WITHOUT_D = ("logit_C", "M", "neg_H")


@dataclass(frozen=True)
class CombinedScoreConfig:
    include_D: bool
    n_splits: int
    seed: int
    C: float = 1.0  # fixed regularisation; not tuned (avoids a second selection loop)


def score_features(P, D: Optional[Sequence[float]], include_D: bool) -> np.ndarray:
    comp = compute_comparators(P, D if include_D else None)
    cols = [logit(comp["C"].to_numpy()), comp["M"].to_numpy(), comp["neg_H"].to_numpy()]
    if include_D:
        if D is None:
            raise ValueError("include_D=True requires D")
        cols.append(comp["D"].to_numpy(dtype=float))
    return np.column_stack(cols)


def _model(cfg: CombinedScoreConfig) -> Pipeline:
    return Pipeline([("scale", StandardScaler()),
                     ("lr", LogisticRegression(C=cfg.C, max_iter=2000, random_state=cfg.seed))])


def fit_combined_score(P_dev, correct_dev, groups_dev, cfg: CombinedScoreConfig,
                       D_dev: Optional[Sequence[float]] = None) -> Dict[str, object]:
    """Cross-fitted development scores plus a final model fitted on all usable development rows."""
    X = score_features(P_dev, D_dev, cfg.include_D)
    y = np.asarray(correct_dev, dtype=int)
    g = np.asarray(groups_dev)
    usable = np.isfinite(X).all(axis=1)
    oof = np.full(len(y), np.nan)
    warns: List[str] = []
    splits, w = inner_group_splits(g, y, cfg.n_splits, required_classes=[0, 1])
    warns += w
    for k, (tr, te) in enumerate(splits):
        tr = tr[usable[tr]]
        te_u = te[usable[te]]
        if len(set(y[tr].tolist())) < 2:
            warns.append(f"split {k}: training part has a single correctness outcome; OOF scores left NaN")
            continue
        m = _model(cfg).fit(X[tr], y[tr])
        if len(te_u):
            oof[te_u] = m.predict_proba(X[te_u])[:, 1]
    if len(set(y[usable].tolist())) < 2:
        raise ValueError("development data contain a single correctness outcome; meta-model not estimable")
    final = _model(cfg).fit(X[usable], y[usable])
    return {"model": final, "oof_scores": oof, "n_excluded_undefined": int((~usable).sum()),
            "features": FEATURES_WITH_D if cfg.include_D else FEATURES_WITHOUT_D, "warnings": warns}


def apply_combined_score(fitted: Dict[str, object], P, D: Optional[Sequence[float]], include_D: bool) -> np.ndarray:
    """Score new rows (e.g. outer test) with the development-fitted model; never refits."""
    X = score_features(P, D, include_D)
    out = np.full(len(X), np.nan)
    ok = np.isfinite(X).all(axis=1)
    if ok.any():
        out[ok] = fitted["model"].predict_proba(X[ok])[:, 1]
    return out
