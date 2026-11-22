"""
H2-PRISM shared evaluation metrics (support for F5/F6/F9/F10; shared with A14-A16).

STATUS: IMPLEMENTED + TESTED (closed-form fixtures). These functions compute metrics
from saved predictions; they never fit, tune or select anything.

Definitions (Faisal plan F10 step 89):
    loss(y_hat, y)   = 1[y_hat != y]           for accepted SPECIFIC outputs
    Coverage         = N_specific / N_eligible
    Selective risk   = N_incorrect_specific / N_specific   (undefined if N_specific == 0)
AMBIGUITY_SET and UNRESOLVED outcomes are never counted as specific diagnoses.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

SPECIFIC = "SPECIFIC"
AMBIGUITY_SET = "AMBIGUITY_SET"
UNRESOLVED = "UNRESOLVED"
OUTCOMES = (SPECIFIC, AMBIGUITY_SET, UNRESOLVED)


def coverage_and_risk(outcome: Sequence[str], y_pred: Sequence, y_true: Sequence) -> Dict[str, object]:
    outcome = np.asarray(outcome)
    y_pred = np.asarray(y_pred, dtype=object)
    y_true = np.asarray(y_true, dtype=object)
    n = len(outcome)
    spec = outcome == SPECIFIC
    n_spec = int(spec.sum())
    n_err = int(np.sum(y_pred[spec] != y_true[spec]))
    return {
        "n_eligible": n,
        "n_specific": n_spec,
        "n_ambiguity": int(np.sum(outcome == AMBIGUITY_SET)),
        "n_unresolved": int(np.sum(outcome == UNRESOLVED)),
        "coverage": n_spec / n if n else float("nan"),
        "selective_risk": n_err / n_spec if n_spec else float("nan"),
        "selective_risk_defined": bool(n_spec),
    }


def risk_coverage_curve(score: Sequence[float], correct: Sequence[bool]) -> pd.DataFrame:
    """Risk at every coverage level obtained by accepting the top-m samples by score.

    Ties in score are accepted together (no arbitrary ordering inside a tie), so the
    curve only has points where the accepted set is uniquely defined.
    """
    s = np.asarray(score, dtype=float)
    c = np.asarray(correct, dtype=bool)
    if len(s) != len(c):
        raise ValueError("length mismatch")
    if not np.isfinite(s).all():
        raise ValueError("scores must be finite (map invalid inputs to UNRESOLVED before ranking)")
    order = np.argsort(-s, kind="mergesort")
    s_sorted, c_sorted = s[order], c[order]
    last_of_tie = np.r_[s_sorted[1:] != s_sorted[:-1], True]
    m = np.flatnonzero(last_of_tie) + 1
    errs = np.cumsum(~c_sorted)[m - 1]
    return pd.DataFrame({"n_accepted": m, "coverage": m / len(s), "selective_risk": errs / m,
                         "score_threshold": s_sorted[m - 1]})


def rank_match_selection(score: Sequence[float], target_coverage: float) -> np.ndarray:
    """Label-free rank-matched acceptance mask (F10 step 86).

    Accept samples with score >= the score of the ceil(target*n)-th ranked sample.
    Ties at the boundary are all accepted, so realised coverage can exceed the target;
    the realised coverage must be reported.
    """
    s = np.asarray(score, dtype=float)
    if not 0 < target_coverage <= 1:
        raise ValueError("target_coverage must be in (0, 1]")
    if not np.isfinite(s).all():
        raise ValueError("scores must be finite")
    m = int(np.ceil(target_coverage * len(s)))
    if m == 0:
        return np.zeros(len(s), dtype=bool)
    thr = np.sort(s)[::-1][m - 1]
    return s >= thr


def multiclass_brier(P, y_idx) -> float:
    P = np.asarray(P, dtype=float)
    Y = np.zeros_like(P)
    Y[np.arange(len(P)), np.asarray(y_idx, dtype=int)] = 1.0
    return float(np.mean(np.sum((P - Y) ** 2, axis=1)))


def log_loss(P, y_idx, eps: float = 1e-15) -> float:
    P = np.clip(np.asarray(P, dtype=float), eps, 1.0)
    return float(-np.mean(np.log(P[np.arange(len(P)), np.asarray(y_idx, dtype=int)])))


def top_label_ece(P, y_idx, n_bins: int = 10) -> Dict[str, object]:
    """Equal-width top-label expected calibration error with the per-bin table."""
    P = np.asarray(P, dtype=float)
    y_idx = np.asarray(y_idx, dtype=int)
    conf = P.max(axis=1)
    pred = P.argmax(axis=1)
    corr = pred == y_idx
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    b = np.clip(np.digitize(conf, edges[1:-1], right=True), 0, n_bins - 1)
    rows, ece = [], 0.0
    for k in range(n_bins):
        mk = b == k
        nk = int(mk.sum())
        acc = float(corr[mk].mean()) if nk else float("nan")
        cf = float(conf[mk].mean()) if nk else float("nan")
        if nk:
            ece += nk / len(P) * abs(acc - cf)
        rows.append({"bin": k, "lower": edges[k], "upper": edges[k + 1], "n": nk,
                     "mean_confidence": cf, "accuracy": acc})
    return {"ece": float(ece), "bins": pd.DataFrame(rows)}


def classification_summary(y_true, y_pred, labels: Sequence[str]) -> Dict[str, object]:
    """Accuracy, macro-F1 and per-class P/R with explicit reporting of absent classes."""
    y_true = np.asarray(y_true, dtype=object)
    y_pred = np.asarray(y_pred, dtype=object)
    present = [l for l in labels if l in set(y_true.tolist())]
    absent = [l for l in labels if l not in present]
    p, r, f, sup = precision_recall_fscore_support(y_true, y_pred, labels=list(labels), zero_division=0)
    per_class = pd.DataFrame({"class": list(labels), "precision": p, "recall": r, "f1": f, "support": sup})
    per_class.loc[per_class["support"] == 0, ["recall", "f1"]] = np.nan  # undefined, not zero
    return {
        "accuracy": float(np.mean(y_true == y_pred)) if len(y_true) else float("nan"),
        "macro_f1_present_classes": float(f1_score(y_true, y_pred, labels=present, average="macro",
                                                   zero_division=0)) if present else float("nan"),
        "classes_absent_from_y_true": absent,
        "per_class": per_class,
        "confusion_matrix": pd.DataFrame(confusion_matrix(y_true, y_pred, labels=list(labels)),
                                         index=list(labels), columns=list(labels)),
    }


def ambiguity_summary(outcome, ambiguity_set, y_true, n_classes: int, broad_size: Optional[int] = None) -> Dict[str, object]:
    """Inclusion rate and size statistics for AMBIGUITY_SET outcomes (reported together)."""
    outcome = np.asarray(outcome)
    sets = [s.split("|") if isinstance(s, str) and s else [] for s in ambiguity_set]
    y_true = np.asarray(y_true, dtype=object)
    idx = np.flatnonzero(outcome == AMBIGUITY_SET)
    if idx.size == 0:
        return {"n_ambiguity": 0, "inclusion_rate": float("nan"), "mean_size": float("nan"),
                "median_size": float("nan"), "broad_rate": float("nan")}
    sizes = np.array([len(sets[i]) for i in idx])
    incl = np.array([y_true[i] in sets[i] for i in idx])
    broad = n_classes - 1 if broad_size is None else broad_size
    return {"n_ambiguity": int(idx.size), "inclusion_rate": float(incl.mean()),
            "mean_size": float(sizes.mean()), "median_size": float(np.median(sizes)),
            "broad_rate": float(np.mean(sizes >= broad))}


def per_group_selective(df: pd.DataFrame, group_col: str = "Scenario_Family_ID") -> pd.DataFrame:
    """Per-family coverage/risk table (families are the independence unit)."""
    rows = []
    for g, d in df.groupby(group_col, sort=True):
        r = coverage_and_risk(d["policy_outcome"], d["y_pred"], d["y_true"])
        r[group_col] = g
        r["n_scenarios"] = d["Scenario_ID"].nunique() if "Scenario_ID" in d else np.nan
        rows.append(r)
    return pd.DataFrame(rows)
