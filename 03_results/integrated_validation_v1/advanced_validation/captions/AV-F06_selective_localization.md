# AV-F06 — Localization ranking and eligibility

**Scientific question.** Does evidence qualification reduce wrong outlet assignments at matched coverage?

**Caption.** Location decisions for the four withdrawal queries (SID 213, its alternate-profile replicate, SID 312, SID 215). The nearest-template rule always names an outlet and is wrong for SID 312 and SID 215, whose own outlet has no independent template. Matched to the formal policy's coverage (0.5), a margin-ranked nearest-template rule and formal D(Y) both name only SID 213, correctly. Only one outlet has independent support, so no localization rate generalises.

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds.

**Source data.**
- `advanced_validation/tables/A07.csv`
- `advanced_validation/analysis/localization_cases.csv`

**Code.** `scripts/fig_av.py::plot_av_localization` · Files: `figures/AV-F06_selective_localization.png`, `figures/AV-F06_selective_localization.svg`
