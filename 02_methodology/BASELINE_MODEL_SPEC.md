<<<<<<< HEAD
# Baseline Classifier Specification (Faisal F5)

The frozen baseline is a 300-tree `RandomForestClassifier` with
`max_features="sqrt"`, `min_samples_leaf=2`,
`class_weight="balanced_subsample"`, and seed 2026 plus the outer-fold ID.
Hyperparameters are fixed in the versioned configuration rather than tuned
against the outer test set. Fit only on eligible windows from the outer
training topologies. Per-window sample weights make the total contribution of
each `Scenario_Family_ID` equal before class balancing.

Raw class probabilities and predictions are retained. The final outer-fold
prediction table additionally stores the development-selected calibrated
probabilities, but baseline classification metrics are separately identified
as raw or calibrated. All metrics are calculated at the window level and
reported with family-level summaries because windows within simulations are
not independent.

Executable implementation: `src/h2prism/evaluation.py` and
`src/h2prism/experiments.py`. Outputs:
`03_results/BASELINE_RESULTS.csv`,
`03_results/OUTER_PREDICTIONS.csv`, and
`03_results/figures/fig3_confusion_matrix_stage2.png`.
=======
# Baseline Model Specification (F5)

- **Status:** SPECIFIED from `src/h2prism/baseline.py`; IMPLEMENTED and TESTED (`tests/test_baseline.py`).
- **Results:** POST_EXPERIMENT (not produced).

| Item | Specification |
| --- | --- |
| Model | `RandomForestClassifier(n_estimators, min_samples_leaf, max_features, class_weight="balanced_subsample", random_state=20261104, n_jobs=1)` |
| Grid (8 settings) | n_estimators {300, 500} × min_samples_leaf {1, 5} × max_features {sqrt, 0.3} |
| Selection (`select_on_development`) | Inner leave-one-topology-out within the outer-training topologies (2 inner splits). Criterion: macro-F1 over present classes. Tie-break: log loss, then grid order. Inner out-of-fold predictions only |
| Refit | Selected setting refitted on all development windows of the fold |
| Probabilities | `_aligned_proba`: columns aligned to the class order [NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY]; a class absent from training gets 0. The runner fails earlier if a training class is missing |
| Prediction | ŷ = argmax p, ties to the lower class index |
| Resampling | none (no window duplication across folds) |
| Outputs | per-fold `predictions.csv` (`p_raw_*`, `p_cal_*`), `selection.csv` (grid × inner metrics) |
| Leakage | the outer-test fold is never used for selection, refit or calibration |

**Secondary baseline:** logistic regression, A14, `src/h2prism/secondary_baseline.py`. It runs as a separate supporting experiment and is not part of the primary runner.
>>>>>>> 6fee8a0a58a0773ad0ac6f0d5eb1f71ae4d984ed
