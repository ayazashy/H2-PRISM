# H1-F04b — Score ranking quality on the outer test

**Scientific question.** Does D(x) carry ranking information that conventional scores lack?

**Caption.** Correctness AUROC of each registered selection score on the windows eligible for SPECIFIC. Downstream: confidence, margin and −entropy are perfectly anti-informative (AUROC 0: the 650 errors are the most confident windows), while both meta-model scores reach 1.0 with or without D(x). Center: adding D(x) moves the meta-model from 0.522 to 0.981, the same level as confidence (0.983). Upstream has no errors (not shown). Both topologies' errors are tied to the disputed attribution.

**Interpretation limit.** Simulated H2-SimNet topologies; all outer-test windows were inspected in R2; 91.7 % of classifier errors lie in runs whose source-model attribution is disputed (owner decision D1 pending). Not a confirmation of H1.

**Source data.**
- `h1_validation/analysis/h1_03_score_redundancy_test.csv`

**Code.** `scripts/fig_h1.py::plot_h1_score_ranking` · Files: `figures/H1-F04b_score_ranking_quality.png`, `figures/H1-F04b_score_ranking_quality.svg`
