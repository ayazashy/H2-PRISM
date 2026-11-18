# Q1_H09 — Tank-pressure drift

**Scientific question.** Does the test period stay inside the development operating range?

**Caption.** Per-partition distributions of the raw source values (thin grey: min–max; coloured: 5th–95th percentile; diamond: median). Tank-pressure medians rise from 94.2 bar (development) to 102.4 (validation) and 107.8 (test); 71.8% of test rows exceed the development maximum 106.6 bar. Buffer pressure stays inside its development range. Validation contained no out-of-range rows, so development-only checks could not reveal the drift.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/chronology.csv`
- `development_bounds.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_drift` · Files: `figures/Q1_H09_hy2res_tank_pressure_drift.png`, `figures/Q1_H09_hy2res_tank_pressure_drift.svg`
