# AV-F13 — Sensor count–risk–coverage trade-off

**Scientific question.** Which sensor arrangements keep decision quality with fewer channels?

**Caption.** Structured sensor configurations of the Center network: correct and wrong SPECIFIC formal decisions (24 per configuration) against the number of channels, the only measured cost axis (no source-supported sensor prices exist, A15). Filled markers: Pareto-nondominated on (fewer channels, more correct, fewer wrong). 'Without MFS1' avoids the two wrong decisions only by returning ambiguity sets without the truth. Template-level isolability needs 2 channels (MFS1+MFS3) at REF bounds (A16b).

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds. No monetary cost is estimated.

**Source data.**
- `advanced_validation/tables/A16a.csv`
- `A16b.csv`

**Code.** `scripts/fig_av.py::plot_av_sensor_tradeoff` · Files: `figures/AV-F13_sensor_count_tradeoff.png`, `figures/AV-F13_sensor_count_tradeoff.svg`
