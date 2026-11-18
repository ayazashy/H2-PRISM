# Q1_H07 — Errors in recording increments

**Scientific question.** How large are the pressure errors relative to the recording grid?

**Caption.** Held-out MAE and RMSE divided by the 0.1 bar recording increment (43,168 rows, 409 segments). ΔMAE (Ridge − persistence): buffer +0.0154, tank -0.0046 increments; ΔRMSE: -0.0277 and -0.0990. All differences are below 0.1 of one recorded step. Persistence is exactly right on 96.0% (buffer) and 74.4% (tank) of rows.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/quantization_comparison.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_error_increments` · Files: `figures/Q1_H07_hy2res_error_in_increments.png`, `figures/Q1_H07_hy2res_error_in_increments.svg`
