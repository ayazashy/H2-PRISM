"""Tests for h2prism.distinguishability (F7). SYNTHETIC / hand-calculated fixtures only."""

import numpy as np
import pandas as pd
import pytest

from h2prism.distinguishability import (FLAG_INSUFFICIENT_CLASS, FLAG_INVALID, FLAG_LOW_DIVERSITY,
                                        FLAG_OUT_OF_SUPPORT, FLAG_SPARSE, FLAG_ZERO_DISTANCE, DConfig,
                                        EmpiricalSupport)


def _fit(x, y, fam=None, scen=None, classes=("A", "B"), **cfg):
    x = np.asarray(x, dtype=float).reshape(-1, 1)
    n = len(x)
    fam = fam if fam is not None else [f"f{i}" for i in range(n)]
    scen = scen if scen is not None else [f"s{i}" for i in range(n)]
    base = dict(min_class_reference=1, min_distinct_scenarios=1, low_support_min_top_count=1)
    base.update(cfg)
    return EmpiricalSupport(DConfig(**base)).fit(x, y, fam, scen, list(classes))


def _q(es, xq, fam=("none",)):
    xq = np.asarray(xq, dtype=float).reshape(-1, 1)
    fam = list(fam) * len(xq) if len(fam) == 1 else list(fam)
    return es.compute(xq, query_families=fam)


REF_X = [0, 1, 2, 10, 11]
REF_Y = ["A", "A", "A", "B", "B"]


def test_hand_calculated_support_k3_and_k4():
    r3 = _q(_fit(REF_X, REF_Y, k=3), [0.5]).iloc[0]
    assert (r3["q_A"], r3["q_B"], r3["D"]) == pytest.approx((1.0, 0.0, 1.0))
    r4 = _q(_fit(REF_X, REF_Y, k=4), [0.5]).iloc[0]
    assert (r4["q_A"], r4["q_B"], r4["D"]) == pytest.approx((0.75, 0.25, 0.5))
    assert r4["k_effective"] == 4 and r4["top_class"] == "A" and r4["second_class"] == "B"


def test_inverse_distance_weighting_hand_calculated():
    es = _fit([0.0, 2.0], ["A", "B"], k=2, weighting="inverse_distance")
    r = _q(es, [0.5]).iloc[0]
    # standardisation scales both distances by the same sigma, so the ratio is preserved
    wA, wB = 1 / 0.5, 1 / 1.5
    assert r["q_A"] == pytest.approx(wA / (wA + wB))


def test_ties_are_included_and_order_invariant():
    es = _fit([-1.0, 1.0], ["A", "B"], k=1)
    r = _q(es, [0.0]).iloc[0]
    assert r["k_effective"] == 2 and r["D"] == pytest.approx(0.0)


def test_permutation_invariance():
    rng = np.random.default_rng(0)
    x = rng.normal(size=60)
    y = np.where(rng.random(60) > 0.5, "A", "B")
    fam = [f"f{i % 7}" for i in range(60)]
    scen = [f"s{i % 11}" for i in range(60)]
    q = rng.normal(size=15)
    qf = [f"f{i % 7}" for i in range(15)]
    a = _fit(x, y, fam, scen, k=9).compute(q.reshape(-1, 1), qf)
    p = rng.permutation(60)
    b = _fit(x[p], y[p], [fam[i] for i in p], [scen[i] for i in p], k=9).compute(q.reshape(-1, 1), qf)
    pd.testing.assert_frame_equal(a, b)


def test_reference_label_sensitivity():
    es1 = _fit(REF_X, REF_Y, k=3)
    es2 = _fit(REF_X, ["B", "A", "A", "B", "B"], k=3)
    assert _q(es1, [0.1]).iloc[0]["q_A"] != _q(es2, [0.1]).iloc[0]["q_A"]


def test_query_family_excluded():
    es = _fit(REF_X, REF_Y, fam=["fa", "fa", "fa", "fb", "fb"], k=2, min_class_reference=1)
    r = _q(es, [0.5], fam=["fa"]).iloc[0]
    assert r["q_A"] == 0.0 and r["q_B"] == 1.0
    assert FLAG_INSUFFICIENT_CLASS in r["support_flags"]
    assert r["n_available_reference"] == 2
    with pytest.raises(ValueError):
        es.compute(np.array([[0.5]]))  # exclusion requested but no query family given


