# Q1_H03 — Held-out pressure traces

**Scientific question.** How do the references follow held-out pressure?

**Caption.** Held-out test segment 2382 (124 five-second steps, 12:36:44–12:46:59 on 12 April 2024; the interval chosen by chronology and segment length in the original publication script). Observed values change in single 0.1 bar steps; persistence repeats the previous value and the contextual Ridge reference responds smoothly. Buffer and tank pressure are drawn on separate axes.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `03_results/hy2res_external_validation/test_predictions.csv.gz (segment 2382)`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_pressure_traces` · Files: `figures/Q1_H03_hy2res_pressure_traces.png`, `figures/Q1_H03_hy2res_pressure_traces.svg`
