# Test and Validation Report

Environment: Windows, Python 3.12.1, `.venv` (system site-packages, plus pytest 9.2.0 and PyYAML 6.0.3), `MPLBACKEND=Agg`.
**Passing tests show that the software behaves as specified on synthetic fixtures. They are not scientific validation.**

## 1. Commands executed and outcomes

| # | Command | Outcome |
| --- | --- | --- |
| 1 | `python -m pytest -q -p no:cacheprovider` (baseline, unchanged code) | **Collection error**: `NameError: Any` in `dashboard.py` |
| 2 | same with `--ignore=tests/test_visualization.py` (baseline) | **10 passed, 2 failed** (`test_load_scenario_by_id`: raw data absent; `test_load_fold`: empty fold, caused by the silent skip) |
| 3 | new modules only (first run) | 103 passed, 2 failed: a bug in my test helper (one family label passed for several queries). Helper fixed, not the module |
| 4 | `pytest tests/test_distinguishability.py` | 17 passed |
| 5 | full suite after the fixes (run twice) | **129 passed, 1 skipped** (`test_load_fold` needs the raw dataset). 100 DeprecationWarnings from scikit-learn/SciPy L-BFGS-B (`disp`/`iprint`); harmless |
| 6 | `python -m compileall -q src tools scripts audit tests` | OK |
| 7 | F4 validator on `01_dataset_audit/folds.csv` with `DUPLICATE_EXPORT_AUDIT.csv` | **FAIL**: 3× FAMILY_IN_TRAIN_AND_TEST, 1× CONTENT_DUPLICATE_ACROSS_SPLIT (fold 3), 3× MULTIPLE_FILES_PER_SCENARIO → `FOLD_VALIDATION_ISSUES.csv`, `FOLD_VALIDATION_SUMMARY.csv` |
| 8 | `python tools/research_audit/validate_artifacts.py --spec configs/artifact_validation.yaml --out-dir 06_audit_preparation/artifact_validation` | exit 1: 28 PASS, 2 MISSING_ARTIFACT (`03_results/BASELINE_PREDICTIONS.parquet`, `05_documentation/PROVENANCE_REGISTER.csv`), 1 UNSUPPORTED_STATUS (`MASTER_TASK_REGISTER.csv`: COMPLETED / IN_PROGRESS / READY_TO_START). The 4/4 sample-file checksums PASS |
| 9 | `python tools/research_audit/build_provenance_index.py --dirs 01_dataset_audit 03_results data/sample --out 06_audit_preparation/PROVENANCE_INDEX.csv` | 44 files indexed. No sidecars exist, so every run field is `UNKNOWN` (by design: nothing is backfilled) |
| 10 | `python tools/reporting/build_research_figures.py --config configs/reporting_figures.yaml --out-dir 06_audit_preparation/reporting_dry_run` | exit 2: **fails clearly**, because the F10/F6 inputs do not exist. Manifest records NOT_BUILT_MISSING_EVIDENCE |

Side effect noted: `tests/test_visualization.py::test_visualize_cli_runner` rewrites `03_results/figures/fig1_family_distribution.png`. After each run the original was restored with `git checkout -- <file>` (ISS-18).

## 2. Test inventory (130 collected)

| Module | n | What it verifies |
| --- | ---: | --- |
| test_io | 6 | No silent dt assumption; time column used without repair; duplicate and non-monotonic times; irregular sampling; NaN/inf intervals; missing or non-numeric channels |
| test_windows | 11 | Toy window count and boundaries; file-level labels never claim boundaries; row-level boundary crossing; pre-event policy; invalid windows excluded without imputation; time-based windows under irregular sampling; non-monotonic time rejected; family propagation and no cross-scenario windows; double-export detection; compound/untyped mapping; determinism; config validation |
| test_features | 5 | Hand-calculated statistics; offset invariance; metadata guard; register units; deterministic hash |
| test_splits | 7 | Clean folds pass; family overlap critical; content duplicate across split; missing classes and multi-file scenarios; transitive union-find; deterministic group-disjoint inner splits with class warnings; hard assertion |
| test_distinguishability | 17 | Hand-calculated q and D (k = 3, 4); inverse-distance weights; ties; permutation invariance; reference-label sensitivity; own-family exclusion; fewer than k references; missing class gives 0 not NaN; zero distance; scenario dominance; prior correction; invalid features; non-finite reference; training-only standardisation; separated vs overlapping classes; out-of-support threshold; determinism |
| test_comparators | 6 | Closed-form C, M, H; −H direction; invalid inputs; D validation; logit; determinism |
| test_metrics | 8 | Coverage and risk definition; undefined risk; ties in the risk-coverage curve; rank-match overshoot; Brier and log loss; ECE; absent classes; ambiguity summary |
| test_policy | 11 | SPECIFIC; ambiguity set; all-class prevention; excessive breadth; out-of-support; low support; singleton modes; D gate; invalid rows isolated; development-only thresholds; determinism and no label input |
| test_baseline | 8 | RF grid equals the plan; schema and determinism; family leakage refused; metadata features refused; **outer-test perturbation leaves selection and inner OOF unchanged**; missing class recorded; calibration keeps "none" unless better; calibrator simplex |
| test_secondary_baseline | 5 | Config bounded and not frozen; scaler fit on training rows; schema and determinism; feature-order invariance; leakage refused |
| test_feature_sensitivity | 3 | Rule-based arm resolution; prespecified config; same population per arm and NOT_SUPPORTED reporting |
| test_supporting_ablations | 5 | Confidence-only arm; margin threshold required; decisions unchanged when labels change; outer-test thresholds refused; family summary |
| test_research_audit | 6 | PASS and inputs untouched; missing columns, duplicate keys, hash mismatch, status vocabulary, missing artifact; checksum reconciliation; refuses an output dir containing inputs; provenance not backfilled; determinism |
| test_reporting_outputs | 6 | Fixture data never routed to final; preliminary routing; values preserved; missing evidence fails; risk without coverage rejected; byte-identical figures and manifest hashes |
| test_pipeline_integration | 1 | Synthetic multi-family end to end: validation → windows → features → grouped RF → development calibration → D on outer-train reference → comparators → policy → coverage/risk; table hash reproducible; families disjoint |
| test_data_loader / test_dataset_audit / test_visualization | 25 | Pre-existing tests, plus 2 new loader tests |

## 3. Read-only evidence recomputation (for the Yazan verification)

Commands (pandas, from the repository root) computed:
- folds × family overlap;
- `DUPLICATE_EXPORT_AUDIT.csv` joined with `DATASET_SCENARIO_MAP.csv` per Scenario_ID and per tree (252 cross-tree pairs, all DIFFERENT_CONTENT);
- `FILE_LEVEL_AUDIT.csv` grouped by tree (clean tree = 60 CSV + 61 Parquet, 2,420,000 rows), `time_col` counts (230 `Index_implied_1s`), and `sampling_dt_median ≠ 1` (6 files).

The fold computation can be re-run with `h2prism.splits.validate_outer_folds` (see `YAZAN_DATASET_VERIFICATION.md`).

## 4. Not executed (with reasons)

- `audit/run_all_audits.py`, `setup_data.py`, `scripts/download_data.py`: the raw dataset is absent, and downloading about 1 GB from Zenodo needs the user's explicit approval.
- Any model training on project data, calibration, D computation, policy evaluation or statistics. There is no frozen feature table and no valid folds, and primary runs need the F4 freeze.
- A clean-checkout reproduction (F13 step 126) and static analysis (no linter is configured in the project).
