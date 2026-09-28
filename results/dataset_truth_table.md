# H2-SimNet Dataset Truth Table & Scenario Catalog

- **Total Scenarios Analyzed**: 123
- **Total Timesteps**: 2,478,894
- **Verified Columns**: `CompressorDelay, CompressorFault, Leak, MFS1, MFS2, MFS3, MFS4, PS1, PS10, PS11, PS12, PS2, PS3, PS4, PS5, PS6, PS7, PS8, PS9, Timestamp, label_anomaly, leak_G3, leak_G4, leak_G5, leak_G6`
- **Sampling Rate**: Verified at nominal 1.0 Hz (20,000 steps = ~5.5 hours per scenario)

## Scenario Distribution

| topology    | operational_phase   | fault_type            |   count |
|:------------|:--------------------|:----------------------|--------:|
| gest_center | normal_operation    | NORMAL                |       4 |
| gest_down   | initial_rampup      | LEAK_G3               |       2 |
| gest_down   | initial_rampup      | LEAK_G4               |       2 |
| gest_down   | normal_operation    | NORMAL                |       4 |
| gest_down   | steady_state        | COMPRESSOR_DELAY_C1   |       2 |
| gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |       6 |
| gest_down   | steady_state        | LEAK_G3               |      10 |
| gest_down   | steady_state        | LEAK_G4               |       4 |
| gest_down   | steady_state        | leakG5_strong         |       2 |
| gest_down   | steady_state        | leakG5_weak           |       2 |
| gest_down   | steady_state        | leakG6                |       2 |
| gest_down   | transient           | LEAK_G4               |       2 |
| gest_down   | transient           | LEAK_G5_G6_OVERLAPPED |       3 |
| gest_up     | initial_rampup      | LEAK_G3               |       2 |
| gest_up     | initial_rampup      | LEAK_G4               |       2 |
| gest_up     | normal_operation    | NORMAL                |       4 |
| gest_up     | steady_state        | COMPRESSOR_DELAY_C1   |       2 |
| gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |       6 |
| gest_up     | steady_state        | LEAK_G3               |      10 |
| gest_up     | steady_state        | LEAK_G4               |       4 |
| gest_up     | steady_state        | leakG5_strong         |       2 |
| gest_up     | steady_state        | leakG5_weak           |       2 |
| gest_up     | steady_state        | leakG6                |       2 |
| gest_up     | transient           | LEAK_G4               |       2 |
| gest_up     | transient           | LEAK_G5_G6_OVERLAPPED |       3 |
| unknown     | initial_rampup      | LEAK_G3               |       2 |
| unknown     | initial_rampup      | LEAK_G4               |       2 |
| unknown     | steady_state        | COMPRESSOR_DELAY_C1   |       2 |
| unknown     | steady_state        | COMPRESSOR_FAULT_C1   |       6 |
| unknown     | steady_state        | LEAK_G3               |      10 |
| unknown     | steady_state        | LEAK_G4               |       4 |
| unknown     | steady_state        | leakG5_strong         |       2 |
| unknown     | steady_state        | leakG5_weak           |       2 |
| unknown     | steady_state        | leakG6                |       2 |
| unknown     | transient           | LEAK_G4               |       2 |
| unknown     | transient           | LEAK_G5_G6_OVERLAPPED |       3 |

## Complete Scenario Catalog

