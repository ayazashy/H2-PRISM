# AV-F11 — Negative-control false leak attribution

**Scientific question.** Do the policies mistake normal operation for a leak?

**Caption.** Wrong LEAK attributions on the 1,995 NORMAL windows (one normal-operation template simulated in three topologies). The classifier without abstention calls 662 of them LEAK; conventional confidence abstention still issues 655 at coverage 0.25; the evidence policies (s_C, s_C−D) issue none. On Center, the nearest-mechanism rule assigns the command-timing intervention to withdrawal once its own template is removed, whereas formal D(Y) issues no withdrawal decision for either operational intervention (A11b). One template cannot support a rate.

**Interpretation limit.** Simulated H2-SimNet topologies; inspected outer-test windows; 17 independent scenario templates; 91.7 % of classifier errors in runs with disputed attribution (D1 pending).

**Source data.**
- `advanced_validation/analysis/av_r2_negative_control_normal.csv`
- `advanced_validation/tables/A11b.csv`

**Code.** `scripts/fig_av.py::plot_av_negative_control` · Files: `figures/AV-F11_negative_control_false_leak.png`, `figures/AV-F11_negative_control_false_leak.svg`
