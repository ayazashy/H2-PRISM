"""
CANDIDATE evidence statistic E_h(x): independence-group-balanced, signed evidence margin for a stated hypothesis h.
(Protocol 2.0 candidate component P2-F'; the original D(x) in distinguishability.py is unchanged and remains the
comparator.)

Why a new statistic. The registered D(x) = q_(1)(x) - q_(2)(x) is an unsigned, window-weighted agreement margin of the
k nearest reference windows. Forensic findings: (i) it is class-agnostic, so it can be high while supporting a DIFFERENT
class than the classifier's; (ii) overlapping windows of one run, and replicas of one scenario in other topologies,
each count as separate votes, so agreement of ONE scenario looks like strong support (D = 1 for 67-86% of windows);
(iii) it is defined even when no independent evidence exists.

Definition (reference R fitted on development data only; query x; hypothesis h, normally the classifier label):
  z(.)        reference-only standardisation (mean, SD of R; constant columns get SD 1)
  R(x)        reference windows whose independence unit != unit(x)          (exclude_query_unit)
  N(x)        k nearest windows of R(x) in z-space (tie-inclusive)
  G(x)        distinct independence units (scenario independence groups) present in N(x)
  s_c(x)      sum over g in G(x) of the SHARE of g's neighbours labelled c   (each unit has total weight 1)
  q_c(x)      s_c(x) / |G(x)|                                                 (group-balanced class support)
  E_h(x)      q_h(x) - max_{c != h} q_c(x)                                    in [-1, 1]
Undefined (NaN) with an explicit flag when:
  OUT_OF_SUPPORT         mean neighbour distance > the reference's own out-of-support quantile
  HYPOTHESIS_UNSUPPORTED  h has no window in R(x) (no evidence can exist for h)
  INSUFFICIENT_INDEPENDENT_EVIDENCE  |G(x)| < min_units (agreement of fewer units is not evidence)
Interpretation: E_h > 0 = independent reference scenarios near x favour h over every alternative; E_h < 0 = they favour
another class (a CONFLICT between evidence and hypothesis - it does not say which source is wrong); E_h ~ 0 = competing
hypotheses are equally supported. E_h is an empirical neighbourhood statistic, not physical identifiability; it is
only as good as the reference's labels and its coverage of x's configuration (forensic FA-04).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

FLAG_OOS = "OUT_OF_SUPPORT"
FLAG_UNSUPPORTED = "HYPOTHESIS_UNSUPPORTED"
FLAG_FEW_UNITS = "INSUFFICIENT_INDEPENDENT_EVIDENCE"


@dataclass(frozen=True)
class EvidenceConfig:
    k: int = 25
    min_units: int = 2
    exclude_query_unit: bool = True
    out_of_support_quantile: float = 0.99
    tie_tol: float = 1e-12

    def __post_init__(self):
        if self.k < 1 or self.min_units < 1:
            raise ValueError("k and min_units must be >= 1")
        if not 0 < self.out_of_support_quantile <= 1:
            raise ValueError("out_of_support_quantile must be in (0, 1]")


class EvidenceMargin:
    """Fit on development (reference) data only; compute E_h for query rows and stated hypotheses."""

    def __init__(self, config: EvidenceConfig = EvidenceConfig()):
        self.config = config

    def fit(self, X_ref, y_ref, units_ref, classes: Sequence[str]) -> "EvidenceMargin":
        X = np.asarray(X_ref, dtype=float)
        if X.ndim != 2 or not len(X) or not np.isfinite(X).all():
            raise ValueError("reference features must be a finite, non-empty 2-D array")
        self.classes_ = list(classes)
        self.y_ = np.asarray(y_ref, dtype=object)
        self.u_ = np.asarray(units_ref, dtype=object)
        if not (len(self.y_) == len(self.u_) == len(X)):
            raise ValueError("reference arrays have inconsistent lengths")
        if set(self.y_.tolist()) - set(self.classes_):
            raise ValueError("reference labels outside the class list")
        self.mu_ = X.mean(0)
        sd = X.std(0)
        self.sd_ = np.where(sd > 0, sd, 1.0)
        self.Z_ = (X - self.mu_) / self.sd_
        # out-of-support threshold from the reference itself (leave-one-unit-out mean k-NN distance)
        self.oos_ = np.inf
        if self.config.out_of_support_quantile < 1:
            md = self._mean_knn_dist(self.Z_, self.u_)
            md = md[np.isfinite(md)]
            if len(md):
                self.oos_ = float(np.quantile(md, self.config.out_of_support_quantile))
        return self

    def _mean_knn_dist(self, Zq, uq):
        k = self.config.k
        out = np.full(len(Zq), np.nan)
        for c0 in range(0, len(Zq), 512):
            d = cdist(Zq[c0:c0 + 512], self.Z_)
            for i in range(d.shape[0]):
                av = self.u_ != uq[c0 + i]
                if av.sum() == 0:
                    continue
                dv = np.sort(d[i][av])[: min(k, int(av.sum()))]
                out[c0 + i] = dv.mean()
        return out

    def compute(self, X_query, hypotheses: Sequence[str], query_units: Optional[Sequence] = None) -> pd.DataFrame:
        cfg = self.config
        Xq = np.asarray(X_query, dtype=float)
        hyp = list(hypotheses)
        if len(hyp) != len(Xq):
            raise ValueError("one hypothesis per query row is required")
        if cfg.exclude_query_unit and query_units is None:
            raise ValueError("exclude_query_unit=True requires query_units")
        qu = np.asarray(query_units, dtype=object) if query_units is not None else np.array([None] * len(Xq), dtype=object)
        Zq = (Xq - self.mu_) / self.sd_
        rows = []
        for c0 in range(0, len(Zq), 512):
            d = cdist(Zq[c0:c0 + 512], self.Z_)
            for i in range(d.shape[0]):
                rows.append(self._one(d[i], hyp[c0 + i], qu[c0 + i]))
        return pd.DataFrame(rows)

    def _one(self, d, h, qunit) -> dict:
        cfg = self.config
        av = (self.u_ != qunit) if (cfg.exclude_query_unit and qunit is not None) else np.ones(len(d), bool)
        base = {"E": np.nan, "hypothesis": h, "evidence_top_class": None, "n_units": 0, "flag": ""}
        if h not in self.classes_ or not (self.y_[av] == h).any():
            return {**base, "flag": FLAG_UNSUPPORTED}
        dav = d[av]
        k = min(cfg.k, len(dav))
        kth = np.partition(dav, k - 1)[k - 1]
        idx = np.flatnonzero(av)[dav <= kth + cfg.tie_tol]
        if float(d[idx].mean()) > self.oos_:
            return {**base, "flag": FLAG_OOS}
        units = self.u_[idx]
        labs = self.y_[idx]
        ug = pd.unique(units)
        q = {c: 0.0 for c in self.classes_}
        for g in ug:  # each independence unit carries total weight 1, split over its neighbours' labels
            m = units == g
            for c, n in pd.Series(labs[m]).value_counts().items():
                q[c] += n / m.sum()
        q = {c: v / len(ug) for c, v in q.items()}
        top = sorted(self.classes_, key=lambda c: (-q[c], self.classes_.index(c)))[0]
        out = {**base, "evidence_top_class": top, "n_units": int(len(ug)), **{f"q_{c}": q[c] for c in self.classes_}}
        if len(ug) < cfg.min_units:
            return {**out, "flag": FLAG_FEW_UNITS}
        return {**out, "E": q[h] - max(v for c, v in q.items() if c != h)}
