"""
H2-PRISM development-only probability calibration (Task F6 -- preparation, Faisal).

STATUS: IMPLEMENTED + TESTED (synthetic). Calibration is never assumed beneficial:
``select_calibration`` compares none / sigmoid / isotonic with grouped cross-fitting
*inside the development predictions* and keeps "none" unless another method is
strictly better on the prespecified criterion. Outer-test labels are never inputs.

Multiclass handling: one-vs-rest per class, then row renormalisation. A class with no
positives (or no negatives) in the fitting data keeps its raw probability; rows whose
calibrated mass is zero fall back to the raw row. Both events are counted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

from .comparators import logit
from .metrics import log_loss, multiclass_brier
from .splits import inner_group_splits

METHODS = ("none", "sigmoid", "isotonic")


@dataclass
class Calibrator:
    method: str
    n_classes: int
    models: List[object] = field(default_factory=list)
    raw_classes: List[int] = field(default_factory=list)
    n_fallback_rows: int = 0

    def transform(self, P) -> np.ndarray:
        P = np.asarray(P, dtype=float)
        if self.method == "none":
            return P.copy()
        out = np.empty_like(P)
        for k in range(self.n_classes):
            m = self.models[k]
            if m is None:
                out[:, k] = P[:, k]
            elif self.method == "sigmoid":
                out[:, k] = m.predict_proba(logit(P[:, k]).reshape(-1, 1))[:, 1]
            else:
                out[:, k] = m.predict(P[:, k])
        s = out.sum(axis=1, keepdims=True)
        zero = s[:, 0] <= 0
        self.n_fallback_rows = int(zero.sum())
        out = np.where(zero[:, None], P, out / np.where(s > 0, s, 1.0))
        return out


def fit_calibrator(method: str, P_dev, y_dev_idx, n_classes: int) -> Calibrator:
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    P = np.asarray(P_dev, dtype=float)
    y = np.asarray(y_dev_idx, dtype=int)
    cal = Calibrator(method, n_classes)
    if method == "none":
        return cal
    for k in range(n_classes):
        t = (y == k).astype(int)
        if t.min() == t.max():
            cal.models.append(None)
            cal.raw_classes.append(k)
            continue
        if method == "sigmoid":
            m = LogisticRegression(C=1e6, max_iter=1000)
            m.fit(logit(P[:, k]).reshape(-1, 1), t)
        else:
            m = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            m.fit(P[:, k], t)
        cal.models.append(m)
    return cal


def select_calibration(P_dev, y_dev_idx, groups_dev, n_classes: int, n_splits: int,
                       criterion: str = "log_loss", methods: Sequence[str] = METHODS) -> Dict[str, object]:
    """Grouped cross-fitted comparison of calibration methods on development data only."""
    if criterion not in ("log_loss", "brier"):
        raise ValueError("criterion must be 'log_loss' or 'brier'")
    P = np.asarray(P_dev, dtype=float)
    y = np.asarray(y_dev_idx, dtype=int)
    splits, warns = inner_group_splits(groups_dev, y, n_splits)
    rows = []
    for meth in methods:
        Q = np.zeros_like(P)
        for tr, te in splits:
            Q[te] = fit_calibrator(meth, P[tr], y[tr], n_classes).transform(P[te])
        rows.append({"method": meth, "log_loss": log_loss(Q, y), "brier": multiclass_brier(Q, y)})
    table = pd.DataFrame(rows)
    base = float(table.loc[table["method"] == "none", criterion].iloc[0]) if "none" in methods else np.inf
    best = table.sort_values([criterion, "method"]).iloc[0]
    choice = best["method"] if float(best[criterion]) < base else "none"
    return {"selected_method": choice, "criterion": criterion, "table": table, "warnings": warns}
