"""
End-to-end integration on a SYNTHETIC multi-family dataset (F13 step 120).

raw-like frames -> validation -> windows -> features -> grouped RF (outer folds by family)
-> development-only calibration choice -> D(x) (outer-train reference) -> comparators
-> policy with development thresholds -> coverage/risk.  Nothing here is a research result.
"""

import numpy as np
import pandas as pd

from h2prism.baseline import GroupedRunConfig, make_random_forest, run_grouped_evaluation
from h2prism.calibration import fit_calibrator, select_calibration
from h2prism.comparators import compute_comparators
from h2prism.distinguishability import DConfig, EmpiricalSupport
from h2prism.features import extract_features, model_feature_columns, table_sha256
from h2prism.io import build_time_axis, find_invalid_intervals, validate_scenario_frame
from h2prism.metrics import coverage_and_risk
from h2prism.policy import PolicyConfig, apply_policy
from h2prism.splits import assert_group_disjoint
from h2prism.windows import WindowConfig, generate_windows
from synthetic_fixtures import CLASSES, family_round_robin_folds, toy_scenario_frame

CH = ["PS1", "MFS1"]


def _build_feature_table():
    tables = []
    seed = 0
    for cls in CLASSES:
        for f in range(3):
            for s in range(2):
                seed += 1
                df = toy_scenario_frame(240, cls, None if cls == "NORMAL" else 0, seed=seed, channels=CH,
                                        level=5.0 + 0.05 * f)
                ax = build_time_axis(df, assumed_dt_s=1.0, assumption_source="synthetic")
                rep = validate_scenario_frame(df, CH, ax)
                assert rep.ok
                scen = {"file": f"syn/{cls}_{f}_{s}", "Scenario_ID": f"SYN_{cls}_{f}_{s}",
                        "Scenario_Family_ID": f"SYN_FAM_{cls}_{f}", "label_raw": cls, "label_mapped": cls,
                        "phase": "n/a", "topology": "n/a", "eligible_primary": True}
                wm = generate_windows(df, ax, scen, WindowConfig(60, 30, 60, "row_level", "exclude"),
                                      find_invalid_intervals(df, CH))
                tables.append(extract_features(df, ax, wm, CH, ["mean", "std", "slope", "last_minus_first"]))
    return pd.concat(tables, ignore_index=True)


def test_end_to_end_synthetic_pipeline_is_leakage_safe_and_deterministic():
    t1 = _build_feature_table()
    t2 = _build_feature_table()
    assert table_sha256(t1) == table_sha256(t2)
    feats = model_feature_columns(t1)
    folds = family_round_robin_folds(t1, 3)
    cfg = GroupedRunConfig(classes=CLASSES, param_grid=[{"n_estimators": 25, "min_samples_leaf": 1,
                                                         "max_features": "sqrt"}],
                           inner_n_splits=2, seed=0, model_name="rf_synthetic")
    run = run_grouped_evaluation(t1, feats, folds, make_random_forest, cfg)
    preds, inner = run["predictions"], run["inner_oof"]
    pcols = [f"p_raw_{c}" for c in CLASSES]
    decisions = []
    for fold in folds:
        dev = inner[inner["outer_fold"] == fold.fold_id]
        te = preds[preds["outer_fold"] == fold.fold_id]
        assert_group_disjoint(dev["Scenario_Family_ID"], te["Scenario_Family_ID"])
        ydev = np.array([CLASSES.index(v) for v in dev["y_true"]])
        choice = select_calibration(dev[pcols].to_numpy(), ydev, dev["Scenario_Family_ID"], 4, n_splits=2)
        cal = fit_calibrator(choice["selected_method"], dev[pcols].to_numpy(), ydev, 4)
        Pte = cal.transform(te[pcols].to_numpy())
        ref = t1[t1["Scenario_ID"].isin(fold.train_scenarios)]
        es = EmpiricalSupport(DConfig(k=5, min_class_reference=1)).fit(
            ref[feats].to_numpy(), ref["label_mapped"], ref["Scenario_Family_ID"], ref["Scenario_ID"], CLASSES)
        tq = t1.set_index("window_id").loc[te["window_id"]]
        sup = es.compute(tq[feats].to_numpy(), query_families=tq["Scenario_Family_ID"].to_numpy())
        comp = compute_comparators(Pte, sup["D"].to_numpy())
        pol = PolicyConfig(config_id="SYNTHETIC_DEV", tau_accept=0.6, ambiguity_mass=0.9, max_set_size=2,
                           singleton_handling="expand_to_two", threshold_source="development")
        dec = apply_policy(Pte, comp["C"].to_numpy(), CLASSES, pol, flags=sup["support_flags"].tolist())
        dec["y_true"] = te["y_true"].to_numpy()
        decisions.append(dec)
    d = pd.concat(decisions, ignore_index=True)
    r = coverage_and_risk(d["policy_outcome"], d["y_pred_specific"], d["y_true"])
    assert r["n_eligible"] == len(t1)
    assert r["n_specific"] + r["n_ambiguity"] + r["n_unresolved"] == r["n_eligible"]
    assert 0.0 <= r["coverage"] <= 1.0