def test_fewer_than_k_references():
    r = _q(_fit([0.0, 1.0], ["A", "B"], k=5), [0.2]).iloc[0]
    assert FLAG_SPARSE in r["support_flags"] and r["k_effective"] == 2


def test_missing_class_gives_zero_not_nan():
    es = _fit(REF_X, REF_Y, classes=("A", "B", "C"), k=3, min_class_reference=1)
    r = _q(es, [0.5]).iloc[0]
    assert r["q_C"] == 0.0 and not np.isnan(r["D"])
    assert FLAG_INSUFFICIENT_CLASS in r["support_flags"]


def test_zero_distance_and_duplicates_flagged():
    es = _fit([1.0, 1.0, 5.0], ["A", "A", "B"], k=2)
    r = _q(es, [1.0]).iloc[0]
    assert FLAG_ZERO_DISTANCE in r["support_flags"] and r["q_A"] == 1.0


def test_scenario_dominance_and_low_diversity():
    x = [0.0, 0.01, 0.02, 0.03, 5.0, 5.1]
    es = _fit(x, ["A", "A", "A", "A", "B", "B"], scen=["s1"] * 4 + ["s2", "s3"], k=4, min_distinct_scenarios=2)
    r = _q(es, [0.015]).iloc[0]
    assert r["max_scenario_share"] == 1.0 and r["n_distinct_scenarios"] == 1
    assert FLAG_LOW_DIVERSITY in r["support_flags"]
    assert r["D"] == 1.0  # high D from a single scenario: flagged, not trusted


def test_prior_correction():
    x = [0.0] * 10
    y = ["A"] * 8 + ["B"] * 2
    r0 = _q(_fit(x, y, k=10), [0.0]).iloc[0]
    r1 = _q(_fit(x, y, k=10, prior_correction=True), [0.0]).iloc[0]
    assert r0["q_A"] == pytest.approx(0.8)
    assert r1["q_A"] == pytest.approx(0.5) and r1["D"] == pytest.approx(0.0)


def test_invalid_query_features():
    r = _q(_fit(REF_X, REF_Y, k=3), [np.nan]).iloc[0]
    assert r["support_flags"] == FLAG_INVALID and np.isnan(r["D"])


def test_reference_rejects_non_finite():
    with pytest.raises(ValueError):
        _fit([0.0, np.nan], ["A", "B"])


def test_training_only_standardisation():
    es = _fit(REF_X, REF_Y, k=3)
    mu = es.mu_.copy()
    _q(es, [1e6, -1e6])
    assert np.array_equal(es.mu_, mu)
    assert es.mu_[0] == pytest.approx(np.mean(REF_X))


def test_separated_vs_overlapping_classes():
    rng = np.random.default_rng(1)

    def mean_D(sep):
        x = np.r_[rng.normal(0, 1, 200), rng.normal(sep, 1, 200)]
        y = ["A"] * 200 + ["B"] * 200
        es = _fit(x, y, k=15)
        qx = np.r_[rng.normal(0, 1, 50), rng.normal(sep, 1, 50)]
        return _q(es, qx, fam=["q"] * 100)["D"].mean()

    assert mean_D(6.0) > 0.9 > mean_D(0.0)


def test_out_of_support_threshold_from_reference_only():
    rng = np.random.default_rng(2)
    x = rng.normal(0, 1, 120)
    y = np.where(x > 0, "A", "B")
    fam = [f"f{i % 6}" for i in range(120)]
    es = _fit(x, y, fam=fam, k=5)
    thr = es.fit_out_of_support_threshold(0.99)
    es2 = EmpiricalSupport(DConfig(k=5, min_class_reference=1, min_distinct_scenarios=1, low_support_min_top_count=1,
                                   out_of_support_distance=thr)).fit(x.reshape(-1, 1), y, fam, fam, ["A", "B"])
    r = _q(es2, [50.0], fam=["q"]).iloc[0]
    assert FLAG_OUT_OF_SUPPORT in r["support_flags"]


def test_deterministic():
    es = _fit(REF_X, REF_Y, k=3)
    pd.testing.assert_frame_equal(_q(es, [0.3, 7.0]), _q(es, [0.3, 7.0]))
