"""
H2-PRISM supporting ablation arms (Task A16 -- Ahmed; executed only through Faisal's
policy interface h2prism.policy.apply_policy).

STATUS: IMPLEMENTED + TESTED (synthetic). Not executed on project data. Arms are
pre-specified; thresholds come from a development-only configuration supplied by
Faisal (``threshold_source: development`` is enforced by PolicyConfig). This module
never fits thresholds, never resamples families and never computes inferential
statistics -- those remain F10/F11 responsibilities.

Supported arms (score definitions; higher = more willing to accept SPECIFIC):
  confidence_only          s = C(x)                        (method B)
  margin_only              s = M(x)                        (method B2)
  neg_entropy_only         s = -H(x)                       (method B3)
  confidence_and_margin    s = C(x); SPECIFIC also requires M(x) >= tau_margin
  no_D_policy              same as ``score_column`` arm but tau_D disabled
Inputs are saved prediction tables (F12 prediction schema), never raw features.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd

from ..comparators import compute_comparators
from ..metrics import coverage_and_risk
from ..policy import PolicyConfig, apply_policy

ARMS = ("confidence_only", "margin_only", "neg_entropy_only", "confidence_and_margin", "no_D_policy")


def _prob_matrix(pred: pd.DataFrame, classes: Sequence[str], prob_prefix: str) -> np.ndarray:
    cols = [f"{prob_prefix}{c}" for c in classes]
    miss = [c for c in cols if c not in pred.columns]
    if miss:
        raise KeyError(f"prediction table missing probability columns: {miss}")
    return pred[cols].to_numpy(dtype=float)


def run_arm(pred: pd.DataFrame, classes: Sequence[str], arm: str, policy: PolicyConfig,
            prob_prefix: str = "p_calibrated_", tau_margin: Optional[float] = None,
            score_column: Optional[str] = None) -> pd.DataFrame:
    if arm not in ARMS:
        raise ValueError(f"unknown arm '{arm}'")
    if "y_true" in pred.columns:
        pred_in = pred.drop(columns=["y_true"])  # labels are not visible to the decision step
    else:
        pred_in = pred
    P = _prob_matrix(pred_in, classes, prob_prefix)
    comp = compute_comparators(P)
    flags = pred_in["support_flags"].fillna("").tolist() if "support_flags" in pred_in else None
    if arm == "confidence_only":
        score, cfg = comp["C"].to_numpy(), replace(policy, tau_D=None)
    elif arm == "margin_only":
        score, cfg = comp["M"].to_numpy(), replace(policy, tau_D=None)
    elif arm == "neg_entropy_only":
        score, cfg = comp["neg_H"].to_numpy(), replace(policy, tau_D=None)
    elif arm == "confidence_and_margin":
        if tau_margin is None:
            raise ValueError("confidence_and_margin requires tau_margin from the development config")
        score = np.where(comp["M"].to_numpy() >= tau_margin, comp["C"].to_numpy(), -np.inf)
        score = np.where(np.isfinite(score), score, policy.tau_accept - 1.0)
        cfg = replace(policy, tau_D=None)
    else:  # no_D_policy
        if not score_column or score_column not in pred_in.columns:
            raise ValueError("no_D_policy requires score_column naming a development-fitted no-D score (e.g. s_C_minus_D)")
        score, cfg = pred_in[score_column].to_numpy(dtype=float), replace(policy, tau_D=None)
    dec = apply_policy(P, score, classes, cfg, flags=flags)
    out = pred[[c for c in ("window_id", "Scenario_ID", "Scenario_Family_ID", "outer_fold") if c in pred.columns]].copy()
    out["arm"] = arm
    out["acceptance_score"] = score
    for c in dec.columns:
        out[c] = dec[c].to_numpy()
    return out


def family_summary(decisions: pd.DataFrame, y_true: Sequence, group_col: str = "Scenario_Family_ID") -> pd.DataFrame:
    """Descriptive per-family coverage/risk for one arm (no resampling, no inference)."""
    d = decisions.copy()
    d["y_true"] = list(y_true)
    rows = []
    for (arm, g), part in d.groupby(["arm", group_col], sort=True):
        r = coverage_and_risk(part["policy_outcome"], part["y_pred_specific"], part["y_true"])
        r.update({"arm": arm, group_col: g})
        rows.append(r)
    return pd.DataFrame(rows)
