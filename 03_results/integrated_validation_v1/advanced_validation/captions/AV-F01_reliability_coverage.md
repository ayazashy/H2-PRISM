# AV-F01 — Matched reliability–coverage frontier

**Scientific question.** How does wrong-specific risk change with coverage for each comparable policy?

**Caption.** Wrong-specific risk of each registered selection score at the five fixed coverage points inside the shared attainable region, and of the frozen classifier without abstention (all 27,993 windows: risk 0.286). Grey: coverage not attainable in every outer fold under the registered flags. No curve is extrapolated. Values and denominators in A01/A02a.

**Interpretation limit.** Simulated H2-SimNet topologies; inspected outer-test windows; 17 independent scenario templates; 91.7 % of classifier errors in runs with disputed attribution (D1 pending).

**Source data.**
- `advanced_validation/analysis/av_r2_wrong_specific_accounting.csv`

**Code.** `scripts/fig_av.py::plot_av_reliability_coverage` · Files: `figures/AV-F01_reliability_coverage.png`, `figures/AV-F01_reliability_coverage.svg`
