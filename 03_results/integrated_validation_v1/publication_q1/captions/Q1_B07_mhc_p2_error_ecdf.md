# Q1_B07 — P-2 error distribution

**Scientific question.** How do central and tail P-2 errors differ between the references?

**Caption.** Empirical cumulative distribution of absolute errors for P-2 Stage II hydrogen pressure, pooled over the three held-out runs (15,885 rows; serially dependent). Persistence is exactly right on 70.6% of rows; Ridge never is (continuous output). Median error: persistence 0, Ridge 0.0237; p99: 1.2 vs 1.18 barg.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/replay/replayed_predictions.csv.gz`
- `analysis/error_quantiles.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_p2_ecdf` · Files: `figures/Q1_B07_mhc_p2_error_ecdf.png`, `figures/Q1_B07_mhc_p2_error_ecdf.svg`
