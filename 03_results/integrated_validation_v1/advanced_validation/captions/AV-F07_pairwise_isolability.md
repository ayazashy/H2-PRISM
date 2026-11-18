# AV-F07 — Sensor-dependent pairwise isolability

**Scientific question.** Which event pairs are distinguishable under each sensor configuration?

**Caption.** Template-level pairwise isolability at the REF bounds (0.0344 MPa, 0.0182 kg/s total) with ±1 s alignment: a pair is separable if, for every pair of admissible shifts, some coordinate differs by more than twice the bound. Normal operation and the SID 215 withdrawal are not separable even with all channels. Exhaustive search: 2 channels (MFS1+MFS3) preserve all 14 separable pairs (A16b). Conditional on declared bounds.

**Interpretation limit.** Center controlled simulation (air-like gas model, one source family); six captures viewed under several declared conditions — counts, not rates; hypothetical bounds.

**Source data.**
- `advanced_validation/analysis/dy_pairwise_isolability.csv`
- `dy_minimum_sensor_sets.csv`

**Code.** `scripts/fig_av.py::plot_av_isolability` · Files: `figures/AV-F07_pairwise_isolability.png`, `figures/AV-F07_pairwise_isolability.svg`
