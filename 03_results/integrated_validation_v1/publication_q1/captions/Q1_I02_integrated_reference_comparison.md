# Q1_I02 — Cross-study reference comparison

**Scientific question.** Is the learned reference better than persistence when errors are expressed on the recording grid?

**Caption.** Pooled held-out differences between the frozen Ridge and persistence references, divided by each channel's observed recording increment so the studies can be read on one dimensionless scale (values are not pooled). MHC P-2 (0.2 barg): ΔMAE +0.072, ΔRMSE -0.012; MHC MFC-3 (0.01 ln/min): ΔMAE +1.068, ΔRMSE -0.028; HY2RES buffer (0.1 bar): ΔMAE +0.015, ΔRMSE -0.028; HY2RES tank (0.1 bar): ΔMAE -0.005, ΔRMSE -0.099. Ridge is worse on MAE except for HY2RES tank pressure and better on RMSE by small amounts; MHC per-run values are in Q1_B05/B06.

**Interpretation limit.** Studies differ in system, data type and evidence level and are not pooled; simulated (Center, H2-SimNet), experimental (MHC) and operational (HY2RES) evidence is reported side by side only.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/resolution.csv`
- `hy2res .../evidence_enhancement/results/analysis/quantization_comparison.csv`

**Code.** `scripts/fig_integrated.py::plot_integrated_reference_comparison` · Files: `figures/Q1_I02_integrated_reference_comparison.png`, `figures/Q1_I02_integrated_reference_comparison.svg`
