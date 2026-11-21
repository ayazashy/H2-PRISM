"""
H2-PRISM empirical class support q(x) and empirical distinguishability D(x)
(Task F7 -- preparation implementation, Faisal ownership; Ahmed math review A4).

STATUS: IMPLEMENTED + TESTED on synthetic and hand-calculated fixtures. NOT executed
on project data. D(x) is an *empirical* statistic of a reference neighbourhood; it is
not a measure of physical identifiability and no claim about its value is made here.

Definition implemented (02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md):

    z(x)      = (x - mu_ref) / sigma_ref          mu, sigma from the REFERENCE set only
    R(x)      = reference windows whose Scenario_Family_ID != family(x)  (if excluded)
    d_k(x)    = k-th smallest Euclidean distance from z(x) to R(x)
    N(x)      = { r in R(x) : ||z(x) - z(r)|| <= d_k(x) + tie_tol }   (tie-inclusive)
    s_c(x)    = sum_{r in N(x), y_r = c} w_r     w_r = 1 (uniform) or 1/max(d_r, d_floor)
    s_c(x)   <- s_c(x) / pi_c                    (only if prior_correction; pi_c = class
                                                  share in R(x); s_c = 0 if pi_c = 0)
    q_c(x)    = s_c(x) / sum_c' s_c'(x)          q(x) in the simplex over the K classes
    D(x)      = q_(1)(x) - q_(2)(x)              (D = q_(1) if K = 1)

Tie-inclusive neighbourhoods make q and D invariant to the order of reference rows.
Classes absent from N(x) get q_c = 0 (never NaN). D is NaN only when x has
non-finite features or no reference is available, and a flag says which.
The query's own label is never an input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

FLAG_SPARSE = "SPARSE_REFERENCE"
FLAG_INSUFFICIENT_CLASS = "INSUFFICIENT_CLASS_REFERENCE"
FLAG_LOW_DIVERSITY = "LOW_SCENARIO_DIVERSITY"
FLAG_LOW_SUPPORT = "LOW_SUPPORT"
FLAG_OUT_OF_SUPPORT = "OUT_OF_SUPPORT"
FLAG_ZERO_DISTANCE = "ZERO_DISTANCE_NEIGHBOR"
FLAG_INVALID = "INVALID_FEATURES"
FLAG_NO_REFERENCE = "NO_REFERENCE"
# Phase 6 (F-D08): the top class is supported by neighbours from too few distinct runs/families.
# A high D(x) driven by a single run must not count as reliable evidence for one class.
FLAG_TOP_CLASS_FEW_RUNS = "TOP_CLASS_FEW_INDEPENDENT_RUNS"

ALL_FLAGS = (FLAG_SPARSE, FLAG_INSUFFICIENT_CLASS, FLAG_LOW_DIVERSITY, FLAG_LOW_SUPPORT,
             FLAG_OUT_OF_SUPPORT, FLAG_ZERO_DISTANCE, FLAG_INVALID, FLAG_NO_REFERENCE,
             FLAG_TOP_CLASS_FEW_RUNS)


@dataclass(frozen=True)
class DConfig:
    """Parameters of the D(x) statistic.

    k=25 is the plan's prespecified starting value (F7 step 69) and still requires
    justification against reference size before the primary run. The flag thresholds
    below are PROVISIONAL defaults pending Faisal's design decision
    (02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md, section "Open decisions").
    """

    k: int = 25
    weighting: str = "uniform"  # "uniform" | "inverse_distance"
    prior_correction: bool = False
    exclude_query_family: bool = True
    min_class_reference: int = 25
    min_distinct_scenarios: int = 2
    low_support_min_top_count: int = 5
    min_top_class_families: int = 2  # distinct reference families behind the top class (Phase 6)
    tie_tol: float = 1e-12
    zero_distance_tol: float = 1e-9
    distance_floor: float = 1e-6
    out_of_support_distance: Optional[float] = None
    chunk_size: int = 512

    def __post_init__(self) -> None:
        if self.k < 1:
            raise ValueError("k must be >= 1")
        if self.weighting not in ("uniform", "inverse_distance"):
            raise ValueError("weighting must be 'uniform' or 'inverse_distance'")


class EmpiricalSupport:
    """Reference-neighbourhood class support. Fit on training/development data only."""

    def __init__(self, config: DConfig = DConfig()):
        self.config = config
        self._fitted = False

    def fit(self, X_ref, y_ref, families_ref, scenarios_ref, classes: Sequence, support_units=None) -> "EmpiricalSupport":
        """support_units (CANDIDATE protocol 2.0, P2-C): optional unit per reference row used to COUNT independent
        support behind the top class (e.g. scenario independence groups). Default None = families (protocol 1.1);
        query-family exclusion always uses families_ref."""
        X = np.asarray(X_ref, dtype=float)
        if X.ndim != 2 or len(X) == 0:
            raise ValueError("X_ref must be a non-empty 2-D array")
        if not np.isfinite(X).all():
            raise ValueError("reference features contain non-finite values; exclude those windows upstream")
        y = np.asarray(y_ref)
        fam = np.asarray(families_ref)
        scen = np.asarray(scenarios_ref)
        if not (len(y) == len(fam) == len(scen) == len(X)):
            raise ValueError("reference arrays have inconsistent lengths")
        self.classes_ = list(classes)
        unknown = set(y.tolist()) - set(self.classes_)
        if unknown:
            raise ValueError(f"reference labels not in class list: {sorted(map(str, unknown))}")
        self.mu_ = X.mean(axis=0)
        sd = X.std(axis=0, ddof=0)
        self.constant_features_ = np.flatnonzero(sd == 0)
        self.sigma_ = np.where(sd > 0, sd, 1.0)
        self.Z_ = (X - self.mu_) / self.sigma_
        self.y_idx_ = np.array([self.classes_.index(v) for v in y.tolist()], dtype=int)
        self.fam_ = fam
        if support_units is not None and len(support_units) != len(fam):
            raise ValueError("support_units length mismatch")
        self.unit_ = fam if support_units is None else np.asarray(support_units)
        self.scen_ = scen
        self._fitted = True
        return self

    # ------------------------------------------------------------------ core
    def compute(self, X_query, query_families: Optional[Sequence] = None) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("call fit() first")
        cfg = self.config
        Xq = np.asarray(X_query, dtype=float)
        if Xq.ndim != 2 or Xq.shape[1] != self.Z_.shape[1]:
            raise ValueError("query feature dimension does not match reference")
        if cfg.exclude_query_family:
            if query_families is None:
                raise ValueError("exclude_query_family=True requires query_families")
            qfam = np.asarray(query_families)
            if len(qfam) != len(Xq):
                raise ValueError("query_families length mismatch")
        else:
            qfam = None
        K = len(self.classes_)
        n = len(Xq)
        q_out = np.full((n, K), np.nan)
        rec = {k: [None] * n for k in ("D", "top_class", "second_class", "k_effective", "n_available_reference",
                                         "n_distinct_scenarios", "n_distinct_families", "max_scenario_share",
                                         "mean_neighbor_distance", "max_neighbor_distance",
                                         "min_neighbor_distance", "top_class_n_families", "support_flags")}
        valid_rows = np.isfinite(Xq).all(axis=1)
        Zq = (np.where(np.isfinite(Xq), Xq, 0.0) - self.mu_) / self.sigma_

        for c0 in range(0, n, cfg.chunk_size):
            c1 = min(n, c0 + cfg.chunk_size)
            dist = cdist(Zq[c0:c1], self.Z_, metric="euclidean")
            for i in range(c0, c1):
                self._one(i, dist[i - c0], valid_rows[i], qfam, q_out, rec, K)

        out = pd.DataFrame(q_out, columns=[f"q_{c}" for c in self.classes_])
        for kname, vals in rec.items():
            out[kname] = vals
        out["k_requested"] = cfg.k
        return out

    def _one(self, i, d, valid, qfam, q_out, rec, K):
        cfg = self.config
        flags: List[str] = []
        avail = np.ones(len(d), dtype=bool)
        if qfam is not None:
            avail &= self.fam_ != qfam[i]
        n_av = int(avail.sum())
        rec["n_available_reference"][i] = n_av
        if not valid:
            rec["D"][i] = np.nan
            rec["support_flags"][i] = FLAG_INVALID
            for k in ("top_class", "second_class"):
                rec[k][i] = None
            rec["k_effective"][i] = 0
            return
        if n_av == 0:
            rec["D"][i] = np.nan
            rec["support_flags"][i] = FLAG_NO_REFERENCE
            rec["k_effective"][i] = 0
            return
        if n_av < cfg.k:
            flags.append(FLAG_SPARSE)
        class_counts = np.bincount(self.y_idx_[avail], minlength=K)
        if (class_counts < cfg.min_class_reference).any():
            flags.append(FLAG_INSUFFICIENT_CLASS)
        dav = d[avail]
        k_av = min(cfg.k, n_av)
        kth = np.partition(dav, k_av - 1)[k_av - 1]
        sel_local = np.flatnonzero(dav <= kth + cfg.tie_tol)
        idx = np.flatnonzero(avail)[sel_local]
        dn = d[idx]
        yn = self.y_idx_[idx]
        if cfg.weighting == "uniform":
            w = np.ones(len(idx))
        else:
            w = 1.0 / np.maximum(dn, cfg.distance_floor)
        s = np.bincount(yn, weights=w, minlength=K).astype(float)
        if cfg.prior_correction:
            pi = class_counts / n_av
            s = np.where(pi > 0, s / np.where(pi > 0, pi, 1.0), 0.0)
        q = s / s.sum()
        q_out[i] = q
        order = sorted(range(K), key=lambda c: (-q[c], c))  # deterministic tie-break by class index
        D = float(q[order[0]] - q[order[1]]) if K > 1 else float(q[order[0]])
        top_count = int(np.sum(yn == order[0]))
        if top_count < cfg.low_support_min_top_count:
            flags.append(FLAG_LOW_SUPPORT)
        top_fams = len(set(self.unit_[idx][yn == order[0]].tolist()))
        if top_fams < cfg.min_top_class_families:
            flags.append(FLAG_TOP_CLASS_FEW_RUNS)
        rec["top_class_n_families"][i] = top_fams
        scen_n = pd.Series(self.scen_[idx]).value_counts()
        if len(scen_n) < cfg.min_distinct_scenarios:
            flags.append(FLAG_LOW_DIVERSITY)
        if dn.min() <= cfg.zero_distance_tol:
            flags.append(FLAG_ZERO_DISTANCE)
        if cfg.out_of_support_distance is not None and float(dn.mean()) > cfg.out_of_support_distance:
            flags.append(FLAG_OUT_OF_SUPPORT)
        rec["D"][i] = D
        rec["top_class"][i] = self.classes_[order[0]]
        rec["second_class"][i] = self.classes_[order[1]] if K > 1 else None
        rec["k_effective"][i] = int(len(idx))
        rec["n_distinct_scenarios"][i] = int(len(scen_n))
        rec["n_distinct_families"][i] = int(len(set(self.fam_[idx].tolist())))
        rec["max_scenario_share"][i] = float(scen_n.iloc[0] / len(idx))
        rec["mean_neighbor_distance"][i] = float(dn.mean())
        rec["max_neighbor_distance"][i] = float(dn.max())
        rec["min_neighbor_distance"][i] = float(dn.min())
        rec["support_flags"][i] = "|".join(flags)

    # ------------------------------------------------------- development aids
    def development_support(self) -> pd.DataFrame:
        """q/D for every reference window with its own family excluded (development mode)."""
        Xr = self.Z_ * self.sigma_ + self.mu_
        return self.compute(Xr, query_families=self.fam_)

    def fit_out_of_support_threshold(self, quantile: float) -> float:
        """Distance threshold from leave-one-family-out neighbour distances of the reference.

        Uses reference (development) data only. Returns the threshold; the caller must
        create a new DConfig with ``out_of_support_distance`` set (configs are immutable,
        so the choice is explicit and recorded).
        """
        if not 0 < quantile < 1:
            raise ValueError("quantile must be in (0, 1)")
        dev = self.development_support()
        m = dev["mean_neighbor_distance"].astype(float).dropna()
        if m.empty:
            raise ValueError("no leave-one-family-out distances available")
        return float(np.quantile(m.to_numpy(), quantile))
