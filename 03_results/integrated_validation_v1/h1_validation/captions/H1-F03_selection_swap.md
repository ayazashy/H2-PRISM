# H1-F03 — Selection changes caused by D(x)

**Scientific question.** Which cases does the distinguishability component add or remove at matched coverage?

**Caption.** Windows selected by exactly one of the two registered policies at each grid point (identical SPECIFIC counts). Adding D(x) exchanges 1,272–2,066 windows. The windows only s_C−D accepts contain 0–563 errors; those only s_C accepts contain 0–29. All discordant errors come from 1–3 scenario ancestors, all in Center runs whose topology attribution is disputed; they are not independent replications.

**Interpretation limit.** Simulated H2-SimNet topologies; all outer-test windows were inspected in R2; 91.7 % of classifier errors lie in runs whose source-model attribution is disputed (owner decision D1 pending). Not a confirmation of H1.

**Source data.**
- `h1_validation/analysis/h1_05_paired_comparisons.csv`

**Code.** `scripts/fig_h1.py::plot_h1_selection_swap` · Files: `figures/H1-F03_selection_swap.png`, `figures/H1-F03_selection_swap.svg`
