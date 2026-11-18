# Q1_B05 — P-2 per-run performance

**Scientific question.** Is the P-2 model ranking stable across held-out runs?

**Caption.** Run-level MAE and RMSE of the two frozen references for P-2 Stage II hydrogen pressure (barg; units never combined). Ridge − persistence ΔMAE / ΔRMSE: run 24: +0.0199 / -0.00077; run 28: +0.0130 / -0.00071; run 29: +0.0111 / -0.00453. The largest relative RMSE change is 1.02% of the persistence RMSE.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/run_metrics.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_p2_per_run` · Files: `figures/Q1_B05_mhc_p2_per_run.png`, `figures/Q1_B05_mhc_p2_per_run.svg`
