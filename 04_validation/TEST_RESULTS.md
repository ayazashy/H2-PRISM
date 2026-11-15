# Faisal Pipeline Test Results

## Focused automated tests

Command:

```text
python -m pytest tests/test_faisal_pipeline.py tests/test_data_loader.py tests/test_dataset_audit.py -q
```

Result: **20 passed**. This covers the new config-version guard,
preprocessing, event-boundary,
incomplete-tail, family-excluded support, row-order permutation, calibration,
policy, the query-family scaler-exclusion regression, data-loader, and
dataset-audit tests.

Import check: `h2prism.experiments` and `h2prism.evaluation` imported
successfully with the repository's `src` directory on `sys.path`, as configured
by the CLI and test setup.

Notebook validation: the `.ipynb` JSON and all code-cell syntax were checked;
all 19 code cells executed successfully for the one-fold walkthrough and
three-fold evaluation (8,484 train windows, 4,079 test windows per fold;
isotonic calibration selected for the detailed first fold). Fold
diagnostics are derived from the supplied fold table, so the walkthrough does
not require a previously generated report with a newer schema. The default
config path resolves directly to the repository's
`configs/frozen_evaluation_config.yaml`; the rerun loaded version `1.0.2`.
Cell outputs are saved in the notebook for inspection, including the first-fold
classification report, matched-coverage comparison, and three-fold result
tables. The all-fold cell independently refits and evaluates each held-out
topology, reporting raw and calibrated predictions and confusion matrices. The
import cell clears cached `h2prism` modules before loading the workspace source
and prints the resolved source and config paths.

The legacy visualization tests were not run because their import path reaches a
pre-existing missing `Any` import in the teammate-owned
`src/h2prism/visualization/dashboard.py`; that file was left unchanged to
preserve the ownership boundary.

## Full experiment (config 1.0.2)

The frozen three-fold experiment completed successfully after the D(x)
query-family scaling correction. Raw fold accuracies were 91.84%, 19.61%, and
100.00% (70.48% mean across folds); the single 92% fold is not representative
of overall cross-topology transfer. Matched-coverage D-only risk is 0.5775.
Generated artifact details, limitations, and provenance are recorded in
`03_results/MAIN_EXPERIMENT_REPORT.md` and
`03_results/RESULTS_PROVENANCE.csv`. Results concern simulated H2-SimNet data
and do not support unseen-family or real-field performance claims.
