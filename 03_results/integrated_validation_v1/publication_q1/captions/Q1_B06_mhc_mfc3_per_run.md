# Q1_B06 — MFC-3 per-run performance

**Scientific question.** Is the MFC-3 model ranking stable across held-out runs?

**Caption.** Run-level MAE and RMSE of the two frozen references for MFC-3 outlet hydrogen flow (ln/min; units never combined). Ridge − persistence ΔMAE / ΔRMSE: run 24: +0.0141 / +0.00012; run 28: +0.0086 / -0.00044; run 29: +0.0097 / -0.00038. The largest relative RMSE change is 0.15% of the persistence RMSE.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/run_metrics.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_mfc3_per_run` · Files: `figures/Q1_B06_mhc_mfc3_per_run.png`, `figures/Q1_B06_mhc_mfc3_per_run.svg`
