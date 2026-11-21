"""
H2-PRISM comparator scores (Task A16 implementation, Ahmed; definitions owned by
Faisal under F8). Single shared implementation -- do not duplicate elsewhere.

STATUS: IMPLEMENTED + TESTED (closed-form fixtures). Score-only functions: they never
see labels, never fit anything and never select thresholds.

    C(x) = max_k p_k(x)                      confidence            in [1/K, 1]
    M(x) = p_(1)(x) - p_(2)(x)               probability margin    in [0, 1]
    H(x) = -sum_k p_k(x) log p_k(x)          entropy (nats), 0 log 0 := 0, in [0, log K]
    -H(x)                                    entropy oriented so that higher = more willing to accept
    D(x)                                     read from distinguishability.py (F7); validated here only

Direction convention (F8 step 74): for every acceptance score, HIGHER means greater
willingness to issue a SPECIFIC diagnosis.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


class ProbabilityValidationError(ValueError):
    pass


def validate_probabilities(P, atol: float = 1e-6, n_classes: Optional[int] = None) -> np.ndarray:
    """Return P as float array after checking shape, finiteness, range and row sums."""
    P = np.asarray(P, dtype=float)
    if P.ndim != 2:
        raise ProbabilityValidationError("probabilities must be a 2-D array (n_samples, K)")
    if n_classes is not None and P.shape[1] != n_classes:
        raise ProbabilityValidationError(f"expected {n_classes} classes, got {P.shape[1]}")
    if P.shape[1] < 2:
        raise ProbabilityValidationError("at least two classes are required for margin/entropy")
    if not np.isfinite(P).all():
        raise ProbabilityValidationError("probabilities contain NaN/inf")
    if (P < -atol).any() or (P > 1 + atol).any():
        raise ProbabilityValidationError("probabilities outside [0, 1]")
    rs = P.sum(axis=1)
    if not np.allclose(rs, 1.0, atol=atol):
        bad = int(np.sum(~np.isclose(rs, 1.0, atol=atol)))
        raise ProbabilityValidationError(f"{bad} row(s) do not sum to 1 within atol={atol}")
    return np.clip(P, 0.0, 1.0)


def confidence(P) -> np.ndarray:
    P = validate_probabilities(P)
    return P.max(axis=1)


def margin(P) -> np.ndarray:
    P = validate_probabilities(P)
    s = np.sort(P, axis=1)
    return s[:, -1] - s[:, -2]


def entropy(P, normalized: bool = False) -> np.ndarray:
    P = validate_probabilities(P)
    with np.errstate(divide="ignore", invalid="ignore"):
        terms = np.where(P > 0, P * np.log(P), 0.0)
    H = -terms.sum(axis=1)
    H = np.maximum(H, 0.0)
    if normalized:
        H = H / np.log(P.shape[1])
    return H


def validate_distinguishability(D, allow_nan: bool = True) -> np.ndarray:
    D = np.asarray(D, dtype=float)
    if D.ndim != 1:
        raise ValueError("D must be 1-D")
    fin = np.isfinite(D)
    if not allow_nan and not fin.all():
        raise ValueError("D contains NaN/inf")
    if ((D[fin] < -1e-12) | (D[fin] > 1 + 1e-12)).any():
        raise ValueError("D outside [0, 1]")
    return D


def logit(p, eps: float = 1e-6) -> np.ndarray:
    """Clipped logit used for logit(C) in the combined scores of F10."""
    p = np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    return np.log(p) - np.log1p(-p)


def compute_comparators(P, D=None) -> pd.DataFrame:
    """Return C, M, H, neg_H (and D if supplied) with one row per sample."""
    P = validate_probabilities(P)
    out = pd.DataFrame({"C": confidence(P), "M": margin(P), "H": entropy(P)})
    out["neg_H"] = -out["H"]
    if D is not None:
        Dv = validate_distinguishability(D)
        if len(Dv) != len(out):
            raise ValueError("D length does not match probabilities")
        out["D"] = Dv
    return out
