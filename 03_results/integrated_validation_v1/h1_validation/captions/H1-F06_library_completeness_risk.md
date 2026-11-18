# H1-F06 — Hypothesis-library completeness risk

**Scientific question.** Does an incomplete hypothesis library cause false specific decisions?

**Caption.** Formal D(Y) decisions on the Center controlled captures under conditional hypothetical bounds. With the full declared universe every decision is UNRESOLVED, because three declared hypotheses have no adapter. Restricting the universe to modelled hypotheses yields SPECIFIC decisions: over both clock bounds and all sensor groups 48 are correct and 11 wrong, and every wrong decision has a true hypothesis that is absent from the library (asserted). Rows are repeated views of the same six captures, not independent trials. Conditional hypothetical bounds — not calibrated uncertainty.

**Interpretation limit.** One controlled simulation family with an air-like gas model; hypothetical bounds.

**Source data.**
- `h1_validation/analysis/h1_07_dy_library_completeness.csv`
- `03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json`

**Code.** `scripts/fig_h1.py::plot_h1_library_completeness` · Files: `figures/H1-F06_library_completeness_risk.png`, `figures/H1-F06_library_completeness_risk.svg`
