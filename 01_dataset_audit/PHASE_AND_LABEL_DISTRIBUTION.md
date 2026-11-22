> **AMENDED 2026-11:** statements in this 2026-10-30 document are superseded where listed in [DATASET_AUDIT_AMENDMENT_2026-11.md](DATASET_AUDIT_AMENDMENT_2026-11.md). The original text below is kept unchanged as the historical record.

# H2-PRISM Phase and Label Distribution Specification (Task Y3)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30 18:22:43 UTC

### Topology Distribution:
- **Center**: 19 scenarios
- **Downstream**: 19 scenarios
- **Upstream**: 19 scenarios

### Topology x Event Contingency:
```
event_raw   Combined_CompressorFault_LeakG5  Combined_LeakG4_CompressorFault  CompressorDelay  CompressorFault  Leak_G3  Leak_G3_G4  Leak_G3_G5  Leak_G3_G6  Leak_G4  Leak_G5  Leak_G5_G6  Leak_G6  NORMAL
topology                                                                                                                                                                                                  
Center                                    1                                1                1                2        2           2           1           1        3        2           1        1       1
Downstream                                1                                1                1                2        2           2           1           1        3        2           1        1       1
Unknown                                   0                                0                0                0        0           0           0           0        1        0           0        0       0
Upstream                                  1                                1                1                2        2           2           1           1        3        2           1        1       1
```
Every simulated fault exists across all three withdrawal topologies, enabling clean cross-topology generalization evaluation.
