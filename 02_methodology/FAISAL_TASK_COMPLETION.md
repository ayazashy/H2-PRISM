# Faisal Workstream Completion Map

This index covers only Faisal-owned implementation and deliverables. The
teammate plans, audit scripts, dataset artifacts, and teammate-authored
documents are read-only inputs and were not modified.

| Task | Faisal-owned evidence |
|---|---|
| F1 Repository audit | `FAISAL_REPOSITORY_IMPLEMENTATION_AUDIT.md`; existing governance audit/classification documents were consulted read-only. |
| F2 Problem formulation | `DIAGNOSTIC_PROBLEM_FORMULATION.md` |
| F3 Preprocessing/windows/features | `PREPROCESSING_WINDOW_FEATURE_SPEC.md`, `src/h2prism/windows.py`, `tests/test_faisal_pipeline.py` |
| F4 Grouped evaluation | `GROUPED_EVALUATION_PROTOCOL.md`, `src/h2prism/evaluation.py`, frozen config, fold validation output |
| F5 Baseline | `BASELINE_MODEL_SPEC.md`, `03_results/BASELINE_RESULTS.csv` |
| F6 Calibration | `PROBABILITY_CALIBRATION_SPEC.md`, `03_results/CALIBRATION_RESULTS.csv` |
| F7 Empirical support \(D(x)\) | `D_STATISTIC_DESIGN_DECISION.md`, implementation/tests, outer predictions |
| F8 Comparators | `UNCERTAINTY_AND_DISTINGUISHABILITY_COMPARATORS.md` |
| F9 Selective policy | `SELECTIVE_DIAGNOSTIC_POLICY.md`, policy outcomes and prediction table |
| F10 Primary comparison | `03_results/MAIN_EXPERIMENT_REPORT.md`, matched-coverage and outer-prediction tables |
| F11 Statistical validation | `03_results/STATISTICAL_VALIDATION.csv`, `03_results/PER_FAMILY_RESULTS.csv` |
| F12 Integration freeze | `TECHNICAL_ARCHITECTURE_FREEZE.md`, `configs/frozen_evaluation_config.yaml` |
| F13 Testing/reproducibility | `04_validation/LEAKAGE_VALIDATION.md`, `REPRODUCIBILITY_REPORT.md`, `TEST_RESULTS.md`, and the interactive `notebooks/FAISAL_PIPELINE_WALKTHROUGH.ipynb` |

### Interpretation guardrail

The selected primary estimand is cross-topology transfer. Existing folds have
base-family overlap between train and test, so no result from this workstream
should be called unseen-family generalization. The experiment report and fold
diagnostics preserve this limitation.
