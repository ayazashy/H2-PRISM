"""Tests for h2prism.splits (F4 leakage assertions). SYNTHETIC fixtures only."""

import pandas as pd
import pytest

from h2prism.splits import (assert_group_disjoint, content_equivalence_groups, inner_group_splits,
                            validate_outer_folds)


def _folds(rows):
    return pd.DataFrame(rows, columns=["outer_fold_id", "split_role", "Scenario_ID", "Scenario_Family_ID",
                                       "target_class", "file"])


def test_clean_folds_pass():
    f = _folds([(1, "train", "S1", "F1", "A", "a"), (1, "train", "S2", "F2", "B", "b"),
                (1, "test", "S3", "F3", "A", "c"), (1, "test", "S4", "F4", "B", "d")])
    r = validate_outer_folds(f, required_train_classes=["A", "B"])
    assert r.passed, r.issues_frame()


def test_family_overlap_is_critical():
    f = _folds([(1, "train", "S1", "F1", "A", "a"), (1, "test", "S2", "F1", "A", "b")])
    r = validate_outer_folds(f)
    assert not r.passed
    assert "FAMILY_IN_TRAIN_AND_TEST" in set(r.issues_frame()["code"])


def test_content_duplicate_across_split_detected():
    dup = pd.DataFrame({"file_a": ["a"], "file_b": ["x"], "duplicate_classification": ["EXACT_BYTE_DUPLICATE"]})
    eq = content_equivalence_groups(dup)
    f = _folds([(1, "train", "S1", "F1", "A", "a"), (1, "test", "S9", "F9", "A", "x")])
    codes = set(validate_outer_folds(f, equivalence=eq).issues_frame()["code"])
    assert "CONTENT_DUPLICATE_ACROSS_SPLIT" in codes


def test_missing_train_class_and_multi_file_scenario():
    f = _folds([(1, "train", "S1", "F1", "A", "a"), (1, "train", "S1", "F1", "A", "a2"),
                (1, "test", "S2", "F2", "B", "b")])
    codes = set(validate_outer_folds(f, required_train_classes=["A", "B"]).issues_frame()["code"])
    assert {"MISSING_TRAIN_CLASS", "MULTIPLE_FILES_PER_SCENARIO", "MISSING_TEST_CLASS"} <= codes


def test_union_find_transitive():
    dup = pd.DataFrame({"file_a": ["a", "b"], "file_b": ["b", "c"],
                        "duplicate_classification": ["NUMERICALLY_EQUIVALENT_EXPORT", "EXACT_BYTE_DUPLICATE"]})
    eq = content_equivalence_groups(dup)
    assert eq["a"] == eq["b"] == eq["c"]


def test_inner_splits_group_disjoint_deterministic_and_warn():
    groups = ["g1", "g1", "g2", "g3", "g3", "g4"]
    y = ["A", "A", "B", "A", "A", "B"]
    s1, w1 = inner_group_splits(groups, y, 2)
    s2, _ = inner_group_splits(list(reversed(groups)), list(reversed(y)), 2)
    for tr, te in s1:
        assert not ({groups[i] for i in tr} & {groups[i] for i in te})
    assert [sorted({groups[i] for i in te}) for _, te in s1] == [["g1", "g3"], ["g2", "g4"]]
    rg = list(reversed(groups))
    assert [sorted({rg[i] for i in te}) for _, te in s2] == [["g1", "g3"], ["g2", "g4"]]
    assert any("lacks classes" in w for w in w1)


def test_assert_group_disjoint_raises():
    with pytest.raises(AssertionError):
        assert_group_disjoint(["F1", "F2"], ["F2"])
