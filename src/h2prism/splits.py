"""
H2-PRISM grouped split validation and inner development splits (Task F4 -- preparation).

STATUS: IMPLEMENTED + TESTED (synthetic) and EXECUTED read-only against
01_dataset_audit/folds.csv (see 06_audit_preparation/YAZAN_DATASET_VERIFICATION.md).
This module does NOT choose the evaluation design; it checks a proposed design
against the leakage rules that every plan states:

* Scenario_Family_ID is the primary independence unit -> no family in train and test.
* No Scenario_ID in train and test.
* No content-equivalent file (exact byte duplicate / numerically equivalent export,
  per Yazan's DUPLICATE_EXPORT_AUDIT.csv) on both sides of a split.
* Required training classes present; missing test classes reported, never hidden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np
import pandas as pd

EQUIVALENT_CLASSES = (
    "EXACT_BYTE_DUPLICATE",
    "NUMERICALLY_EQUIVALENT_EXPORT",
    "NUMERIC_EQUIVALENT_DIFF_COLUMNS",
)


@dataclass
class FoldIssue:
    fold: object
    severity: str  # CRITICAL | MAJOR | INFO
    code: str
    detail: str


@dataclass
class FoldValidationResult:
    issues: List[FoldIssue] = field(default_factory=list)
    summary: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def passed(self) -> bool:
        return not any(i.severity in ("CRITICAL", "MAJOR") for i in self.issues)

    def issues_frame(self) -> pd.DataFrame:
        return pd.DataFrame([i.__dict__ for i in self.issues], columns=["fold", "severity", "code", "detail"])


def content_equivalence_groups(duplicate_audit: pd.DataFrame,
                               equivalent_classes: Sequence[str] = EQUIVALENT_CLASSES) -> Dict[str, str]:
    """Union-find over file pairs that the duplicate audit classed as content-equivalent.

    Returns {file: group_representative}. Files with no equivalent partner are absent.
    """
    parent: Dict[str, str] = {}

    def find(a: str) -> str:
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    eq = duplicate_audit[duplicate_audit["duplicate_classification"].isin(equivalent_classes)]
    for a, b in zip(eq["file_a"], eq["file_b"]):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    return {f: find(f) for f in list(parent)}


def validate_outer_folds(
    folds: pd.DataFrame,
    required_train_classes: Optional[Iterable[str]] = None,
    equivalence: Optional[Dict[str, str]] = None,
    fold_col: str = "outer_fold_id",
    role_col: str = "split_role",
    class_col: str = "target_class",
) -> FoldValidationResult:
    """Validate an outer-fold assignment table (one row per file or scenario per fold)."""
    need = [fold_col, role_col, "Scenario_ID", "Scenario_Family_ID", class_col]
    miss = [c for c in need if c not in folds.columns]
    if miss:
        raise KeyError(f"folds table missing columns: {miss}")
    res = FoldValidationResult()
    req = set(required_train_classes or [])
    rows = []
    for k, d in folds.groupby(fold_col, sort=True):
        tr, te = d[d[role_col] == "train"], d[d[role_col] == "test"]
        unknown_roles = set(d[role_col]) - {"train", "test"}
        if unknown_roles:
            res.issues.append(FoldIssue(k, "MAJOR", "UNKNOWN_SPLIT_ROLE", str(sorted(unknown_roles))))
        fam = sorted(set(tr["Scenario_Family_ID"]) & set(te["Scenario_Family_ID"]))
        if fam:
            res.issues.append(FoldIssue(k, "CRITICAL", "FAMILY_IN_TRAIN_AND_TEST",
                                        f"{len(fam)} families on both sides: {fam}"))
        scen = sorted(set(tr["Scenario_ID"]) & set(te["Scenario_ID"]))
        if scen:
            res.issues.append(FoldIssue(k, "CRITICAL", "SCENARIO_IN_TRAIN_AND_TEST", str(scen)))
        if equivalence is not None and "file" in d.columns:
            g_tr = {equivalence[f]: f for f in tr["file"] if f in equivalence}
            g_te = {equivalence[f]: f for f in te["file"] if f in equivalence}
            for g in sorted(set(g_tr) & set(g_te)):
                res.issues.append(FoldIssue(
                    k, "CRITICAL", "CONTENT_DUPLICATE_ACROSS_SPLIT",
                    f"train file {g_tr[g]} is content-equivalent to test file {g_te[g]}"))
        tr_cls, te_cls = set(tr[class_col]), set(te[class_col])
        if req - tr_cls:
            res.issues.append(FoldIssue(k, "MAJOR", "MISSING_TRAIN_CLASS", str(sorted(req - tr_cls))))
        if req - te_cls:
            res.issues.append(FoldIssue(k, "INFO", "MISSING_TEST_CLASS", str(sorted(req - te_cls))))
        if "file" in d.columns:
            multi = d.groupby("Scenario_ID")["file"].nunique()
            if (multi > 1).any():
                res.issues.append(FoldIssue(
                    k, "MAJOR", "MULTIPLE_FILES_PER_SCENARIO",
                    f"{int((multi > 1).sum())} scenarios list >1 file; loading all would double-count windows"))
        for role, part in (("train", tr), ("test", te)):
            per_cls = part.groupby(class_col)["Scenario_ID"].nunique().to_dict()
            fam_cls = part.groupby(class_col)["Scenario_Family_ID"].nunique().to_dict()
            rows.append({"fold": k, "role": role, "n_rows": len(part),
                         "n_scenarios": part["Scenario_ID"].nunique(),
                         "n_families": part["Scenario_Family_ID"].nunique(),
                         "scenarios_per_class": per_cls, "families_per_class": fam_cls})
    res.summary = pd.DataFrame(rows)
    return res


def assert_group_disjoint(train_groups: Iterable, test_groups: Iterable, what: str = "family") -> None:
    """Hard leakage assertion used inside every training routine."""
    overlap = set(train_groups) & set(test_groups)
    if overlap:
        raise AssertionError(f"LEAKAGE: {what} present in both train and test: {sorted(map(str, overlap))[:10]}")


def inner_group_splits(
    groups: Sequence,
    y: Sequence,
    n_splits: int,
    required_classes: Optional[Iterable] = None,
) -> Tuple[List[Tuple[np.ndarray, np.ndarray]], List[str]]:
    """Deterministic grouped K-fold for the development (outer-training) data.

    Groups are assigned to folds by sorted group key in round-robin order, which is
    reproducible and independent of row order. Returns (splits, warnings); a warning
    is emitted for every inner split whose training part lacks a required class
    (classes are never dropped silently).
    """
    groups = np.asarray(groups)
    y = np.asarray(y)
    uniq = sorted(set(groups.tolist()), key=lambda g: str(g))
    if n_splits < 2:
        raise ValueError("n_splits must be >= 2")
    if len(uniq) < n_splits:
        raise ValueError(f"only {len(uniq)} groups available for {n_splits} inner splits")
    assign = {g: i % n_splits for i, g in enumerate(uniq)}
    fold_of = np.array([assign[g] for g in groups.tolist()])
    req = set(required_classes) if required_classes is not None else set(y.tolist())
    splits, warns = [], []
    for k in range(n_splits):
        te = np.flatnonzero(fold_of == k)
        tr = np.flatnonzero(fold_of != k)
        assert_group_disjoint(groups[tr], groups[te], "inner group")
        missing = req - set(y[tr].tolist())
        if missing:
            warns.append(f"inner split {k}: training part lacks classes {sorted(map(str, missing))}")
        splits.append((tr, te))
    return splits, warns
