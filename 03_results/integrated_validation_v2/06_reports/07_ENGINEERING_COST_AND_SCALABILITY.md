# Engineering cost and scalability

## Cost categories
Reported separately and never combined (V2-T10):

| category | status | value | source |
|---|---|---|---|
| A training compute | NOT MEASURED in this round | frozen models were not retrained | — |
| B inference compute | MEASURED (time, not money) | D(Y) 13-channel decision median 0.364 s (A14a) | advanced_validation/tables/A14a.csv |
| C sensor acquisition | NOT AVAILABLE | no source-supported prices; see V2-T07 for relative scenarios | A15 |
| D installation and maintenance | NOT AVAILABLE | — | A15 |
| E data generation and simulation | NOT MEASURED | Simscape run times not recorded with the captures | — |
| F operational engineering | NOT AVAILABLE | no consequence-cost basis for false/missed detections | A15 |

## Hypothetical sensor-cost scenarios
Relative units only (V2-T07); these are not prices:
- r = 1: non-dominated configurations: drop_MFS1, flow_only, outage_branch_SID215(PS4,PS8,PS9), outage_branch_SID312(MFS1), pressure_only
- r = 3: non-dominated configurations: drop_MFS1, flow_only, outage_branch_SID312(MFS1), pressure_only
- r = 10: non-dominated configurations: drop_MFS1, outage_branch_SID312(MFS1), pressure_only
- **No financial saving is claimed.**

## Measured compute
- One 13-channel D(Y) decision has a median latency of 0.364 s on AMD Ryzen 5 7520U with Radeon Graphics (8 logical).
- Empirical scaling exponents (A14b): D(Y) vs H_hypotheses: 0.98 over 1–6; D(Y) vs M_channels: 1.02 over 1–13; D(Y) vs S_shifts: 0.00 over 1–101; D(Y) vs T_window_samples: 1.06 over 31–151; D(x) vs K_neighbours: 0.03 over 10–50; D(x) vs N_reference_windows: 0.70 over 1000–20000.
