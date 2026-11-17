"""Constructed counterexamples for the candidate evidence statistic E_h(x) versus the registered D(x).

Each case states the scientific situation, the behaviour E_h must show, and (where informative) what the original
D(x) does in the same situation. No real data is used.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from h2prism.distinguishability import DConfig, EmpiricalSupport  # noqa: E402
from h2prism.evidence_margin import (FLAG_FEW_UNITS, FLAG_OOS, FLAG_UNSUPPORTED, EvidenceConfig,  # noqa: E402
                                     EvidenceMargin)

CL = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
RNG = np.random.default_rng(7)


def _cluster(center, n, unit, label, sd=0.05):
    return RNG.normal(center, sd, (n, 2)), [label] * n, [unit] * n


def _ref(*clusters):
    X = np.vstack([c[0] for c in clusters])
    y = sum((c[1] for c in clusters), [])
    u = sum((c[2] for c in clusters), [])
    return X, y, u


def _em(X, y, u, **kw):
    return EvidenceMargin(EvidenceConfig(k=kw.pop("k", 20), **kw)).fit(X, y, u, CL)


# LEAK evidence from three independent scenarios around (0,0); NORMAL from two independent scenarios around (5,5)
BASE = [_cluster((0, 0), 30, "G_LEAK_A", "LEAK"), _cluster((0.1, 0), 30, "G_LEAK_B", "LEAK"),
        _cluster((0, 0.1), 30, "G_LEAK_C", "LEAK"), _cluster((5, 5), 30, "G_NORM_A", "NORMAL"),
        _cluster((5.1, 5), 30, "G_NORM_B", "NORMAL")]


def test_wrong_classifier_with_correct_neighbour_evidence_is_negative():
    em = _em(*_ref(*BASE), out_of_support_quantile=1.0)
    r = em.compute([[0.05, 0.05]], ["NORMAL"], ["G_QUERY"]).iloc[0]  # classifier says NORMAL; evidence says LEAK
    assert r.E < 0 and r.evidence_top_class == "LEAK"


def test_correct_classifier_with_conflicting_evidence_is_a_conflict_not_a_verdict():
    # true class LEAK, classifier says LEAK, but the query sits among NORMAL references (shifted configuration)
    em = _em(*_ref(*BASE), out_of_support_quantile=1.0)
    r = em.compute([[5.05, 5.0]], ["LEAK"], ["G_QUERY"]).iloc[0]
    assert r.E < 0 and r.evidence_top_class == "NORMAL"  # negative = disagreement; the statistic cannot know who is right


def test_replicated_scenario_is_one_independent_unit_while_original_D_reports_full_support():
    # one LEAK scenario simulated in two topologies: two families, ONE independence group
    clusters = [_cluster((0, 0), 30, "G_S1", "LEAK"), _cluster((0.05, 0), 30, "G_S1", "LEAK"),
                _cluster((5, 5), 30, "G_N1", "NORMAL"), _cluster((5, 5.1), 30, "G_N2", "NORMAL")]
    X, y, u = _ref(*clusters)
    em = _em(X, y, u, out_of_support_quantile=1.0)
    r = em.compute([[0.02, 0.0]], ["LEAK"], ["G_QUERY"]).iloc[0]
    assert np.isnan(r.E) and r.flag == FLAG_FEW_UNITS and r.n_units == 1
    fams = ["F_T1"] * 30 + ["F_T2"] * 30 + ["F_N1"] * 30 + ["F_N2"] * 30
    scen = ["CS_T1_S1"] * 30 + ["CS_T2_S1"] * 30 + ["CS_T1_N1"] * 30 + ["CS_T1_N2"] * 30
    d = EmpiricalSupport(DConfig(k=20, min_class_reference=5, min_top_class_families=2)).fit(X, y, fams, scen, CL).compute(
        np.array([[0.02, 0.0]]), query_families=["OTHER"]).iloc[0]
    assert d.D == 1.0 and "TOP_CLASS_FEW_INDEPENDENT_RUNS" not in d.support_flags  # original: maximal, unflagged


def test_unsupported_hypothesis_is_undefined():
    em = _em(*_ref(*BASE), out_of_support_quantile=1.0)
    r = em.compute([[0, 0]], ["COMPRESSOR_DELAY"], ["G_QUERY"]).iloc[0]  # no DELAY reference at all
    assert np.isnan(r.E) and r.flag == FLAG_UNSUPPORTED


def test_query_unit_exclusion_removes_its_own_scenario_from_the_evidence():
    clusters = [_cluster((0, 0), 30, "G_ONLY_DELAY", "COMPRESSOR_DELAY")] + BASE
    em = _em(*_ref(*clusters), out_of_support_quantile=1.0)
    r = em.compute([[0, 0]], ["COMPRESSOR_DELAY"], ["G_ONLY_DELAY"]).iloc[0]  # the only DELAY scenario is the query's own
    assert np.isnan(r.E) and r.flag == FLAG_UNSUPPORTED


def test_out_of_distribution_observation_is_undefined():
    em = _em(*_ref(*BASE), out_of_support_quantile=0.99)
    r = em.compute([[40.0, -40.0]], ["LEAK"], ["G_QUERY"]).iloc[0]
    assert np.isnan(r.E) and r.flag == FLAG_OOS


def test_highly_similar_competing_hypotheses_give_a_margin_near_zero():
    clusters = [_cluster((0, 0), 30, "G_L1", "LEAK", sd=0.3), _cluster((0, 0), 30, "G_L2", "LEAK", sd=0.3),
                _cluster((0, 0), 30, "G_F1", "COMPRESSOR_FAULT", sd=0.3), _cluster((0, 0), 30, "G_F2", "COMPRESSOR_FAULT", sd=0.3)]
    em = _em(*_ref(*clusters), k=60, out_of_support_quantile=1.0)
    r = em.compute([[0, 0]], ["LEAK"], ["G_QUERY"]).iloc[0]
    assert abs(r.E) <= 0.35 and r.n_units == 4


def test_correct_and_supported_case_is_positive_and_bounded():
    em = _em(*_ref(*BASE), out_of_support_quantile=1.0)
    r = em.compute([[0.03, 0.03]], ["LEAK"], ["G_QUERY"]).iloc[0]
    assert 0 < r.E <= 1 and r.n_units >= 2


def test_original_D_is_unchanged_by_the_candidate():
    import inspect
    import h2prism.distinguishability as dmod
    src = inspect.getsource(dmod.EmpiricalSupport._one)
    assert "D = float(q[order[0]] - q[order[1]])" in src  # the registered definition is kept verbatim


def test_input_validation():
    with pytest.raises(ValueError):
        EvidenceConfig(k=0)
    em = _em(*_ref(*BASE), out_of_support_quantile=1.0)
    with pytest.raises(ValueError):
        em.compute([[0, 0]], ["LEAK", "NORMAL"], ["G"])
