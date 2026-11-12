"""
Prespecified evaluation metrics for the protocol 2.0 ablation program (one definition used by every arm).

Classifier level (window predictions):   accuracy, macro-F1, balanced accuracy, per-class recall, per-topology accuracy,
                                          INDEPENDENCE-GROUP-level accuracy (each scenario independence group weighs 1),
                                          high-confidence-error share, ECE (10 equal-width bins), multiclass Brier.
Decision level (policy decisions):       coverage, selective risk (wrong SPECIFIC / SPECIFIC), wrong-SPECIFIC count,
                                          ambiguity-set inclusion, UNRESOLVED rate - per topology and pooled.
Score level (correctness discrimination): AUROC of a score for predicting top-label correctness (rank-based, ties
                                          averaged), share of windows at the score's maximum (saturation).
Primary metric (prespecified): group-balanced selective risk at the development-fixed operating target, per topology;
secondary: the remaining metrics. All functions take explicit inputs; none reads labels it should not.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd


def classifier_metrics(y_true: Sequence[str], y_pred: Sequence[str], classes: Sequence[str]) -> Dict:
    y, p = np.asarray(y_true, dtype=object), np.asarray(y_pred, dtype=object)
    rec, f1 = {}, []
    for c in classes:
        tp = int(((y == c) & (p == c)).sum())
        fn, fp = int(((y == c) & (p != c)).sum()), int(((y != c) & (p == c)).sum())
        r = tp / (tp + fn) if tp + fn else np.nan
        pr = tp / (tp + fp) if tp + fp else np.nan
        rec[c] = r
        f1.append(2 * pr * r / (pr + r) if (tp and pr + r) else (0.0 if tp + fn else np.nan))
    present = [c for c in classes if (y == c).any()]
    return {"n": len(y), "accuracy": float((y == p).mean()) if len(y) else np.nan,
            "balanced_accuracy": float(np.nanmean([rec[c] for c in present])) if present else np.nan,
            "macro_f1": float(np.nanmean([f for c, f in zip(classes, f1) if c in present])) if present else np.nan,
            **{f"recall_{c}": rec[c] for c in classes}}


def group_level_accuracy(correct: Sequence[bool], groups: Sequence[str]) -> Dict:
    """Each independence group weighs 1 regardless of its window count (scenario-level evidence)."""
    s = pd.Series(np.asarray(correct, dtype=float)).groupby(np.asarray(groups)).mean()
    return {"n_groups": int(len(s)), "group_balanced_accuracy": float(s.mean()) if len(s) else np.nan,
            "worst_group_accuracy": float(s.min()) if len(s) else np.nan}


def ece(P: np.ndarray, y_idx: Sequence[int], n_bins: int = 10) -> float:
    P = np.asarray(P, float)
    conf, pred = P.max(1), P.argmax(1)
    ok = (pred == np.asarray(y_idx)).astype(float)
    bins = np.minimum((conf * n_bins).astype(int), n_bins - 1)
    tot = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            tot += m.mean() * abs(ok[m].mean() - conf[m].mean())
    return float(tot)


def brier(P: np.ndarray, y_idx: Sequence[int]) -> float:
    P = np.asarray(P, float)
    Y = np.zeros_like(P)
    Y[np.arange(len(P)), np.asarray(y_idx)] = 1.0
    return float(((P - Y) ** 2).sum(1).mean())


def auroc(score: Sequence[float], positive: Sequence[bool]) -> float:
    """Probability that a positive (correct) row scores above a negative one; ties count 1/2; NaN scores dropped."""
    s, y = np.asarray(score, float), np.asarray(positive, bool)
    m = np.isfinite(s)
    s, y = s[m], y[m]
    n1, n0 = int(y.sum()), int((~y).sum())
    if not n1 or not n0:
        return np.nan
    r = pd.Series(s).rank(method="average").to_numpy()
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def saturation(score: Sequence[float]) -> float:
    s = np.asarray(score, float)
    s = s[np.isfinite(s)]
    return float((s == s.max()).mean()) if len(s) else np.nan


def decision_metrics(outcome: Sequence[str], y_pred_specific: Sequence[Optional[str]], ambiguity_set: Sequence[str],
                     y_true: Sequence[str]) -> Dict:
    o = np.asarray(outcome, dtype=object)
    sp = o == "SPECIFIC"
    am = o == "AMBIGUITY_SET"
    yt = np.asarray(y_true, dtype=object)
    ypred = np.asarray(y_pred_specific, dtype=object)
    wrong = int((sp & (ypred != yt)).sum())
    inc = [str(t) in str(s).split("|") for t, s in zip(yt[am], np.asarray(ambiguity_set, dtype=object)[am])]
    return {"n": len(o), "coverage": float(sp.mean()) if len(o) else np.nan, "n_specific": int(sp.sum()),
            "n_wrong_specific": wrong, "selective_risk": wrong / int(sp.sum()) if sp.any() else np.nan,
            "ambiguity_rate": float(am.mean()) if len(o) else np.nan,
            "ambiguity_inclusion": float(np.mean(inc)) if inc else np.nan,
            "unresolved_rate": float((o == "UNRESOLVED").mean()) if len(o) else np.nan}
