# Test Results (F13), pre-experiment software validation

- **Status:** pre-experiment portion COMPLETE.
- **Authoritative totals and commands:** `06_audit_preparation/final_acceptance/FINAL_VALIDATION_EVIDENCE.md`, kept up to date with the latest full run.
- This file indexes the suites by component. Experiment-level validation (EXECUTED/VALIDATED results) is POST_EXPERIMENT.

| Component | Suites |
| --- | --- |
| I/O, windows, features | test_io.py, test_windows.py, test_features.py, test_phase6_components.py |
| Splits and folds | test_splits.py, test_dataset_audit.py, test_primary_protocol.py (fold adversarial cases) |
| Baseline, calibration | test_baseline.py, test_pipeline_integration.py |
| D(x) | test_distinguishability.py, test_phase6_components.py |
| Comparators, combined score | test_comparators.py, test_phase6_components.py |
| Policy and thresholds | test_policy.py, test_tie_policy.py |
| Runner end to end, gate, resume, sensitivity paths | test_primary_protocol.py |
| Interface contract | test_interface_contract.py |
| Plan deliverables and governance artifacts | test_plan_deliverables.py |
| Supporting modules (A12–A16) | test_research_audit.py, test_reporting_outputs.py, test_secondary_baseline.py, test_feature_sensitivity.py, test_supporting_ablations.py |
| Config | test_final_config.py, test_candidate_config.py |
