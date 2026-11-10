"""Phase 6 preparation components. SYNTHETIC fixtures only; no real-data training."""

import numpy as np
import pandas as pd
import pytest

from h2prism.calibration import calibration_feasibility
from h2prism.combined_score import CombinedScoreConfig, apply_combined_score, fit_combined_score
from h2prism.distinguishability import FLAG_TOP_CLASS_FEW_RUNS, DConfig, EmpiricalSupport
from h2prism.feature_table import build_feature_table
from h2prism.features import model_feature_columns
from h2prism.uncertainty import paired_stratified_bootstrap, per_stratum_estimates
from h2prism.windows import WindowConfig
from synthetic_fixtures import toy_scenario_frame


# ---------------- D(x) thin-class safeguard
def test_top_class_single_run_is_flagged_even_with_diverse_neighbourhood():
    x = np.array([0.0, 0.01, 0.02, 0.03, 0.05]).reshape(-1, 1)
    y = ["A", "A", "A", "A", "B"]
    fam = ["fA", "fA", "fA", "fA", "fB"]  # all A support comes from one family/run
    es = EmpiricalSupport(DConfig(k=5, min_class_reference=1, min_distinct_scenarios=2, low_support_min_top_count=1)).fit(
        x, y, fam, fam, ["A", "B"])
    r = es.compute(np.array([[0.015]]), query_families=["q"]).iloc[0]
    assert r["D"] == pytest.approx(0.6) and r["n_distinct_scenarios"] == 2  # neighbourhood looks diverse
    assert r["top_class_n_families"] == 1 and FLAG_TOP_CLASS_FEW_RUNS in r["support_flags"]


def test_top_class_two_families_not_flagged():
    x = np.array([0.0, 0.01, 0.02, 0.03]).reshape(-1, 1)
    es = EmpiricalSupport(DConfig(k=4, min_class_reference=1, low_support_min_top_count=1)).fit(
        x, ["A"] * 4, ["f1", "f1", "f2", "f2"], ["s1", "s1", "s2", "s2"], ["A", "B"])
    assert FLAG_TOP_CLASS_FEW_RUNS not in es.compute(np.array([[0.01]]), query_families=["q"]).iloc[0]["support_flags"]


# ---------------- calibration fallback
def test_calibration_feasibility_fallback_to_none():
    y = np.array([0, 0, 1, 1, 2])
    g = np.array(["a", "b", "a", "b", "a"])  # class 2 appears in one group only
    r = calibration_feasibility(y, g, 3)
    assert r["allowed_methods"] == ["none"] and r["groups_per_class"][2] == 1
    ok = calibration_feasibility(np.array([0, 0, 1, 1]), np.array(["a", "b", "a", "b"]), 2)
    assert ok["allowed_methods"] == ["none", "sigmoid"]


