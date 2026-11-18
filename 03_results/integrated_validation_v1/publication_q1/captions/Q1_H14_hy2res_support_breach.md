# Q1_H14 — Support violations by channel

**Scientific question.** Which channels leave the development support in the test period?

**Caption.** Development-support violations per channel among the 44,397 test rows (non-exclusive per channel). Tank pressure exceeds the development maximum on 31,589 rows (299 segments, up to 4.1 bar above); no channel falls below its development minimum; buffer pressure and flow never leave their support. The 413 nonfinite rows are the same rows in every channel (segment-start origins).

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/support_attribution.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_support_breach` · Files: `figures/Q1_H14_hy2res_support_breach.png`, `figures/Q1_H14_hy2res_support_breach.svg`
