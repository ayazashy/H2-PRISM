# H1-F02b — Paired selective-risk differences with intervals

**Scientific question.** Is the observed risk reduction distinguishable from zero at the level of independent units?

**Caption.** Paired differences with 95 % percentile bootstrap intervals (2,000 replicates, seed 20261104). Left: the registered contrast. Δ ranges from -0.134 to 0.000, and every family- and ancestor-level interval includes 0 (upper bounds ≥ 0). Discordant errors come from at most 3 scenario ancestors, and neither policy makes an error in runs with undisputed attribution. Right: the full evidence policy against conventional confidence abstention without the support guard; Δ from -0.467 to -0.277, with ancestor-level intervals below 0 at 3/5 points. The family intervals reproduce the registered diagnostics exactly; the ancestor intervals treat the 17 scenario templates shared by all topologies as units.

**Interpretation limit.** Simulated H2-SimNet topologies; all outer-test windows were inspected in R2; 91.7 % of classifier errors lie in runs whose source-model attribution is disputed (owner decision D1 pending). Not a confirmation of H1.

**Source data.**
- `h1_validation/analysis/h1_05_paired_comparisons.csv`
- `03_results/diagnostics/PRIMARY_a10530f1fcf2/exploratory_shared_coverage.csv`

**Code.** `scripts/fig_h1.py::plot_h1_paired_difference` · Files: `figures/H1-F02b_paired_risk_difference.png`, `figures/H1-F02b_paired_risk_difference.svg`
