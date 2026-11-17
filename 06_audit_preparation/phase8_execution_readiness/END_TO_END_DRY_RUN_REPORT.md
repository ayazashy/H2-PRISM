# 02 End-to-End Synthetic Run (artifact class SYNTHETIC_TEST; not research results)

**Fixture:** `src/h2prism/experiments/synthetic_protocol_fixture.py`.
- 3 topologies; 24 eligible runs plus 1 excluded run.
- Per topology: NORMAL 1, LEAK 4 (one weak/strong family), FAULT 2 (one family), DELAY 1 (label ends early, giving post-event rows).
- Two realizations; manifest in the v0.2 schema; LOTO folds; config with status `SYNTHETIC_TEST_CONFIG`.

**Commands (the real CLI, not a parallel workflow):**
```
python tools/experiments/run_primary_protocol.py --make-synthetic-fixture <fx>
python tools/experiments/run_primary_protocol.py --config <fx>/config.yaml --root <fx> --raw-parent <fx>/raw --out <out> --synthetic
```
Result: `COMPLETED` in about 11 s.
- Outputs: `run_manifest.json`, per-fold predictions, thresholds, selection, calibration and decisions, plus `coverage_risk.csv`, `estimability.csv`, `rq1.csv`, `rq2.csv`, `calibration_records.json`.
- Every CSV carries `artifact_class=SYNTHETIC_TEST`.

## Observed behaviour (synthetic, for verification only)

| Check | Observation |
| --- | --- |
| D(x) safeguard | `TOP_CLASS_FEW_INDEPENDENT_RUNS` fired in every development fold (55–70 windows per fold) |
| Primary-policy estimability | development max attainable coverage 0.48, so 0.80 and 0.90 → `NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL`; 0.30 estimable |
| Warning-only secondary | reaches 0.80 / 0.90 in development (fold 2: 0.90 not estimable) |
| RQ1 at 0.80 (primary) | pooled `NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL`: test-side rank matching reached 0.80 in only 1 of 3 folds; no forced comparison |
| Calibration | sigmoid allowed (2 topologies per class in development); fallback to "none" verified with `min_groups_per_class=3` |
| RQ2 | per-class SPECIFIC / AMBIGUITY_SET / UNRESOLVED rates sum to 1; ambiguity sets validated (size 2 ≤ \|S\| ≤ K−1) |
| Score ties | s_C saturates; rank-matched coverage overshoots the target (protocol-defined tie handling) |

## Edge cases (`tests/test_primary_protocol.py`, all passed)

| Required case | Test | Result |
| --- | --- | --- |
| 1 Valid configuration | `test_valid_config_end_to_end` | pass |
| 2 Missing manifest | `test_missing_manifest` | PreflightError |
| 3 Hash mismatch | `test_hash_mismatch` | PreflightError |
| 4 Duplicate family contamination | `test_duplicate_family_across_topologies` | PreflightError |
| 5 Topology leakage | `test_topology_leakage_in_folds` | PreflightError |
| 6 Fitting leakage | `test_outer_test_labels_do_not_influence_decisions` (shuffled outer labels give identical decisions) | pass |
| 7 Invalid event label | `test_invalid_event_label` | PreflightError |
| 8 Insufficient class support | `test_insufficient_class_support_in_training` | PreflightError (MISSING_TRAIN_CLASS) |
| 9 Calibration fallback | `test_calibration_fallback_recorded` | method "none" recorded |
| 10 Sparse-support flag | `test_sparse_support_flag_and_unattainable_primary_target` | pass |
| 11 Unattainable 0.80 | same | NOT_ESTIMABLE recorded |
| 12 Empty SPECIFIC | `test_empty_specific_reports_undefined_risk` | coverage 0, risk undefined |
| 13 Invalid ambiguity set | `test_invalid_ambiguity_set_rejected` | AssertionError |
| 14 Determinism | `test_deterministic_and_resumable` | byte-identical outputs |
| 15 Interrupted run | same (interrupt after fold 1, then resume) | byte-identical to an uninterrupted run |
| 16 Synthetic / real separation | `test_synthetic_output_refused_inside_results_dir` + artifact_class columns | pass |
| 17 Outer test disabled without authorization | `test_outer_test_disabled_without_authorization`, `test_cli_dry_run_never_fits_or_enters_outer_stage` | AuthorizationError; dry run creates no fold outputs |
