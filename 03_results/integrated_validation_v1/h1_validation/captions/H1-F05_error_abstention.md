# H1-F05 — Decision errors and abstention

**Scientific question.** Does evidence-based abstention preferentially withhold classifier errors?

**Caption.** Fate of the classifier's top-1 errors at rank-matched coverage 0.25 (equal SPECIFIC counts per fold). The evidence-support flags block 6,271 of 8,012 errors (78.3%); the error rate is 0.523 among blocked and 0.109 among eligible windows (base rate 0.286). Conventional confidence abstention issues far more of the same errors as SPECIFIC. Segments below 5 % are unlabelled; exact counts are in h1_05_error_capture.csv and h1_04_selection_by_method.csv. Upstream has no classifier errors. 7,347 of the errors lie in runs with disputed topology attribution, so this shows the guard reacting to an attribution defect, not to independently labelled diagnostic difficulty.

**Interpretation limit.** Simulated H2-SimNet topologies; all outer-test windows were inspected in R2; 91.7 % of classifier errors lie in runs whose source-model attribution is disputed (owner decision D1 pending). Not a confirmation of H1.

**Source data.**
- `h1_validation/analysis/h1_05_error_capture.csv`
- `h1_04_selection_by_method.csv`

**Code.** `scripts/fig_h1.py::plot_h1_error_abstention` · Files: `figures/H1-F05_error_abstention.png`, `figures/H1-F05_error_abstention.svg`
