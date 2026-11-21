# Leakage Test Report (F13), pre-experiment

**Status:** all 16 leakage boundaries were reviewed; none is unresolved. Full table: `06_audit_preparation/final_acceptance/FINAL_CODE_AND_METHOD_AUDIT.md` §3.

| Leakage path | Executable check | Where |
| --- | --- | --- |
| Family / topology / run overlap between development and test | `assert_group_disjoint` (runtime); preflight `fold_family_isolation`, `fold_topology_isolation` | runner, preflight |
| Pinned inner folds differ from the splits actually used | preflight `inner_folds_match_runner` | preflight |
| Duplicate raw content across runs | per-file SHA-256 (57/57 unique per realization) | preflight + scan |
| Metadata or provenance used as features | `assert_no_metadata_features`; exact registered feature set | runner; test_interface_contract.py |
| Outer-test labels influencing decisions | shuffled-label invariance of all decisions and tie selections | test_outer_test_labels_do_not_influence_decisions |
| Thresholds, calibration, D reference, combined score fitted on test data | development-only code paths; label-free rank matching | code review; tie tests |
| Synthetic output in the genuine results directory | refused under `03_results/`; tests write to tmp paths | test_synthetic_output_refused_inside_results_dir |

**Validity risks (not leakage):** run fingerprint (limitation 10) and DELAY/start-up confounding (limitation 11).
