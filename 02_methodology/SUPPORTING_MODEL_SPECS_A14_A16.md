# Ahmed Supporting Modelling Specifications (A14, A15, A16): DRAFT

**Status:** IMPLEMENTED and TESTED on synthetic fixtures only. Not executed on project data. **Faisal technical acceptance is required before any final run.** This file brings together the content the plan assigns to `SECONDARY_BASELINE_SPEC.md`, `FEATURE_SENSITIVITY_PROTOCOL.md` and `SUPPORTING_COMPARATOR_AND_ABLATION_SPEC.md`. Split it into those three files if the owners prefer.

Integration gate (Faisal plan §2.1): source and test review → configuration and fold verification → reproducibility check → output schema and provenance validation → Faisal technical acceptance → Ahmed scientific integration. **None of these gate steps has been completed for A14–A16.**

## A14: Secondary Logistic Regression reference

- Code: `src/h2prism/secondary_baseline.py`. Config: `configs/secondary_baseline.yaml` (DEVELOPMENT_ONLY). Tests: `tests/test_secondary_baseline.py` (5).
- Model: `StandardScaler → LogisticRegression(C, class_weight=balanced)`. The pipeline is refit inside every inner and outer training split.
- Selection: a bounded C grid {0.01, 0.1, 1, 10}. Inner grouped K-fold selects by macro-F1, then log loss as tie-break. This is the same runner as the F5 Random Forest (`baseline.run_grouped_evaluation`), so folds, leakage assertions and the prediction schema are identical by construction.
- Outputs: the F12 prediction columns plus `model_name`, `params`, `seed`, `missing_train_classes` and `run_status`.
- Not permitted: separate splits, modified labels, or any claim of superiority over the Random Forest.

## A15: Feature-representation sensitivity

- Code: `src/h2prism/experiments/feature_sensitivity.py`. Config: `configs/feature_sensitivity.yaml`. Tests: `tests/test_feature_sensitivity.py` (3).
- Arms are resolved by **rule** from the verified feature table: `all`; `offset_invariant` (std, range, last_minus_first, slope, mean_abs_diff, the delta/trend arm aimed at absolute-pressure fingerprinting); and `explicit` channel or statistic lists.
- Every arm uses the same runner, folds and eligible rows (tested). Infeasible arms are reported as NOT_SUPPORTED. Outputs are labelled EXPLORATORY_SECONDARY and cannot choose the primary feature set.
- Before any held-out run: Faisal must approve the arm list, and Yazan must confirm the channels and units.

## A16: Comparators and supporting ablations

- Comparator library: `src/h2prism/comparators.py` (C, M, H, −H, logit, simplex and D validation). This is the single shared implementation required by Faisal F8, so there is no duplicate. Tests: `tests/test_comparators.py` (6).
- Ablation arms: `src/h2prism/experiments/supporting_ablations.py` with `confidence_only` (B), `margin_only` (B2), `neg_entropy_only` (B3), `confidence_and_margin`, and `no_D_policy` (which takes Faisal's development-fitted s_{C−D}). Every arm runs through `policy.apply_policy`. Tests: `tests/test_supporting_ablations.py` (5).
- Thresholds come only from a `PolicyConfig` with `threshold_source: development`. `y_true` is removed before the decision step, and a test checks that decisions do not change when labels are altered.
- Per-family summaries are descriptive. Effect estimates, uncertainty and incremental-value claims stay with F10/F11 (Faisal).
