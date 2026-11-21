# Method-to-Implementation Traceability (A6)

- **Status vocabulary (plan A6):** SPECIFIED, IMPLEMENTED, TESTED, EXECUTED, VALIDATED, DEFERRED, NOT_SUPPORTED.
- Nothing is EXECUTED or VALIDATED: no authorized run exists.
- Every referenced file exists; `tests/test_plan_deliverables.py` checks them.

| Component | Definition | Implementation | Tests | Config keys | Metrics / outputs | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RQ1 primary comparison | STATISTICAL_ANALYSIS_PLAN | primary_protocol.aggregate (COMPARISONS) | test_primary_protocol, test_tie_policy | evaluation.primary_comparison | rq1.csv | Faisal | TESTED |
| RQ2 outcomes | SAP; AMBIGUITY_SET_CONSTRUCTION | aggregate rq2, metrics.ambiguity_summary | test_primary_protocol, test_policy | evaluation.per_class_reporting | rq2.csv, coverage_risk ambiguity_* | Faisal | TESTED |
| Manifest / eligibility | GROUPED_EVALUATION_PROTOCOL | feature_table.normalize_manifest_columns, preflight | test_interface_contract, test_phase6_components | dataset.* | run_manifest preflight | Yazan | TESTED |
| Windows | WINDOWING_SPEC | windows.generate_windows | test_windows | windows.* | window manifest | Faisal | TESTED |
| Features | FEATURE_EXTRACTION_SPEC | features.FEATURE_FUNCTIONS | test_features | features.statistics | feature table hash | Faisal | TESTED |
| Folds | GROUPED_EVALUATION_PROTOCOL, FOLD_VALIDATION_REPORT | splits.validate_outer_folds, inner_group_splits | test_splits, test_primary_protocol | splits.* | preflight checks | Faisal / Yazan | TESTED |
| RF baseline | BASELINE_MODEL_SPEC | baseline.select_on_development | test_baseline | model.* | selection.csv | Faisal | TESTED |
| Calibration | PROBABILITY_CALIBRATION_SPEC | calibration.* | test_baseline, test_primary_protocol | calibration.* | calibration.json, calibration_selection.csv, calibration_reliability.csv | Faisal | TESTED |
| D(x) | DISTINGUISHABILITY_MATHEMATICAL_SPEC | distinguishability.EmpiricalSupport | test_distinguishability | distinguishability.* | predictions D, support_flags | Faisal | TESTED |
| Comparators | UNCERTAINTY_AND_DISTINGUISHABILITY_COMPARATORS | comparators.compute_comparators | test_comparators | evaluation.secondary_comparisons | score_* | Ahmed (A16) / Faisal | TESTED |
| Combined scores | same | combined_score.fit/apply | test_phase6_components | combined_scores.* | score_s_C, score_s_C_minus_D | Faisal | TESTED |
| Policy | DECISION_POLICY_PSEUDOCODE | policy.apply_policy | test_policy | policy_primary, policy_sensitivity_warning_only | decisions_*.csv | Faisal | TESTED |
| Thresholds / PA-1 | POLICY_THRESHOLD_SELECTION | _rank_threshold, exact_count_selection | test_tie_policy | thresholds.* | thresholds.csv, estimability.csv, tie_sensitivity.csv | Faisal | TESTED |
| Family bootstrap | SAP | uncertainty.paired_stratified_bootstrap | test_phase6_components | evaluation.uncertainty | rq1 CIs | Faisal | TESTED |
| Sensitivity analyses (9) | SENSITIVITY_ANALYSIS_SPEC | SENSITIVITY_OVERRIDES | test_primary_protocol | sensitivity_analyses | analysis column | Faisal | TESTED (synthetic); real structural dry run |
| Execution gate | FINAL_EXPERIMENT_CONTRACT | check_authorization | test_primary_protocol | — | run_manifest | Project lead | TESTED |
| Reporting | FIGURE_SPECIFICATION, RESULTS_TABLE_SPECIFICATION | tools/reporting | test_reporting_outputs | configs/reporting_figures.yaml | build manifests | Ahmed | TESTED (synthetic/fixture) |
| Provenance | DATA_PROVENANCE | build_provenance_index, run_manifest | test_research_audit | provenance.required | PROVENANCE_REGISTER | Ahmed | TESTED |
| Leak localisation | — | — | — | — | — | — | NOT_SUPPORTED |
| Physical identifiability | — | — | — | — | — | — | NOT_SUPPORTED |
| Primary / robustness / sensitivity execution | — | runner execute modes | gate tests | — | — | Faisal | DEFERRED (authorization) |
