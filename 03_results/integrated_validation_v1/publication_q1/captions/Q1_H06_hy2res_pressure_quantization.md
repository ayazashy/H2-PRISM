# Q1_H06 — Pressure quantization

**Scientific question.** On what grid are the pressure targets recorded?

**Caption.** Distribution of recorded one-step changes on the shared 43,168-row held-out mask. Both pressures lie 100 % on a 0.1 bar grid over the full source (64 and 263 distinct values; TAB_H01). Buffer pressure is unchanged on 96.0 % of rows and tank pressure on 74.4 %; otherwise the change is exactly one increment (one tank row changes by two). 0.1 bar is the recording increment, not documented instrument resolution or accuracy.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/step_contribution.csv`
- `recording_grid.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_quantization` · Files: `figures/Q1_H06_hy2res_pressure_quantization.png`, `figures/Q1_H06_hy2res_pressure_quantization.svg`
