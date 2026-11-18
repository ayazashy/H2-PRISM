# Faisal Pipeline Reproducibility Record

Run `python scripts/run_experiments.py` from the repository root after
installing `requirements.txt`. The runner reads the frozen
`configs/frozen_evaluation_config.yaml` and the existing provisional manifest,
fold file, and full Parquet benchmark. It writes one CSV per intermediate or
reported result and fails if required data, classes, fold checks, or source
hashes are unavailable.

The run records SHA-256 hashes for the config, manifest, folds, source modules,
and each selected input Parquet in `03_results/RESULTS_PROVENANCE.csv`, along
with the Git commit and Python version. Generated figures use distinct
`*_stage2.png` names; the existing demonstration dashboard/figures are not
overwritten by the experiment runner. Installed versions of the numerical,
data, plotting, machine-learning, and test dependencies are listed as
`runtime_dependency` rows in the provenance table.

The test command and execution outcome are recorded separately in
`04_validation/TEST_RESULTS.md` after validation. A deterministic seed does
not make the current windows statistically independent; inference resamples
family-level risk summaries.

`notebooks/FAISAL_PIPELINE_WALKTHROUGH.ipynb` provides a step-by-step view of
the F1-F13 workstream and demonstrates the same preprocessing, fold loading,
modeling, calibration, support, policy, and result-inspection functions. It is
an educational companion; the Python modules and CLI remain the canonical
implementation.
