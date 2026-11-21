# AV-F05 — Formal D(Y) decision-state transitions

**Scientific question.** Does the formal engine respect evidence monotonicity when information is removed?

**Caption.** Hypothesis-status transitions between the all-channel run and each of the 78 reduced sensor configurations (9,984 hypothesis checks, 6 queries × 4 bound scenarios). Forbidden cells (hatched) are all zero. Across all invariant tests — sensor removal, clock-bound widening and bound widening on the frozen grid — 25,024 paired hypothesis checks show 0 violations (A04a).

**Interpretation limit.** Mathematical property of the engine on fixed models and frozen bounds; not a physical validation.

**Source data.**
- `advanced_validation/analysis/dy_experiment_runs.csv`
- `dy_invariant_checks.csv`

**Code.** `scripts/fig_av.py::plot_av_status_transitions` · Files: `figures/AV-F05_dy_status_transitions.png`, `figures/AV-F05_dy_status_transitions.svg`