# ---------------- combined score
def _dev(n=240, seed=0):
    rng = np.random.default_rng(seed)
    P = rng.dirichlet(np.ones(4), size=n)
    D = rng.random(n)
    correct = (rng.random(n) < P.max(1)).astype(int)
    groups = np.repeat([f"g{i}" for i in range(8)], n // 8)
    return P, D, correct, groups


def test_combined_score_is_cross_fitted_by_group():
    P, D, c, g = _dev()
    cfg = CombinedScoreConfig(include_D=True, n_splits=4, seed=0)
    a = fit_combined_score(P, c, g, cfg, D)
    c2 = c.copy()
    c2[g == "g0"] = 1 - c2[g == "g0"]  # change only group g0's labels
    b = fit_combined_score(P, c2, g, cfg, D)
    assert np.allclose(a["oof_scores"][g == "g0"], b["oof_scores"][g == "g0"])  # its own scores never used its labels
    assert np.isfinite(a["oof_scores"]).all()


def test_combined_score_without_D_ignores_D_and_handles_nan():
    P, D, c, g = _dev()
    cfg0 = CombinedScoreConfig(include_D=False, n_splits=4, seed=0)
    f0 = fit_combined_score(P, c, g, cfg0, D)
    assert np.allclose(apply_combined_score(f0, P[:10], D[:10], False), apply_combined_score(f0, P[:10], D[:10] * 0, False))
    cfg1 = CombinedScoreConfig(include_D=True, n_splits=4, seed=0)
    Dn = D.copy(); Dn[:5] = np.nan
    f1 = fit_combined_score(P, c, g, cfg1, Dn)
    assert f1["n_excluded_undefined"] == 5
    s = apply_combined_score(f1, P[:6], Dn[:6], True)
    assert np.isnan(s[:5]).all() and np.isfinite(s[5])


# ---------------- stratified family bootstrap
def _units():
    return pd.DataFrame({"unit": [f"u{i}" for i in range(9)], "stratum": ["T1"] * 4 + ["T2"] * 4 + ["T3"],
                         "num_a": [1, 2, 0, 1, 3, 1, 0, 2, 1], "den_a": [10] * 9,
                         "num_b": [2, 2, 1, 1, 3, 2, 1, 2, 1], "den_b": [10] * 9})


def test_bootstrap_paired_deterministic_and_stratified():
    a = paired_stratified_bootstrap(_units(), n_boot=500, seed=7)
    b = paired_stratified_bootstrap(_units().sample(frac=1, random_state=3), n_boot=500, seed=7)
    assert a["difference"] == b["difference"] and a["ci_low"] == b["ci_low"]  # row order irrelevant
    assert a["units_per_stratum"] == {"T1": 4, "T2": 4, "T3": 1}
    assert any("T3" in w for w in a["warnings"])
    assert a["ci_low"] <= a["difference"] <= a["ci_high"]


def test_bootstrap_identical_methods_zero_and_rejects_windows():
    u = _units().assign(num_b=lambda d: d.num_a, den_b=lambda d: d.den_a)
    r = paired_stratified_bootstrap(u, n_boot=200, seed=1)
    assert r["difference"] == 0 and r["ci_low"] == 0 and r["ci_high"] == 0
    with pytest.raises(ValueError):
        paired_stratified_bootstrap(pd.concat([u, u.iloc[:1]]), n_boot=10, seed=1)
    assert len(per_stratum_estimates(u)) == 3


# ---------------- manifest-driven feature table
@pytest.fixture
def toy_manifest(tmp_path):
    rows = []
    for i, (cls, onset) in enumerate([("NORMAL", None), ("LEAK", 0), ("COMPRESSOR_FAULT", 0)]):
        for real in ("clean", "noisy"):
            df = toy_scenario_frame(180, cls, onset, seed=i + (10 if real == "noisy" else 0),
                                    channels=("PS1", "PS2"))
            df.index = pd.Index(np.arange(180, dtype=float), name="Timestamp")
            p = tmp_path / real / f"run{i}.parquet"
            p.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(p)
        rows.append({"Scenario_ID": f"CS_T_RUN{i}", "topology": "T", "candidate_primary_class": cls,
                     "eligible_primary_candidate": i != 2 or True, "canonical_clean_file": f"clean/run{i}.parquet",
                     "canonical_noise_added_file": f"noisy/run{i}.parquet", "family_primary": f"FAM_{i}"})
    rows.append({**rows[0], "Scenario_ID": "CS_T_EXCLUDED", "eligible_primary_candidate": False})
    return tmp_path, pd.DataFrame(rows)


def test_feature_table_builder_deterministic_and_leakage_safe(toy_manifest):
    root, man = toy_manifest
    cfg = WindowConfig(60, 30, 60, "row_level", "exclude")
    a = build_feature_table(man, root, "clean", "family_primary", cfg, ["mean", "slope"], channels=["PS1", "PS2"])
    b = build_feature_table(man.iloc[::-1], root, "clean", "family_primary", cfg, ["mean", "slope"], channels=["PS1", "PS2"])
    assert a["feature_table_sha256"] == b["feature_table_sha256"]
    f = a["features"]
    assert "CS_T_EXCLUDED" not in set(f.Scenario_ID)
    assert model_feature_columns(f) == ["PS1__mean", "PS1__slope", "PS2__mean", "PS2__slope"]
    assert (f.groupby("Scenario_ID").Scenario_Family_ID.nunique() == 1).all()
    n = build_feature_table(man, root, "noise_added", "family_primary", cfg, ["mean"], channels=["PS1", "PS2"])
    assert set(n["window_manifest"].file_id.str.split("/").str[0]) == {"noisy"}  # exactly one realization per run


def test_feature_table_requires_decisions(toy_manifest):
    root, man = toy_manifest
    cfg = WindowConfig(60, 30, 60, "row_level", "exclude")
    with pytest.raises(ValueError):
        build_feature_table(man, root, "both", "family_primary", cfg, ["mean"], channels=["PS1"])
    with pytest.raises(KeyError):
        build_feature_table(man, root, "clean", "family_undecided", cfg, ["mean"], channels=["PS1"])
