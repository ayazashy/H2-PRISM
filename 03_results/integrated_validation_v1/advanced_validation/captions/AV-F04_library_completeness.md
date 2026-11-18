# AV-F04 — Hypothesis-library completeness and false specificity

**Scientific question.** How does library completeness change formal decisions?

**Caption.** Formal D(Y) outcomes for four hypothesis libraries. Full declared universe: all UNRESOLVED. Restricted: 8 correct and 2 wrong SPECIFIC. Removing the normal-operation rival removes both wrong decisions (they selected that rival). Removing the true hypothesis of the two supported queries gives 2 wrong SPECIFIC and 4 ambiguity sets without the truth; the rest abstain as MODEL_MISMATCH. False specificity is unavoidable when the truth is absent and a rival remains consistent.

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds.

**Source data.**
- `advanced_validation/analysis/dy_experiment_runs.csv (E4)`

**Code.** `scripts/fig_av.py::plot_av_library_completeness` · Files: `figures/AV-F04_library_completeness.png`, `figures/AV-F04_library_completeness.svg`
