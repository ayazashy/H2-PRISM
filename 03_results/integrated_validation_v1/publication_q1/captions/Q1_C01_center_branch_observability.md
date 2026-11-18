# Q1_C01 — Sensor observability of each outlet withdrawal

**Scientific question.** Which sensors can observe a withdrawal at each outlet?

**Caption.** Peak absolute intervention − control difference per sensor for the three outlet withdrawals (30 s prefix window). SID 213 excites branch meter MFS3 (0.691 kg/s) and SID 312 excites MFS1 (0.647 kg/s). SID 215 has no branch flow meter: its largest flow response is 3.8e-04 kg/s, and it appears mainly in pressure (largest 0.0056 MPa, PS4/PS8). PS3 duplicates PS10 bitwise; PS5 and PS7 (command channel) do not respond to withdrawals. Logarithmic axes; units are kept in separate panels.

**Interpretation limit.** Sensor layout of one simulated Center model; not a field sensor network.

**Source data.**
- `03_results/validation/center_evidence_enhancement/analysis/channel_signal.csv`

**Code.** `scripts/fig_center.py::plot_center_branch_observability` · Files: `figures/Q1_C01_center_branch_observability.png`, `figures/Q1_C01_center_branch_observability.svg`
