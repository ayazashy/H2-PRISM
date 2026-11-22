# AV-F09 — Timing-alignment robustness

**Scientific question.** How do formal decisions respond to clock uncertainty and to observation delay?

**Caption.** Left: widening the admissible clock-shift set from 0 to 10 s leaves every decision unchanged (no new exclusions, as required). Right: an observation delay of 2 s or more with τ = 1 s removes every correct SPECIFIC decision (UNRESOLVED: all supported hypotheses excluded); declaring τ equal to the delay restores them. The two wrong SPECIFIC decisions (SID 215 → normal operation) are delay-invariant because the normal-operation template is constant. Jitter was not tested (no jitter model).

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds.

**Source data.**
- `advanced_validation/analysis/dy_experiment_runs.csv (E2, E3)`

**Code.** `scripts/fig_av.py::plot_av_timing` · Files: `figures/AV-F09_timing_robustness.png`, `figures/AV-F09_timing_robustness.svg`
