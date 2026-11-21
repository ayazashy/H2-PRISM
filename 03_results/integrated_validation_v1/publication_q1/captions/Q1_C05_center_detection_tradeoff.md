# Q1_C05 — Detection completeness versus false alarms

**Scientific question.** What false-alarm burden accompanies event detection in the archive replay?

**Caption.** Clean cumulative replay of the frozen 120 s decision cadence (51 scenarios, 48 events, 65.63 inactive hours). Random forest misses 0 events at 0.244 false episodes per hour; the trivial rules (grey) miss all 48 new-alert detections. Lower-left is better on both axes.

**Interpretation limit.** Archive replay of simulated scenarios; not a field detection rate.

**Source data.**
- `03_results/validation/publication_final_v1/tables/TAB_04.csv`

**Code.** `scripts/fig_center.py::plot_center_detection_tradeoff` · Files: `figures/Q1_C05_center_detection_tradeoff.png`, `figures/Q1_C05_center_detection_tradeoff.svg`
