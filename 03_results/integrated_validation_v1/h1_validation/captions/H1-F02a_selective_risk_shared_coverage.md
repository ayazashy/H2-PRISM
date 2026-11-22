# H1-F02a — Selective risk at shared attainable coverage

**Scientific question.** Within the coverage attainable in every fold, how do the policies' selective risks compare?

**Caption.** Pooled empirical selective risk of the registered policy scores at the exploratory grid {0.05, …, 0.25} that the R2 diagnostics fixed before this analysis; 0.25 is the largest grid point inside the shared attainable region. At 0.25 (6,999 SPECIFIC calls each): s_C 0.146, s_C−D 0.152, guarded confidence 0.238, conventional confidence 0.422. Margin and −entropy are listed in H1-T04 and the analysis CSV. No point beyond the shared region is drawn; uncertainty is shown in H1-F02b.

**Interpretation limit.** Simulated H2-SimNet topologies; all outer-test windows were inspected in R2; 91.7 % of classifier errors lie in runs whose source-model attribution is disputed (owner decision D1 pending). Not a confirmation of H1.

**Source data.**
- `h1_validation/analysis/h1_04_selection_by_method.csv`

**Code.** `scripts/fig_h1.py::plot_h1_selective_risk_shared` · Files: `figures/H1-F02a_selective_risk_shared_coverage.png`, `figures/H1-F02a_selective_risk_shared_coverage.svg`
