# Q1_B09 — Error-tail concentration

**Scientific question.** Do rare large errors dominate RMSE?

**Caption.** Concentration curves of squared error, pooled over the three held-out runs: the share of total SSE carried by the given fraction of largest-error rows (dimensionless; channels in separate panels). The two references' curves almost coincide. For MFC-3 the top 1 % of rows carry 91.1%–100.0% of persistence SSE per run (TAB_B05), so RMSE comparisons are decided by rare large steps.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/concentration_curves.csv`
- `tail_shares.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_error_concentration` · Files: `figures/Q1_B09_mhc_error_concentration.png`, `figures/Q1_B09_mhc_error_concentration.svg`
