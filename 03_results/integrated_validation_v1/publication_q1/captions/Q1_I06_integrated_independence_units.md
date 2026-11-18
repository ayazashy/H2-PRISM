# Q1_I06 — Dataset composition and independence

**Scientific question.** How many independent units support the classification evidence?

**Caption.** Units of the registered R2 dataset per class (all three topologies). 27,993 windows come from 51 runs, 39 scenario families and only 17 scenario ancestors, because every template is simulated in all three topologies. Compressor delay and normal operation each rest on one ancestor. Recomputed from the frozen predictions; identical to the forensic independence table.

**Interpretation limit.** Studies differ in system, data type and evidence level and are not pooled; simulated (Center, H2-SimNet), experimental (MHC) and operational (HY2RES) evidence is reported side by side only.

**Source data.**
- `h1_validation/analysis/h1_02_independence_units_check.csv`
- `03_results/diagnostics/forensics/independence_units.csv`

**Code.** `scripts/fig_integrated.py::plot_integrated_independence_units` · Files: `figures/Q1_I06_integrated_independence_units.png`, `figures/Q1_I06_integrated_independence_units.svg`
