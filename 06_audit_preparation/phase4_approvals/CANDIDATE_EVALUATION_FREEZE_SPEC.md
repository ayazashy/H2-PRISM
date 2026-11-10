# Candidate Evaluation Freeze Specification (CANDIDATE_NOT_APPROVED)

The YAML below is the proposed content of `configs/frozen_evaluation_config.yaml`. It has **not** been written there. Every `PENDING_*` value needs the named decision. Recommended values are shown as comments and are **not** substituted.

```yaml
status: CANDIDATE_NOT_APPROVED
dataset:
  source: "zenodo:10.5281/zenodo.17871393 V2"
  archive_md5: 15bc64a3afc9e2990c9db66eb37617de
  manifest: {file: 06_audit_preparation/pre_experiment_review/CANDIDATE_SCENARIO_MANIFEST.csv, sha256: 29b8b3cc018a043e6d03aa0413e9453d8f4302543800328f3710561d2c025e6b, version: PENDING_Y-D07}
  label_mapping: {file: 06_audit_preparation/pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml, sha256: 61a3182b04e0fd7c9728945f07ab7eee13fe8fb75a8f4b55a999244cb49c1f18, approval: PENDING_A-D05}
  family_view: PENDING_Y-D04            # recommended: family_primary (+ family_extended sensitivity)
  realization: PENDING_F-D01            # recommended: NOISE_ADDED_RELEASE primary, CLEAN_SIMULATION secondary
  classes: [NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY]
  excluded_runs: [leakG4brokenC1 x3 (compound), brokenC1G5_weak x3 (annotation conflict)]
splits:
  outer: {file: 06_audit_preparation/pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv, sha256: 3b21d8231a40245140f32aa6cb5193e3f45b05bd57cbb079ccccd69aafa8b1dd, design: PENDING_F-D02}  # LOTO
  inner: {file: 06_audit_preparation/pre_experiment_review/CANDIDATE_INNER_FOLDS.csv, sha256: ebff65da38a5e70e45e1f1e0c4303b518ba13f9874aed06a3a191bf9c0963c5b, scheme: PENDING_F-D03}  # LOTO_within_train
windows:
  window_s: PENDING_F-D04               # recommended 60
  stride_s: PENDING_F-D04               # recommended 30 (60/60 sensitivity)
  min_samples: PENDING_F-D04            # recommended = window_s (1 s sampling verified)
  label_mode: row_level
  pre_event_policy: PENDING_F-D05       # recommended exclude (label_normal as secondary)
  time_axis: {column_or_index: Timestamp}
features:
  register: {file: 02_methodology/FEATURE_DEFINITION_REGISTER.csv, sha256: 3dd5e927e3473d01168b39ca7539d51fd5d599621bb6263bae20bfdc25bfc137}
  selection: PENDING_F-D06              # recommended all 128; offset-invariant subset = A15 arm
  scaling: fit_on_training_fold_only
model:
  primary: random_forest
  grid: {n_estimators: [300, 500], min_samples_leaf: [1, 5], max_features: [sqrt, 0.3]}  # plan F5; approval PENDING_F-D14
  class_weight: balanced_subsample
  selection: {criterion: macro_f1, tie_break: log_loss, data: inner_oof_only}
  secondary_reference: logistic_regression (configs/secondary_baseline.yaml; PENDING_F-D18)
calibration: {candidates: [none, sigmoid, isotonic], criterion: PENDING_F-D09, data: inner_oof_only}  # recommended log_loss
distinguishability:
  k: PENDING_F-D08                      # recommended 25 (10, 50 sensitivity)
  weighting: PENDING_F-D08              # recommended uniform
  prior_correction: PENDING_F-D08       # recommended false (true as sensitivity)
  exclude_query_family: true
  flags: {min_class_reference: PENDING_F-D08, min_distinct_scenarios: PENDING_F-D08, low_support_min_top_count: PENDING_F-D08, out_of_support_quantile: PENDING_F-D08}
comparators: [C, M, neg_H, D]
combined_scores: {s_C: "LR[logit C, M, -H, D]", s_C_minus_D: "LR[logit C, M, -H]", fit: cross_fitted_development_only, implementation: NOT_YET_IMPLEMENTED}
policy:
  candidate_source: PENDING_F-D11       # recommended p_only
  singleton_handling: PENDING_F-D11     # recommended unresolved
  max_set_size: PENDING_F-D11           # recommended 2
  unresolved_flags: [OUT_OF_SUPPORT, INVALID_FEATURES, NO_REFERENCE]
  specific_blocking_flags: PENDING_F-D11  # recommended [LOW_SCENARIO_DIVERSITY]
  thresholds: {source: development, rule: PENDING_F-D12, target_coverage_primary: 0.80, secondary: [0.60, 0.90]}
evaluation:
  metrics: [coverage, selective_risk, ambiguity_inclusion_and_size, unresolved_rate, accuracy, macro_f1_present_classes, log_loss, brier, ece]
  weighting_and_uncertainty: PENDING_F-D13   # recommended paired family bootstrap (primary map), no topology inference
  practical_significance: PENDING_A-D04       # recommended: effect sizes only
  per_class_reporting: PENDING_F-D07          # NORMAL/FAULT/DELAY descriptive only
seeds: {global: 20261104}
software: {python: 3.12.1, scikit-learn: 1.7.0, numpy: 2.3.1, pandas: 2.3.3, scipy: 1.16.0, pyarrow: 25.0.1}
provenance: {required: [git_commit, config_sha256, manifest_sha256, folds_sha256, seed, run_status], tool: tools/research_audit/build_provenance_index.py}
```

**Freeze rule:** this file may be copied to `configs/frozen_evaluation_config.yaml` only when no `PENDING_` value remains and `TEAM_SIGNOFF_CHECKLIST.md` records the approvals. After that, any change requires a change-control entry.
