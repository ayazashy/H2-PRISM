# V2-F02 — Sensor-failure robustness (synthetic)

**Scientific question.** Do injected sensor faults or timestamp jitter make the formal engine issue more wrong SPECIFIC decisions?

**Caption.** Outcome shares per perturbation. No fault setting raised the count of wrong SPECIFIC decisions above the unperturbed baseline, but at 2 ε_obs bias or drift the correct SPECIFIC decisions are lost first, so the wrong share among SPECIFIC decisions rises; at larger magnitudes every decision becomes UNRESOLVED (all hypotheses excluded). ±1-sample jitter left every outcome unchanged at τ = 1 s.

**Interpretation limit.** Synthetic perturbations of six Center captures under hypothetical bounds; magnitudes are relative to ε_obs, not sensor specifications.

**Source data.**
- `03_results/integrated_validation_v2/04_results/analysis/s1_dy_synthetic_stress_runs.csv`

**Code.** `scripts/fig_v2.py::f02` · Files: `figures/V2-F02_dy_synthetic_sensor_faults.png`, `figures/V2-F02_dy_synthetic_sensor_faults.svg`
