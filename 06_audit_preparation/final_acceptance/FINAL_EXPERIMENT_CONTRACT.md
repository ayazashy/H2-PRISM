# Final Experiment Contract

The machine-checked schemas are in `configs/interface_contracts.yaml` v2.0.0, enforced by `tests/test_interface_contract.py`. This page summarises the contract and maps the method to the code.

## 1. Pinned inputs (verified by preflight; any mismatch → PreflightError)

| Input | File | SHA-256 |
| --- | --- | --- |
| Config | `06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml` (final-protocol-1.1) | `f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae` |
| Manifest v0.2 (57 runs, 51 eligible) | `06_audit_preparation/phase6_resolution/CANDIDATE_MANIFEST_V02.csv` | `36bcbaf97bb17659995f393884d1dcde3bbca9236c3dcdcc6e7651e61538fb59` |
| Outer folds (LOTO) | `pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv` | `3b21d8231a40245140f32aa6cb5193e3f45b05bd57cbb079ccccd69aafa8b1dd` |
| Inner folds | `pre_experiment_review/CANDIDATE_INNER_FOLDS.csv` | `ebff65da38a5e70e45e1f1e0c4303b518ba13f9874aed06a3a191bf9c0963c5b` |
| Label mapping | `pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml` | `61a3182b04e0fd7c9728945f07ab7eee13fe8fb75a8f4b55a999244cb49c1f18` |
| Feature register | `02_methodology/FEATURE_DEFINITION_REGISTER.csv` | `3dd5e927e3473d01168b39ca7539d51fd5d599621bb6263bae20bfdc25bfc137` |
| Raw files | `data/raw/H2-SimNet-Dataset/...` (gitignored; Zenodo V2) | per-file `sha256_noise_added` / `sha256_clean` in the manifest |
| Expected derived tables | noise_added feature table / clean feature table | `4d1310a6…` / `3bc7e712…` (27,993 windows × 128 features each) |

## 2. Entry point

The only entry point is `tools/experiments/run_primary_protocol.py`. Modes are mutually exclusive.

| Flag | Mode | Artifact class | Fits models | Outer test | Gate |
| --- | --- | --- | --- | --- | --- |
| `--dry-run` (default) | preflight | PREFLIGHT_ONLY | no | no | none |
| `--synthetic` | synthetic | SYNTHETIC_TEST | yes | yes (synthetic) | config status `SYNTHETIC_TEST_CONFIG`; refused under `03_results/` |
| `--execute-primary` | execute | PRIMARY_EXPERIMENT (noise_added) | yes | yes | authorization YAML (scope + config_sha256 + authorized_by + date) |
| `--execute-robustness` | execute | ROBUSTNESS_EXPERIMENT (clean) | yes | yes | same, scope ROBUSTNESS_EXPERIMENT |
| `--make-synthetic-fixture DIR` | fixture | — | no | no | — |

Exit code 2 means refusal (PreflightError or AuthorizationError).

## 3. Method → implementation map (supports A6 and F12)

| Method step (config key) | Module / function |
| --- | --- |
| Windows 60 s / 30 s, row labels, pre-event excluded (`windows`) | `windows.py`, `feature_table.build_feature_table` |
| 16 channels × 8 statistics (`features`) | `features.py`; runner exact-set check |
| LOTO outer, LOTO-within-train inner (`splits`) | `splits.validate_outer_folds`, `assert_group_disjoint`; runner |
| RF grid selection by macro-F1 (`model`) | `baseline.select_on_development` |
| Calibration none/sigmoid with feasibility rule (`calibration`) | `calibration.calibration_feasibility`, `select_calibration`, `fit_calibrator` |
| D(x): k=25 tie-inclusive, own family excluded, flags, OOS q=0.99 (`distinguishability`) | `distinguishability.EmpiricalSupport` |
| C, M, −H, D comparators | `comparators.compute_comparators` |
| s_C = LR[logit C, M, −H, D]; s_C−D without D (`combined_scores`) | `combined_score.fit_combined_score` / `apply_combined_score` |
| Primary and warning-only policy (`policy_primary`, `policy_sensitivity_warning_only`) | `policy.apply_policy` |
| Development thresholds, targets 0.80 / 0.60 / 0.90 (`thresholds`) | `primary_protocol._rank_threshold` |
| Matched coverage PA-1 (`thresholds.matched_coverage`) | `primary_protocol.exact_count_selection`, `tie_keys` |
| Coverage, selective risk, ambiguity, unresolved | `metrics.coverage_and_risk`, `ambiguity_summary` |
| Paired family bootstrap by topology (`evaluation.uncertainty`) | `uncertainty.paired_stratified_bootstrap` |

## 4. Outputs (per run directory)

- `run_manifest.json`: artifact_class, status (RUNNING / COMPLETED / PREFLIGHT_PASSED), run_key, config/code/feature hashes, input hashes (manifest, folds, mapping, register), git commit, seed, preflight checks, prohibited claims.
- `folds/fold_k/`: `predictions.csv` (p_raw, p_cal, D, flags, support counts, six scores), `thresholds.csv`, `selection.csv`, `calibration.json`, `decision_index.json`, `decisions_nnn.csv`, `tie_sensitivity_counts.csv`, `DONE.json`.
- Aggregates, written only when COMPLETED:
  - `coverage_risk.csv`: every method × variant × target × mode.
  - `estimability.csv`: per fold; requested, realized and tied counts.
  - `rq1.csv`: 5 comparisons × 2 variants × 3 targets × 2 modes, all rows present. Requested target, realized coverages, gap, effect, CI, units.
  - `rq2.csv`: per class, with reporting role.
  - `tie_sensitivity.csv`: secondary.
  - `calibration_records.json`.
- **Representation rules:**
  - NOT_ESTIMABLE rows keep empty numeric fields (never 0).
  - Undefined risk (n_specific = 0) is NaN with `selective_risk_defined = False`.
  - The D(x) flags and the class-specific family and scenario support (`top_class_n_families`, `n_distinct_scenarios`) are kept per window.
  - Per-topology results come from the fold columns. Pooled results are conditional on the three simulated topologies.

## 5. Safeguards (enforced)

- **Fail closed** on any pinned-hash mismatch, schema error, class or label error, family/topology/run overlap, unknown flag, missing tie rule, feature-set mismatch, non-finite feature, duplicate window_id, or foreign output directory.
- **Labels:** outer-test labels are used only for scoring (shuffle test).
- **Results directory:** synthetic output is refused under `03_results/`; every table carries `artifact_class`.
- **Partial runs:** `run_manifest.status = RUNNING` and no aggregate files. Resume happens only with an identical run_key.
