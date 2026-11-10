"""Protocol amendment PA-1: exact-count matched coverage with a deterministic, label-free tie key."""

import numpy as np
import pytest

from h2prism.experiments.primary_protocol import _rank_threshold, _required_count, exact_count_selection, tie_keys

SALT = "h2prism-pa1-v1"


def ids(n, prefix="w"):
    return np.array([f"{prefix}{i:05d}" for i in range(n)])


def sel(scores, avail=None, target=0.5, wid=None, salt=SALT):
    s = np.asarray(scores, float)
    a = np.ones(len(s), bool) if avail is None else np.asarray(avail, bool)
    return exact_count_selection(s, a, ids(len(s)) if wid is None else wid, target, salt)


def test_all_scores_tied_selects_exact_count():
    m, info = sel(np.ones(10), target=0.3)
    assert m.sum() == 3 and info["realized_coverage"] == 0.3
    assert info["n_tied_at_boundary"] == 10 and info["n_tied_selected"] == 3


def test_partial_ties_at_boundary_keep_strictly_higher_scores():
    s = np.array([0.9, 0.9, 0.7, 0.7, 0.7, 0.7, 0.1, 0.1])
    m, info = sel(s, target=0.5)  # 4 of 8
    assert m[:2].all() and m.sum() == 4 and not m[6:].any()
    assert info["n_tied_at_boundary"] == 4 and info["n_tied_selected"] == 2


def test_row_order_invariance():
    rng = np.random.default_rng(0)
    s = rng.choice([0.2, 0.5, 1.0], size=200)
    w = ids(200)
    m, _ = sel(s, wid=w, target=0.6)
    perm = rng.permutation(200)
    m2, _ = sel(s[perm], wid=w[perm], target=0.6)
    assert set(w[m]) == set(w[perm][m2])


def test_duplicate_scores_resolved_by_key_not_position():
    s = np.full(6, 0.5)
    w = ids(6)
    keys = tie_keys(w, SALT)
    m, _ = sel(s, wid=w, target=0.5)
    assert set(w[m]) == set(w[np.argsort(keys)[:3]])


def test_missing_scores_are_never_selected():
    s = np.array([np.nan, 1.0, np.inf * 0, 0.5])
    m, info = sel(s, target=0.5)
    assert m.tolist() == [False, True, False, True] and info["n_eligible_for_specific"] == 2


def test_ineligible_candidates_are_never_selected_even_with_top_scores():
    s = np.array([1.0, 1.0, 0.2, 0.1])
    m, _ = sel(s, avail=[False, True, True, True], target=0.5)
    assert not m[0] and m.sum() == 2


def test_insufficient_eligible_coverage_is_not_estimable():
    m, info = sel(np.ones(10), avail=[True] * 5 + [False] * 5, target=0.8)
    assert m is None and info["requested_count"] == 8 and info["max_attainable_coverage"] == 0.5
    assert info["realized_coverage"] is None


def test_all_ineligible_is_not_estimable():
    m, info = sel(np.ones(4), avail=[False] * 4, target=0.25)
    assert m is None and info["n_eligible_for_specific"] == 0


def test_exact_attainability_boundary():
    m, info = sel(np.ones(10), avail=[True] * 8 + [False] * 2, target=0.8)
    assert m is not None and m.sum() == 8


def test_different_policy_masks_give_identical_counts():
    s = np.array([1.0] * 6 + [0.5] * 4)
    m1, _ = sel(s, avail=[True] * 10, target=0.4)
    m2, _ = sel(s, avail=[True, False] * 5, target=0.4)
    assert m1.sum() == m2.sum() == 4
    assert not m2[1::2].any()


def test_two_methods_with_identical_targets_get_identical_counts():
    rng = np.random.default_rng(1)
    a = rng.choice([0.9, 1.0], 101)  # saturated scores
    b = rng.random(101)
    for t in (0.3, 0.6, 0.8):
        ma, ia = sel(a, target=t)
        mb, ib = sel(b, target=t)
        assert ma.sum() == mb.sum() == _required_count(t, 101)
        assert ia["realized_coverage"] == ib["realized_coverage"]


def test_repeatable_and_platform_independent_key():
    m1, _ = sel(np.ones(50), target=0.4)
    m2, _ = sel(np.ones(50), target=0.4)
    assert (m1 == m2).all()
    # SHA-256 of a UTF-8 string is platform independent; pin one value
    assert tie_keys(["w00000"], SALT)[0] == __import__("hashlib").sha256(b"h2prism-pa1-v1|w00000").hexdigest()


def test_selection_never_reads_labels():
    import inspect
    sig = inspect.signature(exact_count_selection)
    assert not ({"y", "y_true", "labels", "label"} & set(sig.parameters))


def test_hash_key_avoids_identifier_order_bias():
    """window_ids sorted by class (e.g. run IDs grouped by class) would bias a lexicographic tie-break."""
    w = np.array([f"A_run_{i:04d}" for i in range(500)] + [f"B_run_{i:04d}" for i in range(500)])
    cls = np.array([0] * 500 + [1] * 500)
    m, _ = sel(np.ones(1000), wid=w, target=0.5)
    lex = np.argsort(w)[:500]
    assert cls[lex].mean() == 0.0  # lexicographic order would take only class A
    assert 0.4 < cls[m].mean() < 0.6  # salted hash order is not aligned with identifier order


def test_alternative_salts_change_only_tied_members():
    s = np.array([1.0] * 3 + [0.5] * 20 + [0.1] * 7)
    m1, _ = sel(s, target=0.5, salt="a")
    m2, _ = sel(s, target=0.5, salt="b")
    assert m1[:3].all() and m2[:3].all() and not m1[23:].any() and not m2[23:].any()
    assert m1.sum() == m2.sum() == 15


def test_duplicate_window_ids_rejected():
    with pytest.raises(ValueError):
        sel(np.ones(3), wid=np.array(["a", "a", "b"]))


def test_development_threshold_float_robust_count():
    # 0.6 * 10 = 6.000000000000001 must require 6, not 7
    assert _required_count(0.6, 10) == 6 and _required_count(0.8, 10) == 8
    tau, _ = _rank_threshold(np.arange(10, dtype=float), np.ones(10, bool), 0.6)
    assert tau == 4.0
