# Q1_I08 — Three-outcome decision shares

**Scientific question.** Does the policy produce specific, ambiguous and unresolved outcomes in a class-interpretable way?

**Caption.** Registered RQ3 outcome shares of the s_C policy at rank-matched coverage 0.60, pooled over the two outer folds where 0.60 is attainable (Center absent). Every SPECIFIC decision is correct (0 of 11,198 wrong) and all 31 ambiguity sets (size 2) contain the true class; compressor-fault windows are never decided because the support flags block them. LEAK is reported as 'restricted', the other classes as descriptive only (registered rule).

**Interpretation limit.** Two topologies, one or two families per thin class; inspected outer test.

**Source data.**
- `03_results/primary_protocol/PRIMARY/rq2.csv`
- `h1_validation/analysis/h1_06_three_outcome_validity_r2.csv`

**Code.** `scripts/fig_integrated.py::plot_integrated_rq3_outcomes` · Files: `figures/Q1_I08_integrated_rq3_outcomes.png`, `figures/Q1_I08_integrated_rq3_outcomes.svg`
