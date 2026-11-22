# AV-F02 — False-specific risk at equal coverage

**Scientific question.** At equal coverage, how many wrong SPECIFIC decisions does each policy make, and where?

**Caption.** Counts of wrong SPECIFIC decisions with denominator and risk at two fixed coverage points (identical SPECIFIC counts per method). Every wrong SPECIFIC decision of s_C (1019 at 0.25) lies in runs whose topology attribution is disputed; the guarded conventional scores add 650 errors from the one undisputed Downstream NORMAL run, which the evidence policy withholds. Counts are comparable only because population and coverage are identical.

**Interpretation limit.** Simulated H2-SimNet topologies; inspected outer-test windows; 17 independent scenario templates; 91.7 % of classifier errors in runs with disputed attribution (D1 pending).

**Source data.**
- `advanced_validation/analysis/av_r2_wrong_specific_accounting.csv`

**Code.** `scripts/fig_av.py::plot_av_false_specific_equal_coverage` · Files: `figures/AV-F02_false_specific_equal_coverage.png`, `figures/AV-F02_false_specific_equal_coverage.svg`
