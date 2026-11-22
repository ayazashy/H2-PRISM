# H2-SimNet Dataset Truth Table & Provenance Catalog

- **Total Scenarios Audited**: 123
- **Total Timesteps Across Scenarios**: 2,478,894
- **Verified Signal Channels**: `CompressorDelay, CompressorFault, Leak, MFS1, MFS2, MFS3, MFS4, PS1, PS10, PS11, PS12, PS2, PS3, PS4, PS5, PS6, PS7, PS8, PS9, Timestamp, label_anomaly, leak_G3, leak_G4, leak_G5, leak_G6`
- **Nominal Sampling Resolution**: 1.0 s / 1 Hz (Each scenario = 20,000 timesteps ≈ 5.5 hours)

## Scenario Distribution by Operational Category

| Topology | Phase | Fault Type | Scenario Count |
| :--- | :--- | :--- | :--- |
| `gest_center` | `normal_operation` | `NORMAL` | 4 |
| `gest_down` | `initial_rampup` | `LEAK_G3` | 2 |
| `gest_down` | `initial_rampup` | `LEAK_G4` | 2 |
| `gest_down` | `normal_operation` | `NORMAL` | 4 |
| `gest_down` | `steady_state` | `COMPRESSOR_DELAY_C1` | 2 |
| `gest_down` | `steady_state` | `COMPRESSOR_FAULT_C1` | 6 |
| `gest_down` | `steady_state` | `LEAK_G3` | 10 |
| `gest_down` | `steady_state` | `LEAK_G4` | 4 |
| `gest_down` | `steady_state` | `leakG5_strong` | 2 |
| `gest_down` | `steady_state` | `leakG5_weak` | 2 |
| `gest_down` | `steady_state` | `leakG6` | 2 |
| `gest_down` | `transient` | `LEAK_G4` | 2 |
| `gest_down` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 3 |
| `gest_up` | `initial_rampup` | `LEAK_G3` | 2 |
| `gest_up` | `initial_rampup` | `LEAK_G4` | 2 |
| `gest_up` | `normal_operation` | `NORMAL` | 4 |
| `gest_up` | `steady_state` | `COMPRESSOR_DELAY_C1` | 2 |
| `gest_up` | `steady_state` | `COMPRESSOR_FAULT_C1` | 6 |
| `gest_up` | `steady_state` | `LEAK_G3` | 10 |
| `gest_up` | `steady_state` | `LEAK_G4` | 4 |
| `gest_up` | `steady_state` | `leakG5_strong` | 2 |
| `gest_up` | `steady_state` | `leakG5_weak` | 2 |
| `gest_up` | `steady_state` | `leakG6` | 2 |
| `gest_up` | `transient` | `LEAK_G4` | 2 |
| `gest_up` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 3 |
| `unspecified` | `initial_rampup` | `LEAK_G3` | 2 |
| `unspecified` | `initial_rampup` | `LEAK_G4` | 2 |
| `unspecified` | `steady_state` | `COMPRESSOR_DELAY_C1` | 2 |
| `unspecified` | `steady_state` | `COMPRESSOR_FAULT_C1` | 6 |
| `unspecified` | `steady_state` | `LEAK_G3` | 10 |
| `unspecified` | `steady_state` | `LEAK_G4` | 4 |
| `unspecified` | `steady_state` | `leakG5_strong` | 2 |
| `unspecified` | `steady_state` | `leakG5_weak` | 2 |
| `unspecified` | `steady_state` | `leakG6` | 2 |
| `unspecified` | `transient` | `LEAK_G4` | 2 |
| `unspecified` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 3 |


## Representative Scenario Sample Catalog

