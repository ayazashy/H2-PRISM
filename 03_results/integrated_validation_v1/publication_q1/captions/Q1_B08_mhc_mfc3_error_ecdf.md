# Q1_B08 — MFC-3 error distribution

**Scientific question.** How do central and tail MFC-3 errors differ between the references?

**Caption.** Empirical cumulative distribution of absolute errors for MFC-3 outlet hydrogen flow, pooled over the three held-out runs (15,885 rows; serially dependent). Persistence is exactly right on 90.7% of rows; Ridge never is (continuous output). Median error: persistence 0, Ridge 0.0121; p99: 0.99 vs 0.973 ln/min.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/replay/replayed_predictions.csv.gz`
- `analysis/error_quantiles.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_mfc3_ecdf` · Files: `figures/Q1_B08_mhc_mfc3_error_ecdf.png`, `figures/Q1_B08_mhc_mfc3_error_ecdf.svg`
