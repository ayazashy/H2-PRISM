"""Closed-form tests for h2prism.metrics. SYNTHETIC values only."""

import numpy as np
import pytest

from h2prism.metrics import (ambiguity_summary, classification_summary, coverage_and_risk, log_loss,
                             multiclass_brier, rank_match_selection, risk_coverage_curve, top_label_ece)


def test_coverage_and_risk_definition():
    r = coverage_and_risk(["SPECIFIC", "SPECIFIC", "AMBIGUITY_SET", "UNRESOLVED"], ["A", "B", None, None],
                          ["A", "A", "A", "B"])
    assert r["coverage"] == 0.5 and r["selective_risk"] == 0.5
    assert r["n_ambiguity"] == 1 and r["n_unresolved"] == 1


def test_risk_undefined_without_specific():
    r = coverage_and_risk(["UNRESOLVED"], [None], ["A"])
    assert np.isnan(r["selective_risk"]) and r["selective_risk_defined"] is False


def test_risk_coverage_curve_ties_grouped():
    c = risk_coverage_curve([0.9, 0.9, 0.5, 0.1], [True, False, True, True])
    assert c["n_accepted"].tolist() == [2, 3, 4]
    assert c["selective_risk"].tolist() == pytest.approx([0.5, 1 / 3, 0.25])


def test_rank_match_selection_reports_tie_overshoot():
    m = rank_match_selection([0.9, 0.8, 0.8, 0.1], 0.5)
    assert m.tolist() == [True, True, True, False]  # realised coverage 0.75 > 0.5 target


def test_proper_scores():
    P = np.array([[1.0, 0.0], [0.5, 0.5]])
    assert multiclass_brier(P, [0, 0]) == pytest.approx((0 + 0.5) / 2)
    assert log_loss(P, [0, 1]) == pytest.approx(-np.log(0.5) / 2)


def test_ece_perfectly_calibrated_bin():
    P = np.array([[0.75, 0.25]] * 4)
    assert top_label_ece(P, [0, 0, 0, 1])["ece"] == pytest.approx(0.0)


def test_classification_summary_reports_absent_classes():
    s = classification_summary(["A", "A"], ["A", "B"], ["A", "B", "C"])
    assert s["classes_absent_from_y_true"] == ["B", "C"]
    pc = s["per_class"].set_index("class")
    assert np.isnan(pc.loc["C", "recall"])


def test_ambiguity_summary():
    s = ambiguity_summary(["AMBIGUITY_SET", "AMBIGUITY_SET", "SPECIFIC"], ["A|B", "A|B|C", ""], ["B", "D", "A"],
                          n_classes=4)
    assert s["inclusion_rate"] == 0.5 and s["mean_size"] == 2.5 and s["broad_rate"] == 0.5
