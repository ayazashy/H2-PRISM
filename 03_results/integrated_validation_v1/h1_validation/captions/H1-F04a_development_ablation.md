# H1-F04a — Development ablation of D(x)

**Scientific question.** Does D(x) add decision value beyond confidence on development data?

**Caption.** Protocol 2.0 development ablation (means over outer folds; same 27,993 windows). In every arm where the operating point is estimable, s_C, s_C−D and confidence have identical group-balanced risk (A, D, E: 0 vs 0 floor on one topology; C: 0.045; G1: 0.091; G2: s_C and s_C−D 0.091, confidence 0.095). Arms B and F have no estimable operating point and are omitted from the plot (listed in H1-T05a).

**Interpretation limit.** Development-only, exploratory; windows were inspected as R2 outer test.

**Source data.**
- `03_results/ablation/ARM_SUMMARY.csv`

**Code.** `scripts/fig_h1.py::plot_h1_development_ablation` · Files: `figures/H1-F04a_development_ablation.png`, `figures/H1-F04a_development_ablation.svg`
