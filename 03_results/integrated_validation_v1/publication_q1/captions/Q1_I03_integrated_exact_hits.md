# Q1_I03 — Measurement-grid limitation

**Scientific question.** Why do MAE and RMSE disagree across the experimental and operational studies?

**Caption.** Exact-hit share of the persistence reference on the held-out rows of each channel (MHC: 15,885 rows per channel; HY2RES: 43,168 rows). Ridge never predicts a recorded value exactly. Because most recorded values repeat, MAE rewards persistence, while RMSE is decided by the few rows with recorded changes. This is a property of the recording grid, not of instrument accuracy.

**Interpretation limit.** Studies differ in system, data type and evidence level and are not pooled; simulated (Center, H2-SimNet), experimental (MHC) and operational (HY2RES) evidence is reported side by side only.

**Source data.**
- `study_b/.../analysis/resolution.csv`
- `hy2res .../analysis/quantization_comparison.csv`

**Code.** `scripts/fig_integrated.py::plot_integrated_exact_hits` · Files: `figures/Q1_I03_integrated_exact_hits.png`, `figures/Q1_I03_integrated_exact_hits.svg`
