# AV-F03 — Classification error attribution

**Scientific question.** Which event classes produce the wrong SPECIFIC decisions?

**Caption.** Wrong / SPECIFIC decisions per true class for the classifier without abstention (all windows) and for each policy at coverage 0.25. LEAK errors (LEAK → NORMAL in Center) dominate every policy; the NORMAL errors of the conventional scores (NORMAL → LEAK) come from one template. Class supports: NORMAL 1,995, LEAK 21,921, FAULT 3,984, DELAY 93 windows from 1, 13, 2 and 1 scenario templates.

**Interpretation limit.** Simulated H2-SimNet topologies; inspected outer-test windows; 17 independent scenario templates; 91.7 % of classifier errors in runs with disputed attribution (D1 pending).

**Source data.**
- `advanced_validation/analysis/av_r2_wrong_specific_by_class.csv`

**Code.** `scripts/fig_av.py::plot_av_error_attribution` · Files: `figures/AV-F03_error_attribution_by_class.png`, `figures/AV-F03_error_attribution_by_class.svg`
