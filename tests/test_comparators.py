"""Closed-form tests for h2prism.comparators (A16). SYNTHETIC values only."""

import numpy as np
import pytest

from h2prism.comparators import (ProbabilityValidationError, compute_comparators, confidence, entropy, logit,
                                 margin, validate_distinguishability, validate_probabilities)

P = np.array([[0.7, 0.2, 0.1, 0.0], [0.25, 0.25, 0.25, 0.25], [1.0, 0.0, 0.0, 0.0], [0.4, 0.4, 0.2, 0.0]])


def test_closed_form_values():
    assert confidence(P).tolist() == pytest.approx([0.7, 0.25, 1.0, 0.4])
    assert margin(P).tolist() == pytest.approx([0.5, 0.0, 1.0, 0.0])
    H = entropy(P)
    assert H[0] == pytest.approx(-(0.7 * np.log(0.7) + 0.2 * np.log(0.2) + 0.1 * np.log(0.1)))
    assert H[1] == pytest.approx(np.log(4))
    assert H[2] == 0.0  # 0 log 0 := 0
    assert entropy(P, normalized=True)[1] == pytest.approx(1.0)


def test_direction_convention():
    df = compute_comparators(P)
    assert (df["neg_H"] == -df["H"]).all()
    assert df["neg_H"].iloc[2] > df["neg_H"].iloc[1]  # certain row ranks above uniform row


def test_validation_rejects_bad_inputs():
    for bad in ([[0.5, 0.6]], [[np.nan, 1.0]], [[1.2, -0.2]], [0.5, 0.5], [[1.0]]):
        with pytest.raises(ProbabilityValidationError):
            validate_probabilities(bad)
    with pytest.raises(ProbabilityValidationError):
        validate_probabilities(P, n_classes=3)


def test_D_validation_and_alignment():
    D = np.array([0.1, np.nan, 1.0, 0.0])
    assert compute_comparators(P, D)["D"].isna().sum() == 1
    with pytest.raises(ValueError):
        validate_distinguishability([1.5])
    with pytest.raises(ValueError):
        validate_distinguishability([np.nan], allow_nan=False)
    with pytest.raises(ValueError):
        compute_comparators(P, D[:2])


def test_logit_clipped_and_finite():
    v = logit([0.0, 0.5, 1.0])
    assert np.isfinite(v).all() and v[1] == pytest.approx(0.0)


def test_deterministic():
    assert compute_comparators(P).equals(compute_comparators(P))
