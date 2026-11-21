"""X10 / D-05: window-level and per-group risk reported beside the registered group-balanced endpoint."""

import numpy as np

from h2prism.evaluation_metrics import selective_risk_report


def test_saturation_is_flagged_and_window_differences_stay_visible():
    """Two methods select different numbers of windows from an all-wrong NORMAL group (as in arm H): the
    group-balanced risk is identical (1/11) but the window-level risk differs, and the saturation flag is set."""
    groups = np.array(["N"] * 100 + [f"L{i}" for i in range(10) for _ in range(50)], dtype=object)
    wrong = np.array([True] * 100 + [False] * 500)
    sel_a = np.zeros(600, bool); sel_a[:20] = True; sel_a[100:] = True
    sel_b = np.zeros(600, bool); sel_b[:80] = True; sel_b[100:] = True
    a, b = selective_risk_report(sel_a, wrong, groups), selective_risk_report(sel_b, wrong, groups)
    assert a["group_balanced_risk"] == b["group_balanced_risk"] == 1 / 11
    assert a["window_risk"] < b["window_risk"]
    assert a["saturated_by_all_wrong_groups"] and b["saturated_by_all_wrong_groups"] and a["n_all_wrong_groups"] == 1


def test_no_selection_is_not_estimable_not_zero():
    r = selective_risk_report(np.zeros(5, bool), np.ones(5, bool), list("abcde"))
    assert r["n_specific"] == 0 and np.isnan(r["window_risk"]) and np.isnan(r["group_balanced_risk"])


def test_partial_errors_are_not_flagged_as_saturation():
    r = selective_risk_report([True] * 4, [True, False, False, False], ["a", "a", "b", "b"])
    assert r["per_group_risk"] == {"a": 0.5, "b": 0.0} and not r["saturated_by_all_wrong_groups"]
