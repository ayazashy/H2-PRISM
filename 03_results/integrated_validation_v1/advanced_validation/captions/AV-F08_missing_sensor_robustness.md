# AV-F08 — Missing-sensor robustness

**Scientific question.** What happens to formal decisions when pressure or flow sensors are lost?

**Caption.** Formal D(Y) outcomes under predeclared sensor losses (restricted universe, ±1 s, S3, S4, S5, REF). Flow-only sensing raises wrong SPECIFIC from 2 to 4 of 24; without MFS3 the correct SPECIFIC decisions drop from 8 to 2 and become ambiguity sets. Removing any single pressure sensor other than those of the SID 215 branch changes nothing. Ambiguity sets without the truth (hatched ochre) are not safe outcomes.

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds.

**Source data.**
- `advanced_validation/analysis/dy_experiment_runs.csv (E1)`

**Code.** `scripts/fig_av.py::plot_av_missing_sensor` · Files: `figures/AV-F08_missing_sensor_robustness.png`, `figures/AV-F08_missing_sensor_robustness.svg`
