"""
Leakage, regression and consistency checks on the CANDIDATE_NOT_APPROVED pre-experiment
package (06_audit_preparation/pre_experiment_review). Reads saved artifacts only.
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from h2prism.baseline import outer_folds_from_table
from h2prism.splits import assert_group_disjoint, content_equivalence_groups, validate_outer_folds

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "06_audit_preparation" / "pre_experiment_review"
CLASSES = ["NORMAL", "LEAK", "COMPRESSOR_FAULT", "COMPRESSOR_DELAY"]
pytestmark = pytest.mark.skipif(not (PKG / "CANDIDATE_OUTER_FOLDS.csv").exists(), reason="candidate package not built")


@pytest.fixture(scope="module")
def folds():
    return pd.read_csv(PKG / "CANDIDATE_OUTER_FOLDS.csv")


@pytest.fixture(scope="module")
def manifest():
    return pd.read_csv(PKG / "CANDIDATE_SCENARIO_MANIFEST.csv")


@pytest.mark.parametrize("view", ["family_primary", "family_extended", "family_conservative"])
def test_outer_folds_family_isolated(folds, view):
    r = validate_outer_folds(folds.rename(columns={view: "Scenario_Family_ID"}), required_train_classes=CLASSES)
    assert r.passed, r.issues_frame()
    for k, d in folds.groupby("outer_fold_id"):
        assert_group_disjoint(d.loc[d.split_role == "train", view], d.loc[d.split_role == "test", view])


def test_every_eligible_scenario_once_per_fold_and_no_hidden_exclusions(folds, manifest):
    el = set(manifest.loc[manifest.eligible_primary_candidate, "Scenario_ID"])
    for _, d in folds.groupby("outer_fold_id"):
        assert set(d.Scenario_ID) == el and d.Scenario_ID.is_unique
    excl = manifest[~manifest.eligible_primary_candidate]
    assert set(excl.candidate_primary_class) == {"EXCLUDED_COMPOUND", "EXCLUDED_PENDING_REVIEW"}
    assert (excl.class_note.str.len() > 0).all()


def test_each_topology_tested_once_and_all_classes_tested(folds):
    tests = folds[folds.split_role == "test"]
    assert tests.groupby("outer_fold_id").topology.nunique().eq(1).all()
    assert sorted(tests.topology.unique()) == ["Center", "Downstream", "Upstream"]
    assert tests.groupby("outer_fold_id").target_class.nunique().eq(4).all()


def test_no_byte_identical_file_across_split(folds):
    inv = pd.read_csv(PKG / "CANDIDATE_FILE_INVENTORY.csv")
    files = inv.groupby("candidate_Scenario_ID")["file"].apply(list)
    sha = dict(zip(inv.file, inv.sha256))
    for _, d in folds.groupby("outer_fold_id"):
        tr = {sha[f] for s in d[d.split_role == "train"].Scenario_ID for f in files[s]}
        te = {sha[f] for s in d[d.split_role == "test"].Scenario_ID for f in files[s]}
        assert not (tr & te)


def test_regression_misfiled_leakG4_resolved():
    inv = pd.read_csv(PKG / "CANDIDATE_FILE_INVENTORY.csv").set_index("file")
    for f in ("H2-SimNet-Dataset/H2-SimNet-clean/anomalous-scenarios/parquet/leakG4.parquet",
              "H2-SimNet-Dataset/anomalous-scenarios/parquet/leakG4.parquet"):
        assert inv.loc[f, "candidate_Scenario_ID"] == "CS_UPSTREAM_ASSESTMENT_TRANSIENT_LEAKG4"
        assert inv.loc[f, "realization_type"] == "MISFILED_COPY"
    assert not inv.candidate_Scenario_ID.str.startswith("UNRESOLVED").any()


def test_regression_original_folds_defect_still_detected_if_present():
    orig = pd.read_csv(ROOT / "01_dataset_audit" / "folds.csv")
    if "SCEN_UNKNOWN_UNKNOWN_LEAKG4" not in set(orig.Scenario_ID):
        pytest.skip("original folds changed by owner")
    eq = content_equivalence_groups(pd.read_csv(ROOT / "01_dataset_audit" / "DUPLICATE_EXPORT_AUDIT.csv"))
    codes = set(validate_outer_folds(orig, equivalence=eq).issues_frame().code)
    assert {"FAMILY_IN_TRAIN_AND_TEST", "CONTENT_DUPLICATE_ACROSS_SPLIT"} <= codes


def test_inner_loto_splits_feasible():
    inner = pd.read_csv(PKG / "CANDIDATE_INNER_FOLDS.csv")
    assert inner[inner.scheme == "LOTO_within_train"].feasible.all()


def test_families_never_span_topologies():
    fam = pd.read_csv(PKG / "CANDIDATE_FAMILY_MAP.csv")
    for v in ("family_primary", "family_extended"):
        assert fam.groupby(v).topology.nunique().max() == 1


def test_label_findings_recorded(manifest):
    g56 = manifest[manifest.run_stem == "leakG5G6_overlapped"]
    assert (g56.leak_locations_rowlevel == "G4;G6").all() and g56.filename_vs_label_locations.str.startswith("MISMATCH").all()
    assert (manifest.loc[manifest.run_stem == "brokenC1G5_weak", "candidate_primary_class"] == "EXCLUDED_PENDING_REVIEW").all()
    assert (manifest.loc[manifest.run_stem == "leakG4brokenC1", "candidate_primary_class"] == "EXCLUDED_COMPOUND").all()


def test_candidate_status_everywhere(manifest, folds):
    assert set(manifest.status) == {"CANDIDATE_NOT_APPROVED"} and set(folds.status) == {"CANDIDATE_NOT_APPROVED"}
    y = yaml.safe_load((PKG / "CANDIDATE_LABEL_MAPPING.yaml").read_text(encoding="utf-8"))
    assert y["metadata"]["status"] == "CANDIDATE_NOT_APPROVED"


def test_output_hashes_match_files():
    hashes = json.loads((PKG / "OUTPUT_HASHES.json").read_text(encoding="utf-8"))
    for name, h in hashes.items():
        assert hashlib.sha256((PKG / name).read_bytes()).hexdigest() == h, name


def test_folds_consumable_by_runner_interface(folds):
    of = outer_folds_from_table(folds)
    assert len(of) == 3 and all(set(f.train_scenarios).isdisjoint(f.test_scenarios) for f in of)


def test_inner_splits_independent_and_inside_outer_train(folds):
    """Phase 4 regression: inner train/validation never share a run or family, and stay inside outer-train."""
    inner = pd.read_csv(PKG / "CANDIDATE_INNER_FOLDS.csv")
    fam = pd.read_csv(PKG / "CANDIDATE_FAMILY_MAP.csv").set_index("Scenario_ID")
    for _, r in inner.iterrows():
        tr, va = set(r.train_scenarios.split(";")), set(r.val_scenarios.split(";"))
        assert not (tr & va)
        outer_train = set(folds[(folds.outer_fold_id == r.outer_fold_id) & (folds.split_role == "train")].Scenario_ID)
        assert tr | va <= outer_train
        view = "topology" if r.scheme == "LOTO_within_train" else "family_primary"
        assert not (set(fam.loc[list(tr), view]) & set(fam.loc[list(va), view]))
