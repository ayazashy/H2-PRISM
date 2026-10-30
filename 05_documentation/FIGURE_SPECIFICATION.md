# H2-PRISM Research Figure & Table Specifications (Task A5)
**Governance Owner**: Ahmed (Research Lead), Collaborator: Faisal (ML Lead), Yazan (Readiness Lead)  
**Date**: 2026-10-30  
**Status**: APPROVED SPECIFICATION

---

## 1. Research Figure Register

All research figures are generated deterministically via [`scripts/visualize.py`](../scripts/visualize.py) using publication-grade styling defined in [`src/h2prism/visualization/`](../src/h2prism/visualization/).

| Figure ID | File Path | Primary Research Question / Component | Description & Required Data Inputs |
| :--- | :--- | :---: | :--- |
| **Figure 1** | `03_results/figures/fig1_family_distribution.png` | **Data Audit & Feasibility** (Yazan Y5) | Bar chart comparing independent family counts per class under conservative pooling vs. topology-stratified grouping. Proves necessity of 3-fold CV. |
| **Figure 2** | `03_results/figures/fig2_pipeline_telemetry.png` | **SCADA Telemetry Dynamics** (Yazan Y3) | 2-panel synchronized pressure (PS1..PS12) and mass flow (MFS1..MFS4) timeseries with shaded event duration window. |
| **Figure 3** | `03_results/figures/fig3_confusion_matrix.png` | **Baseline Attribution** (Faisal F5) | Normalized confusion matrix across the 4 primary classes (`NORMAL`, `LEAK`, `COMPRESSOR_FAULT`, `COMPRESSOR_DELAY`) with cell sample counts. |
| **Figure 4** | `03_results/figures/fig4_risk_coverage_curve.png` | **Primary Experimental Comparison** (**RQ1**) | Risk-Coverage curves comparing Method C (Combined with $D(x)$) vs. Method C$-$D (Combined without $D(x)$) vs. Method B (Confidence-only) at matched coverage. |
| **Figure 5** | `03_results/figures/fig5_calibration_reliability.png` | **Probability Calibration** (Faisal F6) | 10-bin reliability diagram with empirical accuracy bars, mean confidence diamonds, sample count histogram, ECE, and Brier score. |
| **Figure 6** | `03_results/figures/fig6_distinguishability_separation.png` | **Empirical Distinguishability** (**RQ1**) | Empirical density histogram of $D(x) = q_{(1)}(x) - q_{(2)}(x)$ stratified by correct vs. incorrect predictions among difficult samples. |

---

## 2. Interactive Executive Dashboard

In addition to static publication figures, the visualization suite generates a standalone single-page HTML report:
- **Location**: [`03_results/dashboard.html`](../03_results/dashboard.html)
- **Features**: Embedded base64 high-resolution plots, executive KPI cards (coverage, selective risk, calibration error), and responsive layout viewable in any browser without external server requirements.