| ID | File Name | Topology | Phase | Fault Type | Has Anomaly | Anomaly Ratio |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `scen_001` | `leakG4.csv` | `unspecified` | `transient` | `LEAK_G4` | 1 | 0.98 |
| `scen_002` | `leakG5G6_overlapped.csv` | `unspecified` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 1 | 0.98 |
| `scen_003` | `leakG5G6_overlapped_noisy.csv` | `unspecified` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 1 | 0.98 |
| `scen_004` | `brokenC1G5_weak.csv` | `unspecified` | `steady_state` | `COMPRESSOR_FAULT_C1` | 1 | 0.9988 |
| `scen_005` | `brokenC1_strong.csv` | `unspecified` | `steady_state` | `COMPRESSOR_FAULT_C1` | 1 | 0.9988 |
| `scen_006` | `brokenC1_weak.csv` | `unspecified` | `steady_state` | `COMPRESSOR_FAULT_C1` | 1 | 0.9988 |
| `scen_007` | `leakG3.csv` | `unspecified` | `steady_state` | `LEAK_G3` | 1 | 0.8 |
| `scen_008` | `leakG3G4_strong.csv` | `unspecified` | `steady_state` | `LEAK_G3` | 1 | 0.875 |
| `scen_009` | `leakG3G4_weak.csv` | `unspecified` | `steady_state` | `LEAK_G3` | 1 | 0.875 |
| `scen_010` | `leakG3G5_overlapped.csv` | `unspecified` | `steady_state` | `LEAK_G3` | 1 | 0.8 |
| `scen_011` | `leakG3G6.csv` | `unspecified` | `steady_state` | `LEAK_G3` | 1 | 0.8 |
| `scen_012` | `leakG4_strong.csv` | `unspecified` | `steady_state` | `LEAK_G4` | 1 | 0.875 |
| `scen_013` | `leakG4_weak.csv` | `unspecified` | `steady_state` | `LEAK_G4` | 1 | 0.875 |
| `scen_014` | `leakG5_strong.csv` | `unspecified` | `steady_state` | `leakG5_strong` | 1 | 0.75 |
| `scen_015` | `leakG5_weak.csv` | `unspecified` | `steady_state` | `leakG5_weak` | 1 | 0.75 |
| `scen_016` | `leakG6.csv` | `unspecified` | `steady_state` | `leakG6` | 1 | 0.65 |
| `scen_017` | `startdelayC1.csv` | `unspecified` | `steady_state` | `COMPRESSOR_DELAY_C1` | 1 | 0.0488 |
| `scen_018` | `leakG3.csv` | `unspecified` | `initial_rampup` | `LEAK_G3` | 1 | 0.995 |
| `scen_019` | `leakG4brokenC1.csv` | `unspecified` | `initial_rampup` | `LEAK_G4` | 1 | 0.9988 |
| `scen_020` | `leakG4.csv` | `gest_down` | `transient` | `LEAK_G4` | 1 | 0.98 |
| `scen_021` | `leakG5G6_overlapped.csv` | `gest_down` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 1 | 0.98 |
| `scen_022` | `leakG5G6_overlapped_noisy.csv` | `gest_down` | `transient` | `LEAK_G5_G6_OVERLAPPED` | 1 | 0.98 |
| `scen_023` | `brokenC1G5_weak.csv` | `gest_down` | `steady_state` | `COMPRESSOR_FAULT_C1` | 1 | 0.9988 |
| `scen_024` | `brokenC1_strong.csv` | `gest_down` | `steady_state` | `COMPRESSOR_FAULT_C1` | 1 | 0.9988 |
| `scen_025` | `brokenC1_weak.csv` | `gest_down` | `steady_state` | `COMPRESSOR_FAULT_C1` | 1 | 0.9988 |
| `scen_026` | `leakG3.csv` | `gest_down` | `steady_state` | `LEAK_G3` | 1 | 0.8 |
| `scen_027` | `leakG3G4_strong.csv` | `gest_down` | `steady_state` | `LEAK_G3` | 1 | 0.875 |
| `scen_028` | `leakG3G4_weak.csv` | `gest_down` | `steady_state` | `LEAK_G3` | 1 | 0.875 |
| `scen_029` | `leakG3G5_overlapped.csv` | `gest_down` | `steady_state` | `LEAK_G3` | 1 | 0.8 |
| `scen_030` | `leakG3G6.csv` | `gest_down` | `steady_state` | `LEAK_G3` | 1 | 0.8 |

*(Truncated: 123 total records recorded in `results/materials_manifest.csv`)*
