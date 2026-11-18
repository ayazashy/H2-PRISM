# Q1_H10 — Unresolved-reason decomposition

**Scientific question.** Why does the frozen state rule abstain on most test rows?

**Caption.** Exclusive primary reason for each of the 32,308 UNRESOLVED test rows (denominator 44,397 test rows). OUT_OF_SUPPORT (tank pressure above the development maximum) accounts for 31,589 (97.8%); INVALID_INPUT (nonfinite origin measurement) and EMPTY_CELL (no state with two development segments) account for the rest. These are kept distinct from ambiguity. Reasons reproduce the frozen min–max guard exactly.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/unresolved_taxonomy.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_unresolved_reasons` · Files: `figures/Q1_H10_hy2res_unresolved_reasons.png`, `figures/Q1_H10_hy2res_unresolved_reasons.svg`
