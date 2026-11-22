# Validation Test Report: Phase 3 (non-training)

Environment: Windows, Python 3.12.1, `.venv` (system site-packages plus pytest 9.2.0, PyYAML 6.0.3). Raw data are present in `data/raw/`.

| # | Command | Result |
| --- | --- | --- |
| 1 | `python tools/dataset/build_pre_experiment_package.py --raw-parent data/raw --out 06_audit_preparation/pre_experiment_review` (first run) | Built. **Two defects in my builder found and fixed:** (a) the solver-export check divided by channel range, so near-constant channels gave false "UNEXPLAINED" results; now it uses the median over channels with range > 1e-3; (b) the filename location parser counted the "1" in "C1"; now it parses only `G<d>` tokens |
| 2 | Same, rebuilt | 57 runs, 51 eligible, 0 cross-topology shared rows, 0 fold-validation issues |
| 3 | Same with `--order reversed` (Windows separators) into scratch; compare `OUTPUT_HASHES.json` | 13/13 identical |
| 4 | `pytest tests/test_dataset_manifest.py tests/test_candidate_package.py tests/test_real_data_interfaces.py tests/test_io.py` | 35 passed |
| 5 | `pytest` (full suite) | **157 passed, 2 skipped**, 100 DeprecationWarnings from scikit-learn/SciPy (harmless) |
| 6 | `python -m compileall -q src tools tests` | OK |
| 7 | `python tools/research_audit/validate_artifacts.py --spec configs/candidate_artifact_validation.yaml --out-dir 06_audit_preparation/pre_experiment_review/artifact_validation` | 33 PASS, exit 0 |

**Skipped (2):** `test_load_scenario_sample_fallback_is_checksum_verified` and `test_load_fold_does_not_silently_return_empty`. Both exercise behaviour that applies only when the raw dataset is absent, and it is present now.

**Side effect handled:** `test_visualization.py` regenerates `03_results/figures/fig1` and `fig2`. Both were restored with `git checkout -- <file>` after each full run.

## Coverage of the required checks

- **Dataset:** archive provenance (Phase 2), checksum reconciliation (Phase 2 plus hash test), inventory and duplicate reconciliation (`test_realization_typing_and_misfiled_copy`, `test_regression_misfiled_leakG4_resolved`), scenario and family consistency (`test_families_never_span_topologies`), labels (`test_label_findings_recorded`), timing (`test_real_data_interfaces` delay case).
- **Evaluation:** family isolation under 3 views, byte-identity isolation, inner feasibility, class presence, determinism (hash test plus reverse-order build), and a regression check that the original leaky folds are still detected (`test_regression_original_folds_defect_still_detected_if_present`).
- **Software:** unit, integration, compile, schema (A12), and cross-platform checks.
- **Not executed (not authorised):** any model fit, calibration, D(x) or policy evaluation on real data.
