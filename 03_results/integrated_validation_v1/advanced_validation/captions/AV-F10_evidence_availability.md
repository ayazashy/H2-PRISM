# AV-F10 — Evidence availability versus decision outcomes

**Scientific question.** Does less evidence lead to abstention or to false certainty?

**Caption.** All predeclared sensor configurations grouped by the number of available channels (an objective information axis; configurations with the same count differ in which channels remain, see AV-F08). Correct SPECIFIC decisions become rarer and ambiguity more frequent as channels are removed, but wrong SPECIFIC decisions do not fall monotonically: the 3-channel flow-only set has the highest wrong-specific share. Channel identity matters more than count.

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds.

**Source data.**
- `advanced_validation/analysis/dy_experiment_runs.csv (E1)`
- `dy_evidence_availability.csv`

**Code.** `scripts/fig_av.py::plot_av_evidence_availability` · Files: `figures/AV-F10_evidence_availability.png`, `figures/AV-F10_evidence_availability.svg`