| file_id   | file_name                     | topology    | operational_phase   | fault_type            |   has_anomaly |   anomaly_fraction |
|:----------|:------------------------------|:------------|:--------------------|:----------------------|--------------:|-------------------:|
| scen_001  | leakG4.csv                    | unknown     | transient           | LEAK_G4               |             1 |             0.98   |
| scen_002  | leakG5G6_overlapped.csv       | unknown     | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_003  | leakG5G6_overlapped_noisy.csv | unknown     | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_004  | brokenC1G5_weak.csv           | unknown     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_005  | brokenC1_strong.csv           | unknown     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_006  | brokenC1_weak.csv             | unknown     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_007  | leakG3.csv                    | unknown     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_008  | leakG3G4_strong.csv           | unknown     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_009  | leakG3G4_weak.csv             | unknown     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_010  | leakG3G5_overlapped.csv       | unknown     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_011  | leakG3G6.csv                  | unknown     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_012  | leakG4_strong.csv             | unknown     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_013  | leakG4_weak.csv               | unknown     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_014  | leakG5_strong.csv             | unknown     | steady_state        | leakG5_strong         |             1 |             0.75   |
| scen_015  | leakG5_weak.csv               | unknown     | steady_state        | leakG5_weak           |             1 |             0.75   |
| scen_016  | leakG6.csv                    | unknown     | steady_state        | leakG6                |             1 |             0.65   |
| scen_017  | startdelayC1.csv              | unknown     | steady_state        | COMPRESSOR_DELAY_C1   |             1 |             0.0488 |
| scen_018  | leakG3.csv                    | unknown     | initial_rampup      | LEAK_G3               |             1 |             0.995  |
| scen_019  | leakG4brokenC1.csv            | unknown     | initial_rampup      | LEAK_G4               |             1 |             0.9988 |
| scen_020  | leakG4.csv                    | gest_down   | transient           | LEAK_G4               |             1 |             0.98   |
| scen_021  | leakG5G6_overlapped.csv       | gest_down   | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_022  | leakG5G6_overlapped_noisy.csv | gest_down   | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_023  | brokenC1G5_weak.csv           | gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_024  | brokenC1_strong.csv           | gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_025  | brokenC1_weak.csv             | gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_026  | leakG3.csv                    | gest_down   | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_027  | leakG3G4_strong.csv           | gest_down   | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_028  | leakG3G4_weak.csv             | gest_down   | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_029  | leakG3G5_overlapped.csv       | gest_down   | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_030  | leakG3G6.csv                  | gest_down   | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_031  | leakG4_strong.csv             | gest_down   | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_032  | leakG4_weak.csv               | gest_down   | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_033  | leakG5_strong.csv             | gest_down   | steady_state        | leakG5_strong         |             1 |             0.75   |
| scen_034  | leakG5_weak.csv               | gest_down   | steady_state        | leakG5_weak           |             1 |             0.75   |
| scen_035  | leakG6.csv                    | gest_down   | steady_state        | leakG6                |             1 |             0.65   |
| scen_036  | startdelayC1.csv              | gest_down   | steady_state        | COMPRESSOR_DELAY_C1   |             1 |             0.0488 |
| scen_037  | leakG3.csv                    | gest_down   | initial_rampup      | LEAK_G3               |             1 |             0.995  |
| scen_038  | leakG4brokenC1.csv            | gest_down   | initial_rampup      | LEAK_G4               |             1 |             0.9988 |
| scen_039  | leakG4.csv                    | gest_up     | transient           | LEAK_G4               |             1 |             0.98   |
| scen_040  | leakG5G6_overlapped.csv       | gest_up     | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_041  | leakG5G6_overlapped_noisy.csv | gest_up     | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_042  | brokenC1G5_weak.csv           | gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_043  | brokenC1_strong.csv           | gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_044  | brokenC1_weak.csv             | gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_045  | leakG3.csv                    | gest_up     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_046  | leakG3G4_strong.csv           | gest_up     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_047  | leakG3G4_weak.csv             | gest_up     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_048  | leakG3G5_overlapped.csv       | gest_up     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_049  | leakG3G6.csv                  | gest_up     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_050  | leakG4_strong.csv             | gest_up     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_051  | leakG4_weak.csv               | gest_up     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_052  | leakG5_strong.csv             | gest_up     | steady_state        | leakG5_strong         |             1 |             0.75   |
| scen_053  | leakG5_weak.csv               | gest_up     | steady_state        | leakG5_weak           |             1 |             0.75   |
| scen_054  | leakG6.csv                    | gest_up     | steady_state        | leakG6                |             1 |             0.65   |
| scen_055  | startdelayC1.csv              | gest_up     | steady_state        | COMPRESSOR_DELAY_C1   |             1 |             0.0488 |
| scen_056  | leakG3.csv                    | gest_up     | initial_rampup      | LEAK_G3               |             1 |             0.995  |
| scen_057  | leakG4brokenC1.csv            | gest_up     | initial_rampup      | LEAK_G4               |             1 |             0.9988 |
| scen_058  | normality_gest_center.csv     | gest_center | normal_operation    | NORMAL                |             0 |             0      |
| scen_059  | normality_gest_down.csv       | gest_down   | normal_operation    | NORMAL                |             0 |             0      |
| scen_060  | normality_gest_up.csv         | gest_up     | normal_operation    | NORMAL                |             0 |             0      |
| scen_061  | normality_gest_center.csv     | gest_center | normal_operation    | NORMAL                |             0 |             0      |
| scen_062  | normality_gest_down.csv       | gest_down   | normal_operation    | NORMAL                |             0 |             0      |
| scen_063  | normality_gest_up.csv         | gest_up     | normal_operation    | NORMAL                |             0 |             0      |
| scen_064  | normality_gest_center.csv     | gest_center | normal_operation    | NORMAL                |             0 |             0      |
| scen_065  | normality_gest_down.csv       | gest_down   | normal_operation    | NORMAL                |             0 |             0      |
| scen_066  | normality_gest_up.csv         | gest_up     | normal_operation    | NORMAL                |             0 |             0      |
| scen_067  | leakG4.csv                    | unknown     | transient           | LEAK_G4               |             1 |             0.98   |
| scen_068  | leakG5G6_overlapped.csv       | unknown     | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_069  | brokenC1G5_weak.csv           | unknown     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_070  | brokenC1_strong.csv           | unknown     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_071  | brokenC1_weak.csv             | unknown     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_072  | leakG3.csv                    | unknown     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_073  | leakG3G4_strong.csv           | unknown     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_074  | leakG3G4_weak.csv             | unknown     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_075  | leakG3G5_overlapped.csv       | unknown     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_076  | leakG3G6.csv                  | unknown     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_077  | leakG4_strong.csv             | unknown     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_078  | leakG4_weak.csv               | unknown     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_079  | leakG5_strong.csv             | unknown     | steady_state        | leakG5_strong         |             1 |             0.75   |
| scen_080  | leakG5_weak.csv               | unknown     | steady_state        | leakG5_weak           |             1 |             0.75   |
| scen_081  | leakG6.csv                    | unknown     | steady_state        | leakG6                |             1 |             0.65   |
| scen_082  | startdelayC1.csv              | unknown     | steady_state        | COMPRESSOR_DELAY_C1   |             1 |             0.0488 |
| scen_083  | leakG3.csv                    | unknown     | initial_rampup      | LEAK_G3               |             1 |             0.995  |
| scen_084  | leakG4brokenC1.csv            | unknown     | initial_rampup      | LEAK_G4               |             1 |             0.9988 |
| scen_085  | leakG4.csv                    | gest_down   | transient           | LEAK_G4               |             1 |             0.98   |
| scen_086  | leakG5G6_overlapped.csv       | gest_down   | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_087  | brokenC1G5_weak.csv           | gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_088  | brokenC1_strong.csv           | gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_089  | brokenC1_weak.csv             | gest_down   | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_090  | leakG3.csv                    | gest_down   | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_091  | leakG3G4_strong.csv           | gest_down   | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_092  | leakG3G4_weak.csv             | gest_down   | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_093  | leakG3G5_overlapped.csv       | gest_down   | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_094  | leakG3G6.csv                  | gest_down   | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_095  | leakG4_strong.csv             | gest_down   | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_096  | leakG4_weak.csv               | gest_down   | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_097  | leakG5_strong.csv             | gest_down   | steady_state        | leakG5_strong         |             1 |             0.75   |
| scen_098  | leakG5_weak.csv               | gest_down   | steady_state        | leakG5_weak           |             1 |             0.75   |
| scen_099  | leakG6.csv                    | gest_down   | steady_state        | leakG6                |             1 |             0.65   |
| scen_100  | startdelayC1.csv              | gest_down   | steady_state        | COMPRESSOR_DELAY_C1   |             1 |             0.0488 |
| scen_101  | leakG3.csv                    | gest_down   | initial_rampup      | LEAK_G3               |             1 |             0.995  |
| scen_102  | leakG4brokenC1.csv            | gest_down   | initial_rampup      | LEAK_G4               |             1 |             0.9988 |
| scen_103  | leakG4.csv                    | gest_up     | transient           | LEAK_G4               |             1 |             0.98   |
| scen_104  | leakG5G6_overlapped.csv       | gest_up     | transient           | LEAK_G5_G6_OVERLAPPED |             1 |             0.98   |
| scen_105  | brokenC1G5_weak.csv           | gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_106  | brokenC1_strong.csv           | gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_107  | brokenC1_weak.csv             | gest_up     | steady_state        | COMPRESSOR_FAULT_C1   |             1 |             0.9988 |
| scen_108  | leakG3.csv                    | gest_up     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_109  | leakG3G4_strong.csv           | gest_up     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_110  | leakG3G4_weak.csv             | gest_up     | steady_state        | LEAK_G3               |             1 |             0.875  |
| scen_111  | leakG3G5_overlapped.csv       | gest_up     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_112  | leakG3G6.csv                  | gest_up     | steady_state        | LEAK_G3               |             1 |             0.8    |
| scen_113  | leakG4_strong.csv             | gest_up     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_114  | leakG4_weak.csv               | gest_up     | steady_state        | LEAK_G4               |             1 |             0.875  |
| scen_115  | leakG5_strong.csv             | gest_up     | steady_state        | leakG5_strong         |             1 |             0.75   |
| scen_116  | leakG5_weak.csv               | gest_up     | steady_state        | leakG5_weak           |             1 |             0.75   |
| scen_117  | leakG6.csv                    | gest_up     | steady_state        | leakG6                |             1 |             0.65   |
| scen_118  | startdelayC1.csv              | gest_up     | steady_state        | COMPRESSOR_DELAY_C1   |             1 |             0.0488 |
| scen_119  | leakG3.csv                    | gest_up     | initial_rampup      | LEAK_G3               |             1 |             0.995  |
| scen_120  | leakG4brokenC1.csv            | gest_up     | initial_rampup      | LEAK_G4               |             1 |             0.9988 |
| scen_121  | normality_gest_center.csv     | gest_center | normal_operation    | NORMAL                |             0 |             0      |
| scen_122  | normality_gest_down.csv       | gest_down   | normal_operation    | NORMAL                |             0 |             0      |
| scen_123  | normality_gest_up.csv         | gest_up     | normal_operation    | NORMAL                |             0 |             0      |
