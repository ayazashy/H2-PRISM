# L20 — Stage-2 (H2-SimNet, Faisal) import conflict: resolution record

## Interface incompatibilities

The Stage-2 branch (9fa470c) was merged into a tree that already held the frozen Center/F3 code (db6876a; tag h2prism-center-baseline-v1). Three conflicts resulted.

| # | Shared path | Frozen Center / registered content | Stage-2 content (9fa470c) | Effect |
|---|---|---|---|---|
| 1 | `src/h2prism/windows.py` | `WindowConfig`, `generate_windows`, `check_window_manifest`, `map_rows_to_primary`, `PRIMARY_CLASSES`, `BOUNDARY_*` (sha256 c4660efb…) | `SENSOR_CHANNELS`, `TARGET_CLASSES`, `LABEL_MAP`, `map_target_class`, `build_window_dataset` (sha256 25784162…) | 6eddd4a kept the frozen file, so `evaluation.py` raised `ImportError: TARGET_CLASSES` |
| 2 | `h2prism.experiments` | package `src/h2prism/experiments/` (registered primary protocol, fixtures, ablations) | module `src/h2prism/experiments.py` (Stage-2 runner) | The package shadows the module, so the runner was unreachable whatever happened to `windows.py` |
| 3 | `configs/frozen_evaluation_config.yaml` and 7 methodology specifications (BASELINE_MODEL_SPEC, DIAGNOSTIC_PROBLEM_FORMULATION, D_STATISTIC_DESIGN_DECISION, GROUPED_EVALUATION_PROTOCOL, PROBABILITY_CALIBRATION_SPEC, SELECTIVE_DIAGNOSTIC_POLICY, UNCERTAINTY_AND_DISTINGUISHABILITY_COMPARATORS) | pointer to the single frozen configuration `06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml` (final-protocol-1.1); `owner_freeze_attestation: NOT_RECORDED # Faisal (F4)` | Stage-2 frozen config 1.0.2 (blob sha256 6ccda2e4… at 9fa470c) and Stage-2 versions of the 7 specs | `simnet_experiments._read_config` rejects the registered config, so `test_accepted_frozen_config_is_supported` fails |

The two windowing APIs share no public name. Conflicts 1 and 2 are naming conflicts only. Conflict 3 is a conflict of methodology: two frozen evaluation definitions claim the same path.

## Resolved (software; no methodological change)

- **Windowing module.** `src/h2prism/simnet_windows.py` is the Stage-2 `windows.py` from 9fa470c, byte-identical (sha256 25784162…). The frozen `src/h2prism/windows.py` is unchanged (c4660efb…).
- **Stage-2 runner.** `src/h2prism/experiments.py` was renamed (git mv) to `src/h2prism/simnet_experiments.py`.
- **Edits to Stage-2 files.** Six lines across four files changed, imports and one provenance path only:
  - `evaluation.py` (1 line);
  - `simnet_experiments.py` (2 lines: the import, and the source-provenance path `windows.py` → `simnet_windows.py`, which hashes the same bytes as before);
  - `scripts/run_experiments.py` (1 line);
  - `tests/test_faisal_pipeline.py` (2 lines).
  - No algorithm, threshold, label mapping or default changed.
- **Regression test.** `tests/test_windows_modules.py` checks that both window files keep their exact bytes, that their public APIs stay disjoint, and that the Stage-2 modules import.
- **Result.** `tests/test_faisal_pipeline.py` now collects (previously a collection error) and passes 7 of 8 tests. The frozen windowing and protocol suites pass unchanged.

## Still BLOCKED (methodological and governance decision)

`test_accepted_frozen_config_is_supported` fails because the frozen evaluation configuration at the shared path is the registered one, not Stage-2 config 1.0.2. Restoring 1.0.2, under any path, would create a second "frozen evaluation" source of truth. That contradicts the explicit single-source rule in `configs/frozen_evaluation_config.yaml`. It also needs a decision on the 7 Stage-2 methodology specifications that 6eddd4a replaced with the Center versions.

**Approval required** from the project lead and the Stage-2/F4 owner (Faisal). Choose one:

- **(a) Retire Stage-2 config 1.0.2.** It is superseded by `FINAL_EXPERIMENT_CONFIG.yaml` final-protocol-1.1. Mark `test_accepted_frozen_config_is_supported` and the Stage-2 runner historical, and keep the code importable for reference.
- **(b) Retain it as a separately named legacy workflow.** Restore config 1.0.2 verbatim as, for example, `configs/simnet_stage2_evaluation_config_1_0_2.yaml`, labelled LEGACY and non-registered. Point `simnet_experiments.DEFAULT_CONFIG` at it. Restore the 7 Stage-2 specifications under labelled historical names.
- **(c) Another owner-defined arrangement.**

Until a decision is recorded, the single failing test is the accurate state and is not suppressed.
