# Q1_H13 — Positive-flow distinguishability

**Scientific question.** Do the measured channels separate the operating states once zero flow is removed?

**Caption.** Empirical rank probability between compressor-powered (12 segments) and electrolyzer-only test rows. Flow separates the states with all rows (0.945) only because most electrolyzer-only rows have zero flow; restricted to positive flow it falls to 0.554; with positive flow all three channels lie between 0.46 and 0.56. This is evidence sufficiency, not state classification accuracy.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/distinguishability.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_positive_flow` · Files: `figures/Q1_H13_hy2res_positive_flow_distinguishability.png`, `figures/Q1_H13_hy2res_positive_flow_distinguishability.svg`
