# Q1_C06 — Detector behaviour under sensor stress

**Scientific question.** How do hypothetical sensor stresses change detection and false alarms?

**Caption.** One-second causal replay under hypothetical sensor perturbations (white and correlated noise, bias, drift, stuck, delay). Correlated noise drives CUSUM to 3.44 false episodes per hour, and the reference detector raises a persistent alarm (no new-alert detections) under white and correlated noise. Each metric keeps its own scale.

**Interpretation limit.** Perturbations are hypothetical, without industrial calibration.

**Source data.**
- `03_results/validation/publication_final_v1/tables/TAB_05.csv`

**Code.** `scripts/fig_center.py::plot_center_sensor_stress` · Files: `figures/Q1_C06_center_sensor_stress.png`, `figures/Q1_C06_center_sensor_stress.svg`
