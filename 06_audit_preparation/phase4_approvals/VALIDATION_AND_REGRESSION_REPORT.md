# Validation and Regression Report: Phase 4 (preparation checks only; no training)

| # | Command | Result |
| --- | --- | --- |
| 1 | `python -m compileall -q src tools tests` | OK |
| 2 | `MPLBACKEND=Agg python -m pytest -q -p no:cacheprovider -rs` | **158 passed, 2 skipped** (160 collected). 100 DeprecationWarnings from scikit-learn/SciPy (L-BFGS-B `disp`/`iprint`), harmless |
| 3 | `python tools/dataset/build_pre_experiment_package.py --raw-parent data/raw --out <scratch> --order reversed`, then compare `OUTPUT_HASHES.json` | **13/13 identical** (deterministic; separator- and order-independent) |
| 4 | `python tools/research_audit/validate_artifacts.py --spec configs/candidate_artifact_validation.yaml --out-dir 06_audit_preparation/phase4_approvals/evidence/artifact_validation` | **33/33 PASS** |
| 5 | `python tools/dataset/phase4_decision_evidence.py` (windowing and counting only) | evidence CSVs written; no model fitted |
| 6 | `python 06_audit_preparation/phase4_approvals/build_decision_matrix.py` | 44 decisions, all `PENDING_HUMAN_APPROVAL`, unique IDs |

Afterwards `03_results/figures/fig1*.png` and `fig2*.png`, which `test_visualization` regenerates, were restored with `git checkout -- <file>`.

## Coverage of the requested checks

| Check | Evidence |
| --- | --- |
| Manifest, family and label consistency | `test_candidate_package.py` (families never span topologies; label findings; status everywhere; hashes match) |
| Outer-fold leakage | `test_outer_folds_family_isolated[3 views]`, `test_no_byte_identical_file_across_split` |
| Inner-fold feasibility and independence | `test_inner_loto_splits_feasible`; **new** `test_inner_splits_independent_and_inside_outer_train` (inner train ∩ validation = ∅ for runs and families/topologies; inner ⊆ outer train) |
| Schema and provenance | A12 33/33; `OUTPUT_HASHES.json` test |
| Deterministic regeneration and cross-platform paths | row 3; `test_dataset_manifest.py` |
| No dependence on outer-test labels | `test_baseline.py::test_outer_test_rows_do_not_influence_selection`; policy refuses non-development thresholds; ablation decisions unchanged when labels change |
| Regression of previously found defects | misfiled leakG4 resolved; original `folds.csv` still detected as leaky while unchanged; loader no longer silent; fabricated figures quarantined |

## Test-count reconciliation (no hidden failures)

| Reported | Collected | Condition | Explanation |
| --- | ---: | --- | --- |
| 129 passed / 1 skipped (Phase 1) | 130 | raw data absent | `test_load_fold` skipped (needs raw data) |
| 128 passed / 2 skipped (Phase 2) | 130 | raw data present | `test_load_fold` runs and passes; the 2 tests that apply only without raw data skip |
| 157 passed / 2 skipped (Phase 3) | 159 | raw data present | +29 tests: `test_dataset_manifest` 11, `test_candidate_package` 14 (the Phase 3 checkpoint said 13: a miscount, since one test is parametrised ×3), `test_real_data_interfaces` 4 |
| **158 passed / 2 skipped (Phase 4)** | 160 | raw data present | +1 inner-split regression test |

## Unresolved technical defects

None of the tested components fails. Not yet implemented (blocking at a later stage):
- the correctness meta-model (F-D10);
- the manifest-driven window and feature table builder;
- the F11 family bootstrap;
- scenario-balanced D support (optional).

Not verified: execution on macOS or Linux.
