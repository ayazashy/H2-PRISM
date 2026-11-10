# Final Validation Evidence (Phase 9; commands run 2026-11-11)

The environment is the repository `.venv` (Python 3.12). Local paths are redacted as `<scratch>`.

## 1. Static checks and the test suite

| Command | Result |
| --- | --- |
| `python -m compileall -q src tools tests scripts` | COMPILE_OK |
| `python -m pytest -q -rs` | **231 passed, 2 skipped, 0 failed** (233 collected; final run after the governance-gate change) |
| Skips | `test_data_loader.py:68`, `:76`: the sample-data fallback is exercised only when raw data is absent (raw data is present). Expected |
| `validate_artifacts.py --spec configs/candidate_artifact_validation.yaml` | PASS 33 |
| `git status 03_results` after the full suite | clean (the test side effect is fixed, D8) |

New or extended suites:
- `test_tie_policy.py`: 17 tests.
- `test_primary_protocol.py`: 16 → 32 tests (includes 6 governance-clearance gate tests).
- `test_interface_contract.py`: 5 tests.

## 2. Tie policy (PA-1): required cases → tests (`tests/test_tie_policy.py` unless noted)

| Case | Test | Result |
| --- | --- | --- |
| All scores tied | `test_all_scores_tied_selects_exact_count` | pass |
| Partial ties at the boundary | `test_partial_ties_at_boundary_keep_strictly_higher_scores` | pass |
| Different row orders | `test_row_order_invariance`; `test_primary_protocol::test_reordered_inputs_give_identical_results` | pass (byte-identical outputs) |
| Duplicate scores | `test_duplicate_scores_resolved_by_key_not_position` | pass |
| Missing scores | `test_missing_scores_are_never_selected` | pass |
| Ineligible candidates | `test_ineligible_candidates_are_never_selected_even_with_top_scores` | pass |
| Insufficient eligible coverage | `test_insufficient_eligible_coverage_is_not_estimable`, `test_exact_attainability_boundary` | pass (NOT_ESTIMABLE, never forced) |
| All ineligible | `test_all_ineligible_is_not_estimable` | pass |
| Different policy masks | `test_different_policy_masks_give_identical_counts` | pass |
| Identical target counts | `test_two_methods_with_identical_targets_get_identical_counts` | pass |
| Repeatability / platform-independent key | `test_repeatable_and_platform_independent_key` (pinned SHA-256 value) | pass |
| Label independence | `test_selection_never_reads_labels`; `test_primary_protocol::test_outer_test_labels_do_not_influence_decisions` (selections identical under shuffled labels) | pass |
| Bias-sensitive tie ordering | `test_hash_key_avoids_identifier_order_bias`: a lexicographic key would select 100% class A; the salted hash gives 40–60% | pass |
| Salt changes only tied members | `test_alternative_salts_change_only_tied_members` | pass |
| Duplicate ids rejected | `test_duplicate_window_ids_rejected` | pass |

## 3. Synthetic end-to-end run (SYNTHETIC_TEST; not research results)

`run_primary_protocol.py --make-synthetic-fixture <scratch>/fx`, then `--synthetic`: **COMPLETED**, 198 test windows across 3 folds.

| Check | Observation |
| --- | --- |
| Matched coverage | primary s_C vs s_C−D, target 0.30, rank-matched: realized coverage 0.30303 vs 0.30303 (before PA-1: 0.45 vs 0.55) |
| Estimability | development max coverage below 0.80 → 0.80 and 0.90 are NOT_ESTIMABLE under the primary policy, with empty numeric fields |
| RQ1 completeness | 5 comparisons × 12 combinations = 60 rows (7 estimable, 5 not, per comparison) |
| Tie sensitivity (5 salts in the fixture) | pooled difference 0.000–0.017 vs primary 0.033. Heavy ties make tie order material on synthetic data, which is why it is reported |
| Calibration fallback, flags, ambiguity validity, determinism, resume, unauthorized execution | covered by the 32 runner tests |

**Adversarial tests that fail as intended** (`tests/test_primary_protocol.py`):
- missing manifest;
- hash mismatch;
- duplicate family across topologies;
- topology leakage;
- invalid label;
- missing training class;
- missing raw file;
- modified raw file;
- wrong manifest schema;
- inconsistent fold ids;
- missing tie rule;
- foreign output directory;
- interrupted run (no aggregates; resume is byte-identical);
- unauthorized execution (AuthorizationError, exit code 2, no fold output);
- missing, partial or non-ATTESTED/WAIVED `governance_clearance` (AuthorizationError, nothing written). A complete authorization still cannot run a non-final config (status check). The gate test also pins the config hash `f788b6d8…`, so the protocol is unchanged.

## 4. Real-data read-only validation (no model fitting, no outer-test scoring)

| Item | noise_added (primary) | clean (robustness) |
| --- | --- | --- |
| Preflight checks | **26/26 PASS** | 26/26 PASS |
| Eligible runs / raw files hash-verified | 51 / 51 | 51 / 51 |
| Windows (NORMAL / LEAK / FAULT / DELAY) | 27,993 (1,995 / 21,921 / 3,984 / 93) | 27,993 |
| Features / non-finite values | 128 / 0 | 128 / 0 |
| Feature table sha256 | `4d1310a6…` (identical to the Phase-8 run: deterministic regeneration) | `3bc7e712…` (identical to Phase 8) |
| Window manifest sha256 | `adcc2f68…` | — |

- **Official archive:** 264/264 files match `RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256`.
- **Manifest:** 57/57 unique hashes per realization; no hash shared between realizations.
- **Duplicates:** 0 duplicate feature vectors in total, 0 across runs, 0 across topologies.
- **Windows:** every window lies in a single run.

## 5. Reproducibility and cross-platform

- **Determinism:** two complete synthetic runs (direct, and interrupted then resumed) produce byte-identical aggregate CSVs. Reversed manifest rows and shuffled fold rows also give byte-identical aggregates.
- **Hashes:** tie keys are SHA-256 over UTF-8; `code_sha256` normalises CRLF; CSV/JSON are written with LF and a fixed float format.
- **Line endings:** `.gitattributes` forces LF for `06_audit_preparation/**/*.{csv,json,yaml}`, which covers the pinned config, the manifest, the folds and the final-acceptance matrix. The config hash therefore survives a Windows checkout.
- **Real preflight:** run twice (Phase 8 and Phase 9); feature-table hashes are identical.
