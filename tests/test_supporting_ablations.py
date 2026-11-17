"""Tests for A16 supporting ablation arms. SYNTHETIC values only; thresholds are test values."""

import numpy as np
import pandas as pd
import pytest

from h2prism.experiments.supporting_ablations import family_summary, run_arm
from h2prism.policy import PolicyConfig

CL = ["A", "B", "C"]
POL = PolicyConfig(config_id="TEST_DEV", tau_accept=0.7, ambiguity_mass=0.9, max_set_size=2,
                   singleton_handling="expand_to_two", threshold_source="development")


def _pred():
    P = np.array([[0.8, 0.15, 0.05], [0.5, 0.45, 0.05], [0.34, 0.33, 0.33], [0.9, 0.1, 0.0]])
    df = pd.DataFrame(P, columns=[f"p_calibrated_{c}" for c in CL])
    df["window_id"] = ["w0", "w1", "w2", "w3"]
    df["Scenario_ID"] = ["s0", "s0", "s1", "s2"]
    df["Scenario_Family_ID"] = ["f0", "f0", "f1", "f2"]
    df["outer_fold"] = 1
    df["y_true"] = ["A", "B", "C", "B"]
    df["support_flags"] = ["", "", "", "OUT_OF_SUPPORT"]
    df["s_C_minus_D"] = [0.9, 0.2, 0.1, 0.95]
    return df


def test_confidence_only_arm():
    d = run_arm(_pred(), CL, "confidence_only", POL)
    assert d["policy_outcome"].tolist() == ["SPECIFIC", "AMBIGUITY_SET", "UNRESOLVED", "UNRESOLVED"]
    assert d.loc[0, "y_pred_specific"] == "A"


def test_confidence_and_margin_requires_dev_threshold():
    with pytest.raises(ValueError):
        run_arm(_pred(), CL, "confidence_and_margin", POL)
    d = run_arm(_pred(), CL, "confidence_and_margin", POL, tau_margin=0.7)
    assert d.loc[0, "policy_outcome"] != "SPECIFIC"  # margin 0.65 < 0.7


def test_no_D_arm_uses_supplied_score_and_ignores_labels():
    p = _pred()
    a = run_arm(p, CL, "no_D_policy", POL, score_column="s_C_minus_D")
    p2 = p.copy()
    p2["y_true"] = ["C", "C", "A", "A"]  # changing labels must not change decisions
    b = run_arm(p2, CL, "no_D_policy", POL, score_column="s_C_minus_D")
    assert a.equals(b)
    with pytest.raises(ValueError):
        run_arm(p, CL, "no_D_policy", POL)


def test_outer_test_thresholds_refused():
    with pytest.raises(ValueError):
        PolicyConfig(config_id="X", tau_accept=0.5, ambiguity_mass=0.9, max_set_size=2,
                     singleton_handling="expand_to_two", threshold_source="outer_test")


def test_family_summary_traceable():
    p = _pred()
    d = run_arm(p, CL, "confidence_only", POL)
    s = family_summary(d, p["y_true"])
    assert set(s["Scenario_Family_ID"]) == {"f0", "f1", "f2"}
    assert s.set_index("Scenario_Family_ID").loc["f0", "coverage"] == 0.5
