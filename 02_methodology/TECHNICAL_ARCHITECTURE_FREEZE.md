# Technical Architecture Freeze (Faisal F12)

## Versioned interfaces

- `configs/frozen_evaluation_config.yaml`: versioned model, windows, folds,
  calibration selection, support neighbor count, policy, and uncertainty
  settings; marked frozen before outer evaluation.
- `configs/interface_contracts.yaml`: existing shared interface contract,
  retained unchanged.
- `src/h2prism/windows.py`: event eligibility, window manifest, and
  sensor-only feature extraction.
- `src/h2prism/evaluation.py`: fold checks, baseline, calibration,
  family-excluded support, comparators, and policy.
- `src/h2prism/experiments.py`: outer-fold execution and machine-readable
  result/provenance artifacts.
- `scripts/run_experiments.py`: repository-root CLI entry point.

The accepted configuration is `1.0.2`. Version `1.0.1` recorded that incomplete
trailing samples are counted rather than padded and that exact D(x) distance
ties use unique `window_id`. Version `1.0.2` corrects family-excluded
standardization for D(x), as described below. These changes do not alter the
selected folds, feature summaries, estimator, calibration method, D(x)
definition, or policy thresholds. The primary outputs are CSV tables under
`03_results/`, the report
`03_results/MAIN_EXPERIMENT_REPORT.md`, Stage 2 figures with the
`_stage2.png` suffix, and validation reports under `04_validation/`. The
legacy demo artifacts are not overwritten.

## Change control and compatibility

The input manifest and fold files are read-only. Scenario identity is
deduplicated to one canonical Parquet per `Scenario_ID`. CSV tables include
fold IDs and preserve scenario/family IDs for audit. Each run records SHA-256
hashes of config, manifest, folds, source, and input Parquet files plus the Git
commit and Python version in `03_results/RESULTS_PROVENANCE.csv`.

The `1.0.2` version also corrects the D(x) reference construction: the scaler
is fitted after excluding the query family, so that family cannot influence
its own support geometry.

Changes to labels, window definitions, feature definitions, fold assignments,
model/calibration settings, reference construction, or policy thresholds
require a new config version and rerunning all dependent results. No teammate
plan, data audit script, or teammate-owned data artifact is modified by this
implementation.
