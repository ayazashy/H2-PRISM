"""Tests for h2prism.policy (F9). SYNTHETIC values only; thresholds are arbitrary test values."""

import numpy as np
import pytest

from h2prism.policy import PolicyConfig, apply_policy

CL = ["A", "B", "C", "D"]


def cfg(**kw):
    base = dict(config_id="TEST", tau_accept=0.8, ambiguity_mass=0.9, max_set_size=3,
                singleton_handling="expand_to_two", threshold_source="development")
    base.update(kw)
    return PolicyConfig(**base)


def run(P, score, c=None, **kw):
    return apply_policy(np.array(P, dtype=float), score, CL, c or cfg(), **kw)


def test_specific():
    out = run([[0.9, 0.05, 0.05, 0.0]], [0.9])
    assert out.loc[0, "policy_outcome"] == "SPECIFIC" and out.loc[0, "y_pred_specific"] == "A"


def test_valid_ambiguity_set():
    out = run([[0.5, 0.45, 0.05, 0.0]], [0.5])
    assert out.loc[0, "policy_outcome"] == "AMBIGUITY_SET"
    assert out.loc[0, "ambiguity_set"] == "A|B" and out.loc[0, "set_size"] == 2


def test_all_class_prevention():
    out = run([[0.25, 0.25, 0.25, 0.25]], [0.25])
    assert out.loc[0, "policy_outcome"] == "UNRESOLVED"
    assert out.loc[0, "reason_code"].startswith("ALL_CLASS_SET_PREVENTED")


def test_excessive_breadth():
    out = run([[0.4, 0.3, 0.25, 0.05]], [0.4], c=cfg(max_set_size=2))
    assert out.loc[0, "reason_code"].startswith("SET_TOO_BROAD")


def test_out_of_support_never_forced_specific():
    out = run([[0.99, 0.01, 0, 0]], [0.99], flags=["OUT_OF_SUPPORT"])
    assert out.loc[0, "policy_outcome"] == "UNRESOLVED" and "OUT_OF_SUPPORT" in out.loc[0, "reason_code"]


def test_low_support_blocks_specific_when_configured():
    c = cfg(specific_blocking_flags=("LOW_SUPPORT",))
    out = run([[0.95, 0.05, 0, 0]], [0.95], c=c, flags=["LOW_SUPPORT"])
    assert out.loc[0, "policy_outcome"] == "AMBIGUITY_SET"
    assert "FLAG_BLOCKS_SPECIFIC:LOW_SUPPORT" in out.loc[0, "reason_code"]


def test_singleton_handling_modes():
    P = [[0.95, 0.05, 0, 0]]
    assert run(P, [0.1]).loc[0, "ambiguity_set"] == "A|B"
    out = run(P, [0.1], c=cfg(singleton_handling="unresolved"))
    assert out.loc[0, "policy_outcome"] == "UNRESOLVED"


def test_D_gate():
    c = cfg(tau_D=0.5)
    P = [[0.9, 0.1, 0, 0]] * 3
    out = run(P, [0.9] * 3, c=c, D=[0.6, 0.4, np.nan])
    assert out["policy_outcome"].tolist() == ["SPECIFIC", "AMBIGUITY_SET", "AMBIGUITY_SET"]


def test_invalid_input_isolated_per_row():
    out = run([[0.9, 0.1, 0, 0], [0.9, 0.9, 0, 0], [0.9, 0.1, 0, 0]], [0.9, 0.9, np.nan])
    assert out["reason_code"].tolist()[1:] == ["INVALID_INPUT", "INVALID_SCORE"]
    assert out.loc[0, "policy_outcome"] == "SPECIFIC"


def test_thresholds_must_come_from_development():
    with pytest.raises(ValueError):
        cfg(threshold_source="outer_test")
    with pytest.raises(ValueError):
        apply_policy(np.array([[1, 0, 0, 0.0]]), [1.0], CL, cfg(max_set_size=4))


def test_deterministic_and_label_free():
    P = np.random.default_rng(0).dirichlet(np.ones(4), size=50)
    s = P.max(axis=1)
    a, b = run(P, s), run(P, s)
    assert a.equals(b)
    import inspect
    assert "y_true" not in inspect.signature(apply_policy).parameters
