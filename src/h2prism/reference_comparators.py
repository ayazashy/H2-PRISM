"""
Standard comparators from the selective-prediction, set-valued and OOD literature (action X09; issues D-13, E-02).
RESEARCH MODULE: implementations with synthetic tests; not registered in any protocol (registration needs the methods
owner) and not evaluated on any project data. Bibliographic details: 00_governance/LITERATURE_REGISTER.csv.

  confidence-only abstention (Chow's reject rule)   -> already h2prism.comparators.confidence (not duplicated)
  trust_score            ratio d(x, nearest other class) / d(x, predicted class), optional alpha density filter
                         (Jiang, Kim, Guan & Gupta, 2018)
  split_conformal_*      LAC and APS prediction sets with the finite-sample quantile (Vovk et al.; Sadinle et al.;
                         Romano, Sesia & Candes, 2020). Coverage guarantee requires exchangeable calibration and test
                         units; with grouped (dependent) data the guarantee holds only at the group level when one
                         score per group is used (`calibration_unit_scores`).
  mahalanobis_score      min class-conditional Mahalanobis distance with a shared covariance (Lee et al., 2018)
  knn_distance_score     distance to the k-th nearest reference (Sun et al., 2022)
  ensemble_disagreement  mean KL divergence of members from the ensemble mean, from GIVEN probability arrays
Relationship to Distinguishability v2 (tested): with one window per scenario, m = 1, no own-group exclusion and unit
resolution, v2's margin M = d_other - d_pred and log(trust score) = log d_other - log d_pred have the same sign and the
same zero, but rank windows differently (difference vs ratio). v2 adds group-level corroboration (m-th nearest
independent scenario), own-group exclusion, explicit insufficiency states and resolution units; whether that adds
diagnostic value is an empirical question (H-R3), not established here.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np
from scipy.spatial.distance import cdist


def _as2d(X):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or not np.isfinite(X).all():
        raise ValueError("features must be a finite 2-D array")
    return X


# ------------------------------------------------------------------------------------------------ trust score
def trust_score(X_ref, y_ref, X_query, y_pred, alpha: float = 0.0, k: int = 10, eps: float = 1e-12) -> np.ndarray:
    """Jiang et al. (2018) trust score. alpha in [0, 1): fraction of each class's reference points with the largest
    k-NN radius removed before scoring (density filter). Higher = more trustworthy prediction."""
    Xr, Xq = _as2d(X_ref), _as2d(X_query)
    y_ref, y_pred = np.asarray(y_ref, object), np.asarray(y_pred, object)
    if not 0 <= alpha < 1:
        raise ValueError("alpha must be in [0, 1)")
    keep = {}
    for c in np.unique(y_ref):
        Xc = Xr[y_ref == c]
        if alpha > 0 and len(Xc) > k:
            r = np.sort(cdist(Xc, Xc), 1)[:, min(k, len(Xc) - 1)]
            Xc = Xc[r <= np.quantile(r, 1 - alpha)]
        keep[c] = Xc
    if set(np.unique(y_pred)) - set(keep):
        raise ValueError("predicted class without reference points")
    dist = {c: cdist(Xq, Xc).min(1) for c, Xc in keep.items()}
    out = np.empty(len(Xq))
    for i, c in enumerate(y_pred):
        d_pred = dist[c][i]
        d_other = min(dist[o][i] for o in keep if o != c)
        out[i] = d_other / max(d_pred, eps)
    return out


# ------------------------------------------------------------------------------------------------ conformal
def _conformal_quantile(scores, alpha: float) -> float:
    s = np.sort(np.asarray(scores, float))
    n = len(s)
    if n == 0:
        raise ValueError("no calibration scores")
    rank = int(np.ceil((n + 1) * (1 - alpha)))
    return float("inf") if rank > n else float(s[rank - 1])


def lac_scores(P, y_idx) -> np.ndarray:
    P = np.asarray(P, float)
    return 1.0 - P[np.arange(len(P)), np.asarray(y_idx)]


def aps_scores(P, y_idx) -> np.ndarray:
    """Deterministic APS score: total probability of classes ranked at or above the true class."""
    P = np.asarray(P, float)
    out = np.empty(len(P))
    for i, (p, y) in enumerate(zip(P, y_idx)):
        out[i] = p[p >= p[y]].sum()
    return out


def calibration_unit_scores(scores, units) -> np.ndarray:
    """One score per independent unit (the maximum: conservative), so exchangeability is assumed only across units."""
    scores, units = np.asarray(scores, float), np.asarray(units, object)
    return np.array([scores[units == u].max() for u in dict.fromkeys(units.tolist())])


def split_conformal_sets(P_cal, y_cal_idx, P_test, alpha: float = 0.1, method: str = "lac",
                         cal_units: Optional[Sequence] = None) -> Dict[str, object]:
    """Prediction sets (boolean matrix n_test x K) with marginal coverage >= 1 - alpha under exchangeability."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0, 1)")
    fn = {"lac": lac_scores, "aps": aps_scores}.get(method)
    if fn is None:
        raise ValueError("method must be 'lac' or 'aps'")
    s = fn(P_cal, y_cal_idx)
    if cal_units is not None:
        s = calibration_unit_scores(s, cal_units)
    q = _conformal_quantile(s, alpha)
    P = np.asarray(P_test, float)
    if method == "lac":
        sets = (1.0 - P) <= q
    else:
        sets = np.zeros_like(P, dtype=bool)
        for i, p in enumerate(P):
            for c in range(P.shape[1]):
                sets[i, c] = p[p >= p[c]].sum() <= q
    return {"sets": sets, "qhat": q, "n_calibration_units": int(len(s))}


