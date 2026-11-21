# Secondary Baseline Specification (A14)

- **Status:** IMPLEMENTED and TESTED on synthetic fixtures (`tests/test_secondary_baseline.py`). **Not part of the primary runner; results are POST_EXPERIMENT.**
- Split out of `SUPPORTING_MODEL_SPECS_A14_A16.md` §A14, which remains the detailed source.

| Item | Specification |
| --- | --- |
| Model | `StandardScaler → LogisticRegression(C, class_weight=balanced, max_iter=2000)`; the scaler is refit inside every training split |
| Selection | C ∈ {0.01, 0.1, 1, 10}; inner grouped selection by macro-F1, then log loss (shared `baseline.run_grouped_evaluation`) |
| Outputs | F12 prediction schema plus `model_name`, `params`, `seed`, `missing_train_classes`, `run_status` |
| Claims | reference benchmark only; no superiority claim over the RF |

## Reconciliation item (needs a decision; not changed here)

- `configs/secondary_baseline.yaml` is still `DEVELOPMENT_ONLY`, with `inner_n_splits: 3` grouped by `Scenario_Family_ID`.
- The frozen primary protocol uses leave-one-topology-out outer folds and LOTO-within-train inner splits.
- **Faisal must freeze the A14 inner scheme** (recommended: the same LOTO-within-train as F5, for comparability) before a real-data A14 run.
- No real-data A14 entry point is wired until then. This is a scientific choice and is not made here.
