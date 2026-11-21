"""
H2-PRISM three-outcome selective diagnostic policy g(x) (Task F9 -- preparation,
Faisal ownership; Ahmed reviews validity/interpretation).

STATUS: IMPLEMENTED + TESTED (deterministic fixtures). Thresholds are NOT chosen
here. ``PolicyConfig.threshold_source`` must equal "development"; the policy refuses
to run otherwise, so outer-test-derived thresholds cannot be applied by accident.

g(x) is a DECISION, distinct from the classifier output y_hat(x) = argmax_k p_k(x):

  1. invalid probabilities / score            -> UNRESOLVED (INVALID_INPUT / INVALID_SCORE)
  2. any flag in ``unresolved_flags``         -> UNRESOLVED (FLAG:<name>)  e.g. OUT_OF_SUPPORT
  3. s(x) >= tau_accept AND (tau_D is None or D(x) >= tau_D) AND no flag in
     ``specific_blocking_flags``              -> SPECIFIC with y_hat(x)
  4. otherwise build candidate set S(x): classes ordered by p desc (ties -> lower
     class index), smallest prefix with cumulative p >= ambiguity_mass.
       |S| == 1 -> singleton_handling: "expand_to_two" (S = top-2) or "unresolved"
       |S| >= K -> UNRESOLVED (ALL_CLASS_SET_PREVENTED)   (all-class set is uninformative)
       |S| > max_set_size -> UNRESOLVED (SET_TOO_BROAD)
       else -> AMBIGUITY_SET, enforcing 2 <= |S| <= min(max_set_size, K-1)
The policy never receives y_true.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .comparators import ProbabilityValidationError, validate_probabilities
from .metrics import AMBIGUITY_SET, SPECIFIC, UNRESOLVED

SINGLETON_MODES = ("expand_to_two", "unresolved")


@dataclass(frozen=True)
class PolicyConfig:
    config_id: str
    tau_accept: float
    ambiguity_mass: float
    max_set_size: int
    singleton_handling: str
    threshold_source: str
    tau_D: Optional[float] = None
    unresolved_flags: Tuple[str, ...] = ("OUT_OF_SUPPORT", "INVALID_FEATURES", "NO_REFERENCE")
    specific_blocking_flags: Tuple[str, ...] = ()
    # CANDIDATE protocol 2.0 (P2-D; off in protocol 1.1): when the classifier label differs from the evidence-supported
    # hypothesis (D(x) top class), the policy does NOT assume either source is wrong. "ambiguity_pair" returns the two
    # competing hypotheses as an AMBIGUITY_SET (the true class is included whenever either source is right);
    # "unresolved" withholds a decision. Reason code: EVIDENCE_CONFLICT:<classifier>|<evidence>.
    evidence_conflict: Optional[str] = None

    def __post_init__(self) -> None:
        if self.evidence_conflict not in (None, "ambiguity_pair", "unresolved"):
            raise ValueError("evidence_conflict must be None, 'ambiguity_pair' or 'unresolved'")
        if self.threshold_source != "development":
            raise ValueError("threshold_source must be 'development'; outer-test thresholds are prohibited")
        if not 0 < self.ambiguity_mass <= 1:
            raise ValueError("ambiguity_mass must be in (0, 1]")
        if self.max_set_size < 2:
            raise ValueError("max_set_size must be >= 2")
        if self.singleton_handling not in SINGLETON_MODES:
            raise ValueError(f"singleton_handling must be one of {SINGLETON_MODES}")
        if not np.isfinite(self.tau_accept):
            raise ValueError("tau_accept must be finite")
        if self.tau_D is not None and not (0 <= self.tau_D <= 1):
            raise ValueError("tau_D must be in [0, 1]")


def apply_policy(
    P,
    score: Sequence[float],
    classes: Sequence[str],
    config: PolicyConfig,
    D: Optional[Sequence[float]] = None,
    flags: Optional[Sequence[str]] = None,
    evidence_top_class: Optional[Sequence[Optional[str]]] = None,
) -> pd.DataFrame:
    K = len(classes)
    if config.evidence_conflict is not None and evidence_top_class is None:
        raise ValueError("evidence_conflict is set but evidence_top_class was not supplied")
    if K < 2:
        raise ValueError("at least two classes required")
    if config.max_set_size > K - 1 and K > 2:
        raise ValueError(f"max_set_size={config.max_set_size} exceeds K-1={K - 1}")
    P = np.asarray(P, dtype=float)
    n = len(P)
    score = np.asarray(score, dtype=float)
    if len(score) != n:
        raise ValueError("score length mismatch")
    if config.tau_D is not None:
        if D is None:
            raise ValueError("tau_D is set but D was not supplied")
        D = np.asarray(D, dtype=float)
        if len(D) != n:
            raise ValueError("D length mismatch")
    flag_lists = [set(f.split("|")) - {""} if isinstance(f, str) else set() for f in (flags if flags is not None else [""] * n)]
    if len(flag_lists) != n:
        raise ValueError("flags length mismatch")

    row_ok = np.ones(n, dtype=bool)
    try:
        validate_probabilities(P, n_classes=K)
    except ProbabilityValidationError:
        # validate row-wise so one bad row does not abort the batch
        for i in range(n):
            try:
                validate_probabilities(P[i: i + 1], n_classes=K)
            except ProbabilityValidationError:
                row_ok[i] = False

    out_outcome, out_pred, out_set, out_size, out_reason = [], [], [], [], []
    for i in range(n):
        if not row_ok[i]:
            _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [], "INVALID_INPUT")
            continue
        if not np.isfinite(score[i]):
            _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [], "INVALID_SCORE")
            continue
        hit = sorted(flag_lists[i] & set(config.unresolved_flags))
        if hit:
            _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [], "FLAG:" + "+".join(hit))
            continue
        p = P[i]
        order = sorted(range(K), key=lambda c: (-p[c], c))
        if config.evidence_conflict is not None:
            ev = evidence_top_class[i]
            pred = classes[order[0]]
            if ev is not None and isinstance(ev, str) and ev in classes and ev != pred:
                code = f"EVIDENCE_CONFLICT:{pred}|{ev}"
                if config.evidence_conflict == "ambiguity_pair":
                    _emit(out_outcome, out_pred, out_set, out_size, out_reason, AMBIGUITY_SET, None, [pred, ev], code)
                else:
                    _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [], code)
                continue
        why = []
        if score[i] < config.tau_accept:
            why.append("SCORE_BELOW_THRESHOLD")
        if config.tau_D is not None and not (np.isfinite(D[i]) and D[i] >= config.tau_D):
            why.append("D_BELOW_THRESHOLD_OR_UNDEFINED")
        blocked = sorted(flag_lists[i] & set(config.specific_blocking_flags))
        if blocked:
            why.append("FLAG_BLOCKS_SPECIFIC:" + "+".join(blocked))
        if not why:
            _emit(out_outcome, out_pred, out_set, out_size, out_reason, SPECIFIC, classes[order[0]], [], "ACCEPTED")
            continue
        cum, m = 0.0, 0
        for c in order:
            cum += p[c]
            m += 1
            if cum >= config.ambiguity_mass - 1e-12:
                break
        if m == 1:
            if config.singleton_handling == "unresolved":
                _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [],
                      "SPECIFIC_REJECTED_SINGLE_CANDIDATE;" + ";".join(why))
                continue
            m = 2
        if m >= K:
            _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [],
                  "ALL_CLASS_SET_PREVENTED;" + ";".join(why))
            continue
        if m > config.max_set_size:
            _emit(out_outcome, out_pred, out_set, out_size, out_reason, UNRESOLVED, None, [],
                  "SET_TOO_BROAD;" + ";".join(why))
            continue
        _emit(out_outcome, out_pred, out_set, out_size, out_reason, AMBIGUITY_SET, None,
              [classes[c] for c in order[:m]], ";".join(why))

    return pd.DataFrame({
        "policy_outcome": out_outcome,
        "y_pred_specific": out_pred,
        "ambiguity_set": ["|".join(s) for s in out_set],
        "set_size": out_size,
        "reason_code": out_reason,
        "policy_config_id": config.config_id,
    })


def _emit(o, p, s, z, r, outcome, pred, cset, reason):
    o.append(outcome)
    p.append(pred)
    s.append(cset)
    z.append(len(cset) if outcome == AMBIGUITY_SET else (1 if outcome == SPECIFIC else 0))
    r.append(reason)
