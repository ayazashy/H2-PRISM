"""
Distinguishability v2 (RESEARCH MODULE; not used by any registered run, RC1 or the primary runner).

The original D(x) (distinguishability.py) and E_h (evidence_margin.py) are unchanged and remain comparators.
Full definitions, assumptions and rationale: 02_methodology/DISTINGUISHABILITY_V2.md.

Four separate quantities (never merged into one number):

  Evidence sufficiency  per hypothesis h and query x: n_h(x) = number of independent scenario groups of class h in
                        the reference after removing every group linked to x (its own independence group).
                        SUPPORTED if n_h >= m, INSUFFICIENT_EVIDENCE if 1 <= n_h < m, UNSUPPORTED if n_h = 0.
  Separability          D_h(x) = m-th smallest group distance delta_G(x) over groups G of class h   (SUPPORTED h only)
                        M(x; h) = min_{h' eligible, h' != h} D_h'(x) - D_h(x)                     (signed, unbounded)
                        delta_G(x) = min over windows w of G of ||z(x) - z(w)|| / sqrt(p) / s
                        z = reference-only robust scaling (median, 1.4826 MAD; SD fallback; degenerate columns dropped)
                        s = within-scenario resolution: median distance from a reference window to the nearest window
                            of its OWN group that does not overlap it in time (|t_i - t_j| >= window length).
                        Units of M: multiples of the representation's within-scenario resolution. M is NOT a
                        probability and is not calibrated; M > 0 means x is closer to at least m independent scenarios
                        of h than to m independent scenarios of any competing eligible hypothesis.
  Detectability         Det(x) = D_NORMAL(x) compared with theta_det, the q-quantile of D_NORMAL over NORMAL reference
                        windows scored against the OTHER NORMAL groups (leave-one-group-out). Needs >= m + 1 NORMAL
                        groups; otherwise UNDEFINED_INSUFFICIENT_NORMAL_SUPPORT (never 0, never "not detected").
  Out of support        min over all non-linked reference groups of delta_G(x) > theta_oos, the q-quantile of the same
                        statistic for reference windows scored against the other groups (leave-one-group-out).

Conflict-aware decision (decide()): classifier label y_hat and its confidence are inputs, not truth; evidence is an
input, not truth. Contradictions never turn into a different SPECIFIC label:
  OUT_OF_SUPPORT / INVALID                                  -> UNRESOLVED
  y_hat not SUPPORTED, or no eligible competitor (UNTESTABLE) -> UNRESOLVED (configurable, fail-closed default)
  event predicted but detectability = NOT_DETECTED          -> AMBIGUITY_SET {y_hat, NORMAL}
  NORMAL predicted but detectability = DETECTED             -> AMBIGUITY_SET {NORMAL, best eligible event}
  M(x; y_hat) >= tau                                        -> SPECIFIC-eligible (SEPARATED)
  |M(x; y_hat)| < tau                                       -> AMBIGUITY_SET {y_hat} + every eligible h with D_h - D_yhat < tau
  M(x; y_hat) <= -tau                                       -> AMBIGUITY_SET {y_hat, evidence-best h} (CONFLICT)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

SUPPORTED, INSUFFICIENT, UNSUPPORTED = "SUPPORTED", "INSUFFICIENT_EVIDENCE", "UNSUPPORTED"
DET_DETECTED, DET_NOT, DET_UNDEF = "DETECTED", "NOT_DETECTED", "UNDEFINED_INSUFFICIENT_NORMAL_SUPPORT"
SEPARATED, NOT_SEPARATED, CONFLICT = "SEPARATED", "NOT_SEPARATED", "CONFLICT"
UNTESTABLE, HYP_NOT_SUPPORTED, OOS, INVALID, DEGENERATE = (
    "UNTESTABLE_NO_ELIGIBLE_COMPETITOR", "HYPOTHESIS_NOT_SUPPORTED", "OUT_OF_SUPPORT", "INVALID_FEATURES", "DEGENERATE_SCALE")
SPECIFIC, AMBIGUITY_SET, UNRESOLVED = "SPECIFIC", "AMBIGUITY_SET", "UNRESOLVED"


@dataclass(frozen=True)
class V2Config:
    min_groups: int = 2            # m: independent scenario groups required per hypothesis
    tau: float = 1.0               # separation threshold in within-scenario resolution units
    window_s: float = 60.0         # windows closer than this in time overlap and are not used for the scale
    detect_quantile: float = 0.99
    oos_quantile: float = 0.99
    normal_class: str = "NORMAL"
    untestable_outcome: str = UNRESOLVED

    def __post_init__(self):
        if self.min_groups < 1:
            raise ValueError("min_groups must be >= 1")
        if not self.tau > 0:
            raise ValueError("tau must be > 0")
        if not (0 < self.detect_quantile < 1 and 0 < self.oos_quantile < 1):
            raise ValueError("quantiles must be in (0, 1)")
        if self.untestable_outcome not in (UNRESOLVED, AMBIGUITY_SET):
            raise ValueError("untestable_outcome must be UNRESOLVED or AMBIGUITY_SET")


class DistinguishabilityV2:
    """Fit on development reference data only (features, labels, independence groups, window start times)."""

    def __init__(self, config: V2Config = V2Config()):
        self.config = config

    # ------------------------------------------------------------------ fit
    def fit(self, X_ref, y_ref, groups_ref, times_ref, classes: Sequence[str]) -> "DistinguishabilityV2":
        X = np.asarray(X_ref, dtype=float)
        if X.ndim != 2 or not len(X) or not np.isfinite(X).all():
            raise ValueError("reference features must be a finite, non-empty 2-D array")
        y, g, t = (np.asarray(a, dtype=object) for a in (y_ref, groups_ref, times_ref))
        if not (len(y) == len(g) == len(t) == len(X)):
            raise ValueError("reference arrays have inconsistent lengths")
        self.classes_ = list(classes)
        if set(y.tolist()) - set(self.classes_):
            raise ValueError("reference labels outside the class list")
        med = np.median(X, 0)
        mad = 1.4826 * np.median(np.abs(X - med), 0)
        sd = X.std(0)
        scale = np.where(mad > 0, mad, sd)
        self.keep_ = scale > 0                      # degenerate (constant) columns carry no evidence: dropped
        self.n_dropped_ = int((~self.keep_).sum())
        if not self.keep_.any():
            raise ValueError("every reference feature is constant")
        self.med_, self.scale_ = med[self.keep_], scale[self.keep_]
        self.Z_ = (X[:, self.keep_] - self.med_) / self.scale_
        self.p_ = int(self.keep_.sum())
        self.y_, self.g_, self.t_ = y, g, t.astype(float)
        self.group_class_ = {}
        for gg in pd.unique(g):
            labs = set(y[g == gg].tolist())
            if len(labs) != 1:
                raise ValueError(f"independence group {gg!r} mixes classes {sorted(labs)}")
            self.group_class_[gg] = labs.pop()
        self.groups_ = list(self.group_class_)
        self.s_ = self._resolution()
        self.theta_oos_ = self._loo_quantile(None, self.config.oos_quantile)
        normal_groups = [gg for gg, c in self.group_class_.items() if c == self.config.normal_class]
        self.theta_det_ = (self._loo_quantile(self.config.normal_class, self.config.detect_quantile)
                           if len(normal_groups) >= self.config.min_groups + 1 else None)
        return self

    def _raw_group_dist(self, Zq) -> np.ndarray:
        """(n_query, n_groups) RMS-per-feature distance to the nearest window of each group (not yet scaled by s)."""
        out = np.empty((len(Zq), len(self.groups_)))
        for j, gg in enumerate(self.groups_):
            out[:, j] = cdist(Zq, self.Z_[self.g_ == gg]).min(1) / np.sqrt(self.p_)
        return out

    def _resolution(self) -> Optional[float]:
        """Median distance from a reference window to the nearest non-overlapping window of its own group."""
        vals = []
        for gg in self.groups_:
            m = self.g_ == gg
            Zg, tg = self.Z_[m], self.t_[m]
            if len(Zg) < 2:
                continue
            d = cdist(Zg, Zg) / np.sqrt(self.p_)
            d[np.abs(tg[:, None] - tg[None, :]) < self.config.window_s] = np.inf   # same or overlapping windows
            v = d.min(1)
            vals.extend(v[np.isfinite(v)].tolist())
        if not vals:
            return None
        s = float(np.median(vals))
        return s if s > 0 else None

    def _loo_quantile(self, cls: Optional[str], q: float) -> Optional[float]:
        """Leave-one-group-out reference distribution: for windows of each group (of class cls, or of all classes),
        the m-th nearest OTHER group of class cls (cls given) or the nearest other group of any class (cls None)."""
        if self.s_ is None:
            return None
        D = self._raw_group_dist(self.Z_) / self.s_
        vals = []
        for i, gg in enumerate(self.g_):
            if cls is not None and self.group_class_[gg] != cls:
                continue
            cols = [j for j, h in enumerate(self.groups_) if h != gg and (cls is None or self.group_class_[h] == cls)]
            need = self.config.min_groups if cls is not None else 1
            if len(cols) < need:
                continue
            vals.append(np.sort(D[i, cols])[need - 1])
        return float(np.quantile(vals, q)) if vals else None

    # ------------------------------------------------------------------ compute
    def compute(self, X_query, query_groups: Sequence) -> pd.DataFrame:
        """One row per query: sufficiency state and D_h per class, out-of-support, detectability, evidence-best class."""
        cfg = self.config
        Xq = np.asarray(X_query, dtype=float)
        qg = np.asarray(query_groups, dtype=object)
        if Xq.ndim != 2 or len(qg) != len(Xq):
            raise ValueError("query features / groups mismatch")
        valid = np.isfinite(Xq).all(1)
        Zq = (np.where(np.isfinite(Xq), Xq, 0.0)[:, self.keep_] - self.med_) / self.scale_
        raw = self._raw_group_dist(Zq)
        rows = []
        for i in range(len(Xq)):
            r: Dict[str, object] = {"valid": bool(valid[i]), "scale_s": self.s_}
            usable = [j for j, gg in enumerate(self.groups_) if gg != qg[i]]   # linked (own) group removed
            for c in self.classes_:
                cols = [j for j in usable if self.group_class_[self.groups_[j]] == c]
                r[f"n_groups_{c}"] = len(cols)
                r[f"state_{c}"] = SUPPORTED if len(cols) >= cfg.min_groups else (INSUFFICIENT if cols else UNSUPPORTED)
                r[f"D_{c}"] = (float(np.sort(raw[i, cols])[cfg.min_groups - 1] / self.s_)
                               if (r[f"state_{c}"] == SUPPORTED and self.s_ is not None and valid[i]) else np.nan)
            nearest_any = float(raw[i, usable].min() / self.s_) if (usable and self.s_ is not None) else np.nan
            r["nearest_group_distance"] = nearest_any
            r["out_of_support"] = bool(self.theta_oos_ is not None and np.isfinite(nearest_any) and nearest_any > self.theta_oos_)
            dn = r.get(f"D_{cfg.normal_class}", np.nan)
            if self.theta_det_ is None or not np.isfinite(dn):
                r["detectability"] = DET_UNDEF
            else:
                r["detectability"] = DET_DETECTED if dn > self.theta_det_ else DET_NOT
            elig = {c: r[f"D_{c}"] for c in self.classes_ if np.isfinite(r[f"D_{c}"])}
            r["eligible_classes"] = "|".join(sorted(elig, key=self.classes_.index))
            r["evidence_best_class"] = min(elig, key=lambda c: (elig[c], self.classes_.index(c))) if elig else None
            rows.append(r)
        return pd.DataFrame(rows)

    def margin(self, row: pd.Series, h: str) -> tuple:
        """(M(x; h), state). State explains every undefined value; M is NaN unless h and a competitor are eligible."""
        if self.s_ is None:
            return np.nan, DEGENERATE
        if not row["valid"]:
            return np.nan, INVALID
        if row[f"state_{h}"] != SUPPORTED:
            return np.nan, HYP_NOT_SUPPORTED
        comp = [row[f"D_{c}"] for c in self.classes_ if c != h and np.isfinite(row[f"D_{c}"])]
        if not comp:
            return np.nan, UNTESTABLE
        m = float(min(comp) - row[f"D_{h}"])
        if m >= self.config.tau:
            return m, SEPARATED
        if m <= -self.config.tau:
            return m, CONFLICT
        return m, NOT_SEPARATED


def decide(model: DistinguishabilityV2, ev: pd.DataFrame, y_hat: Sequence[str]) -> pd.DataFrame:
    """Conflict-aware decision per query (see module docstring). Returns outcome, set and the reason chain."""
    cfg = model.config
    rows = []
    for (_, r), yh in zip(ev.iterrows(), y_hat):
        m, st = model.margin(r, yh)
        base = {"y_hat": yh, "margin": m, "separability_state": st, "detectability": r["detectability"]}
        if st in (INVALID, DEGENERATE) or r["out_of_support"]:
            rows.append({**base, "outcome": UNRESOLVED, "set": "", "reason": OOS if r["out_of_support"] else st})
            continue
        if st in (HYP_NOT_SUPPORTED, UNTESTABLE):
            outc = UNRESOLVED if st == HYP_NOT_SUPPORTED else cfg.untestable_outcome
            rows.append({**base, "outcome": outc, "set": yh if outc == AMBIGUITY_SET else "", "reason": st})
            continue
        best = r["evidence_best_class"]
        if r["detectability"] == DET_NOT and yh != cfg.normal_class:
            rows.append({**base, "outcome": AMBIGUITY_SET, "set": "|".join(sorted({yh, cfg.normal_class})),
                         "reason": "EVENT_PREDICTED_BUT_NOT_DETECTABLE"})
            continue
        if r["detectability"] == DET_DETECTED and yh == cfg.normal_class:
            events = {c: r[f"D_{c}"] for c in model.classes_ if c != cfg.normal_class and np.isfinite(r[f"D_{c}"])}
            alt = min(events, key=events.get) if events else None
            rows.append({**base, "outcome": AMBIGUITY_SET if alt else UNRESOLVED,
                         "set": "|".join(sorted({yh, alt})) if alt else "", "reason": "ANOMALY_DETECTED_BUT_PREDICTED_NORMAL"})
            continue
        if st == SEPARATED:
            rows.append({**base, "outcome": SPECIFIC, "set": yh, "reason": SEPARATED})
        elif st == NOT_SEPARATED:
            close = {c for c in model.classes_ if np.isfinite(r[f"D_{c}"]) and r[f"D_{c}"] - r[f"D_{yh}"] < cfg.tau}
            rows.append({**base, "outcome": AMBIGUITY_SET, "set": "|".join(sorted(close | {yh}, key=model.classes_.index)),
                         "reason": NOT_SEPARATED})
        else:  # CONFLICT: evidence separates another class from y_hat; neither source is assumed correct
            rows.append({**base, "outcome": AMBIGUITY_SET, "set": "|".join(sorted({yh, best}, key=model.classes_.index)),
                         "reason": CONFLICT})
    return pd.DataFrame(rows)


def matched_selection(scores, specific_eligible, window_ids, target: float, salt: str):
    """Exact-count matched coverage (PA-1 rule, reused unchanged): SPECIFIC for the top ceil(target * n) eligible rows by
    score; None (NOT_ESTIMABLE) if fewer rows are eligible. Ranking score is supplied by the compared method."""
    from .experiments.primary_protocol import exact_count_selection
    return exact_count_selection(np.asarray(scores, float), np.asarray(specific_eligible, bool),
                                 np.asarray(window_ids), float(target), salt)


def eligibility_from_groups(class_of_group: Dict[str, str], query_group: str, classes: List[str], m: int) -> Dict[str, str]:
    """Sufficiency states without features (used to assess estimability from metadata alone)."""
    out = {}
    for c in classes:
        n = sum(1 for g, cc in class_of_group.items() if cc == c and g != query_group)
        out[c] = SUPPORTED if n >= m else (INSUFFICIENT if n else UNSUPPORTED)
    return out
