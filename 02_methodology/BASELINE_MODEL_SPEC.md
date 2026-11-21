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
