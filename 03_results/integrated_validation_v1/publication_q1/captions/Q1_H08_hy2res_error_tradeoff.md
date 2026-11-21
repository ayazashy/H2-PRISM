# Q1_H08 — Error trade-off by step class

**Scientific question.** Why does Ridge improve RMSE while worsening buffer MAE?

**Caption.** Squared-error difference by recorded step class on the held-out mask. Tank pressure: Ridge gains -54.2 bar² on single-step rows and loses +15.2 bar² on unchanged rows. Ridge predictions are not rounded to the grid. The RMSE improvement therefore reflects partial anticipation of single-increment transitions, not physically resolved accuracy.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/step_contribution.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_error_tradeoff` · Files: `figures/Q1_H08_hy2res_error_tradeoff.png`, `figures/Q1_H08_hy2res_error_tradeoff.svg`
