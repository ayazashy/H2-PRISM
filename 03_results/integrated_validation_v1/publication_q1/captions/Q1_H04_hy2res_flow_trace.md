# Q1_H04 — Held-out flow trace

**Scientific question.** How do the references follow held-out hydrogen flow?

**Caption.** Electrolyzer hydrogen flow in the same held-out segment 2382 (124 steps). h2_flow is a normalised volumetric production over the preceding sample interval and is not quantised at 0.1 (TAB_H01).

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `03_results/hy2res_external_validation/test_predictions.csv.gz (segment 2382)`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_flow_trace` · Files: `figures/Q1_H04_hy2res_flow_trace.png`, `figures/Q1_H04_hy2res_flow_trace.svg`
