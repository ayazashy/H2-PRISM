# Q1_H02 — Partition and causal segmentation

**Scientific question.** How is the record partitioned and segmented to keep prediction causal?

**Caption.** Frozen chronological partition: development (2024-03-27 11:34:27 – 2024-04-09 02:34:59), validation, a one-hour embargo on each side, and the held-out test period from 2024-04-12 12:13:56. Causal segments (2,793 in total) break at OPEN/CLOSE markers and at any step other than 5 s; models use only same-segment lag-1 inputs, with no interpolation. No development segment is shared with the test period.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/chronology.csv`
- `03_results/hy2res_external_validation/segment_registry.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_partition_timeline` · Files: `figures/Q1_H02_hy2res_partition_timeline.png`, `figures/Q1_H02_hy2res_partition_timeline.svg`
