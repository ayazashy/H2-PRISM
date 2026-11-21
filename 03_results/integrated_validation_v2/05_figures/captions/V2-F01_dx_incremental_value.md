# V2-F01 — D(x) incremental-value analysis

**Scientific question.** Does D(x) improve out-of-template prediction of classifier correctness beyond confidence features?

**Caption.** (a) Each point is one held-out scenario template (16 eligible). Adding D to the correctness model increased out-of-template log-loss for most templates. (b) In a synthetic design with a known posterior, D adds information only when the classifier is blind to an informative feature; calibration or overconfidence alone leaves Δ near zero.

**Interpretation limit.** R2 labels are disputed in 36/57 runs; templates are the independent units; synthetic panel is a method check only.

**Source data.**
- `03_results/integrated_validation_v2/04_results/analysis/x2_incremental_utility_per_template.csv`
- `03_results/integrated_validation_v2/04_results/analysis/x5_synthetic_dx_control.csv`

**Code.** `scripts/fig_v2.py::f01` · Files: `figures/V2-F01_dx_incremental_value.png`, `figures/V2-F01_dx_incremental_value.svg`
