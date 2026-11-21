# Q1_B02 — Run eligibility and partition

**Scientific question.** Which experimental runs are evaluated, and how are they partitioned?

**Caption.** Eligibility and partition of all 29 MHC v1.2 workbooks (frozen Study B values; valid pairs recounted by the bit-identical replay). Outside scope: single stage compression (14), capacity measurement (5), thermal analysis without hydrogen (2). Held-out test runs 24, 28 and 29 contribute 15,885 pairs per channel.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/tables/TAB_B01.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_run_partition` · Files: `figures/Q1_B02_mhc_run_partition.png`, `figures/Q1_B02_mhc_run_partition.svg`
