# Q1_H05 — State-dependent reference error

**Scientific question.** Does the reference comparison change with the operating state?

**Caption.** Relative change (Ridge − persistence) / persistence of MAE and RMSE on the frozen held-out test mask, per target and power-defined operating state (states with scored rows). Negative favours Ridge. In the minority compressor-powered state the flow RMSE rises from 0.1347 to 0.6465 NL/h (+380 %). Unknown-power rows (412–413) are not scored.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `03_results/hy2res_external_validation/publication/TABLE_2_HELD_OUT.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_state_error` · Files: `figures/Q1_H05_hy2res_state_dependent_error.png`, `figures/Q1_H05_hy2res_state_dependent_error.svg`