# ------------------------------------------------------------------------------------------------ OOD
def mahalanobis_fit(X_ref, y_ref, ridge: float = 1e-6) -> Dict[str, object]:
    X, y = _as2d(X_ref), np.asarray(y_ref, object)
    classes = list(dict.fromkeys(y.tolist()))
    mu = {c: X[y == c].mean(0) for c in classes}
    resid = np.vstack([X[y == c] - mu[c] for c in classes])
    cov = np.cov(resid, rowvar=False) + ridge * np.eye(X.shape[1])
    return {"classes": classes, "mu": mu, "prec": np.linalg.inv(cov)}


def mahalanobis_score(fit: Dict[str, object], X_query) -> np.ndarray:
    """Minimum class-conditional squared Mahalanobis distance (larger = more out-of-distribution)."""
    Xq = _as2d(X_query)
    d = [np.einsum("ij,jk,ik->i", Xq - fit["mu"][c], fit["prec"], Xq - fit["mu"][c]) for c in fit["classes"]]
    return np.min(np.vstack(d), 0)


def knn_distance_score(X_ref, X_query, k: int = 10, normalize: bool = True) -> np.ndarray:
    """Distance to the k-th nearest reference point (Sun et al. 2022 use L2-normalised features)."""
    Xr, Xq = _as2d(X_ref), _as2d(X_query)
    if normalize:
        Xr = Xr / np.maximum(np.linalg.norm(Xr, axis=1, keepdims=True), 1e-12)
        Xq = Xq / np.maximum(np.linalg.norm(Xq, axis=1, keepdims=True), 1e-12)
    k = min(k, len(Xr))
    return np.sort(cdist(Xq, Xr), 1)[:, k - 1]


# ------------------------------------------------------------------------------------------------ ensembles
def ensemble_disagreement(P_members: Sequence) -> np.ndarray:
    """Mean KL(member || ensemble mean) across members (0 = full agreement). Inputs are given probability arrays;
    nothing is trained here."""
    Ps = np.stack([np.asarray(p, float) for p in P_members])
    if Ps.ndim != 3 or Ps.shape[0] < 2:
        raise ValueError("need >= 2 members of shape (n, K)")
    m = Ps.mean(0)
    eps = 1e-12
    return np.mean(np.sum(Ps * (np.log(Ps + eps) - np.log(m + eps)), axis=2), axis=0)
