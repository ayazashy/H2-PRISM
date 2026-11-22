# Q1_C09 — Categorical location ranking

**Scientific question.** Can the configured outlet be ranked first?

**Caption.** Categorical location ranking for the withdrawal queries (all sensors, 30 s prefix, ±1 s). Q213 and Q213-alt are ranked correctly (SID 213 first) only because a second SID 213 capture exists; the two captures differ only by a +0.005 MPa reservoir overlay. Q312 and Q215 have no independent same-outlet template and cannot be ranked. This is a categorical rank, not a localization distance or accuracy.

**Interpretation limit.** Two supported queries for one outlet; no localization accuracy is estimable.

**Source data.**
- `03_results/validation/center_evidence_enhancement/tables/TAB_C03.csv`

**Code.** `scripts/fig_center.py::plot_center_location_ranking` · Files: `figures/Q1_C09_center_location_ranking.png`, `figures/Q1_C09_center_location_ranking.svg`
