"""Synthetic invariants of the standard comparators (src/h2prism/reference_comparators.py) and their relation to v2."""

from __future__ import annotations

import numpy as np
import pytest

from h2prism import reference_comparators as rc
from h2prism.distinguishability_v2 import DistinguishabilityV2, V2Config


def blobs(seed=0, n=200, sep=4.0, p=3):
    rng = np.random.default_rng(seed)
    X = np.vstack([rng.normal(0, 1, (n, p)), rng.normal(sep, 1, (n, p))])
    y = np.array(["A"] * n + ["B"] * n, dtype=object)
    return X, y


def test_trust_score_higher_for_correct_than_wrong_predictions():
    X, y = blobs()
    Xq = np.array([[0.0, 0.0, 0.0], [4.0, 4.0, 4.0]])
    right = rc.trust_score(X, y, Xq, ["A", "B"])
    wrong = rc.trust_score(X, y, Xq, ["B", "A"])
    assert (right > 1).all() and (wrong < 1).all()
    assert np.allclose(right * wrong, 1.0)                      # ratio inverts when the prediction is swapped


def test_trust_score_alpha_filter_removes_outlying_reference_points():
    X, y = blobs()
    X = np.vstack([X, [[4.0, 4.0, 4.0]]])                      # one class-A point inside class B
    y = np.append(y, "A")
    q = np.array([[4.0, 4.0, 4.0]])
    assert rc.trust_score(X, y, q, ["B"], alpha=0.0) <= 1.0 + 1e-9
    assert rc.trust_score(X, y, q, ["B"], alpha=0.05, k=10) > 1.0


def test_split_conformal_marginal_coverage_on_exchangeable_data():
    """Finite-sample guarantee: coverage >= 1 - alpha (checked as an average over repetitions)."""
    rng = np.random.default_rng(1)
    cov = []
    for rep in range(200):
        K, n = 4, 300
        logits = rng.normal(0, 1.0, (2 * n, K))
        P = np.exp(logits) / np.exp(logits).sum(1, keepdims=True)
        y = np.array([rng.choice(K, p=p) for p in P])
        for method in ("lac", "aps"):
            r = rc.split_conformal_sets(P[:n], y[:n], P[n:], alpha=0.1, method=method)
            cov.append(r["sets"][np.arange(n), y[n:]].mean())
    assert np.mean(cov) >= 0.9 - 0.01


def test_conformal_unit_scores_count_independent_units_not_windows():
    P = np.full((6, 2), 0.5)
    r = rc.split_conformal_sets(P, [0, 0, 0, 1, 1, 1], P, alpha=0.2, cal_units=["g1", "g1", "g1", "g2", "g2", "g2"])
    assert r["n_calibration_units"] == 2


def test_conformal_too_few_units_gives_full_sets_not_false_confidence():
    """With n units, alpha < 1/(n+1) is unattainable: qhat = inf and every class is in every set."""
    P = np.array([[0.9, 0.1], [0.8, 0.2]])
    r = rc.split_conformal_sets(P, [0, 0], P, alpha=0.1)
    assert np.isinf(r["qhat"]) and r["sets"].all()


def test_mahalanobis_and_knn_scores_flag_out_of_distribution_points():
    X, y = blobs()
    fit = rc.mahalanobis_fit(X, y)
    q_in, q_out = np.array([[0.1, 0.0, -0.1]]), np.array([[30.0, -30.0, 30.0]])
    assert rc.mahalanobis_score(fit, q_out)[0] > 100 * rc.mahalanobis_score(fit, q_in)[0]
    assert rc.knn_distance_score(X, q_out, normalize=False)[0] > rc.knn_distance_score(X, q_in, normalize=False)[0]


def test_ensemble_disagreement_zero_when_members_agree():
    P = np.array([[0.7, 0.3], [0.2, 0.8]])
    assert np.allclose(rc.ensemble_disagreement([P, P, P]), 0.0)
    assert (rc.ensemble_disagreement([P, P[:, ::-1]]) > 0).all()


def test_v2_margin_and_trust_score_share_sign_but_not_ranking():
    """One window per scenario, m = 1, NEW queries (no own-group exclusion): v2's raw distances are nearest-window
    distances, so sign(M) == sign(log TS). The two statistics nevertheless order windows differently (difference vs
    ratio), so they are related but not equivalent."""
    rng = np.random.default_rng(3)
    X = np.vstack([rng.normal(0, 1, (40, 2)), rng.normal(3, 1, (40, 2))])
    y = np.array(["A"] * 40 + ["B"] * 40, dtype=object)
    g = np.array([f"G{i}" for i in range(80)], dtype=object)
    m = DistinguishabilityV2(V2Config(min_groups=1)).fit(X, y, g, np.zeros(80), ["A", "B"])
    Q = rng.normal(1.5, 2.0, (300, 2))
    Zq = (Q[:, m.keep_] - m.med_) / m.scale_
    raw = m._raw_group_dist(Zq)                                  # per-group (= per-window) distances, scaled space
    cls = np.array([m.group_class_[gg] for gg in m.groups_], dtype=object)
    dA, dB = raw[:, cls == "A"].min(1), raw[:, cls == "B"].min(1)
    M_A = dB - dA                                                # v2 margin for hypothesis A (before resolution scaling)
    Zr = (X[:, m.keep_] - m.med_) / m.scale_
    ts_A = rc.trust_score(Zr, y, Zq, ["A"] * len(Q))
    assert np.array_equal(np.sign(M_A), np.sign(np.log(ts_A)))
    from scipy.stats import spearmanr
    rho = spearmanr(M_A, np.log(ts_A)).statistic
    assert 0.5 < rho < 0.9999                                    # strongly related, not identical rankings
