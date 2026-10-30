# H2-PRISM Label Hierarchy & Overlap Audit (Task Y4)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30 18:22:43 UTC  
**Status**: VERIFIED & FROZEN FOR FAISAL

---

## 1. Label Co-occurrence & Overlap Matrix

Analysis of label activation across all 58 scenarios:

```
                 label_anomaly  Leak  CompressorFault  CompressorDelay  leak_G3  leak_G4  leak_G5  leak_G6
label_anomaly               55    43               12                3       18       22       12        9
Leak                        43    43                3                0       18       22        9        9
CompressorFault             12     3               12                0        0        3        3        0
CompressorDelay              3     0                0                3        0        0        0        0
leak_G3                     18    18                0                0       18        6        3        3
leak_G4                     22    22                3                0        6       22        0        3
leak_G5                     12     9                3                0        3        0       12        0
leak_G6                      9     9                0                0        3        3        0        9
```

---

## 2. Structural Label Relationships & Exclusions

1. **Hierarchy (Parent vs Child)**:
   - `Leak` is an umbrella category: whenever any of `leak_G3`, `leak_G4`, `leak_G5`, or `leak_G6` is 1, `Leak` is 1.
   - Categorical valve labels (`leak_G3` to `G6`) specify the restriction location; they are **not** metric coordinates.
2. **Compressor Fault vs Compressor Delay**:
   - `CompressorFault` represents reduced ramp amplitude (C1).
   - `CompressorDelay` represents delayed startup (C1).
   - In single-fault scenarios, they are strictly mutually exclusive.
3. **Compound Faults (Exclusion Rule for Primary Task)**:
   - Scenarios `brokenC1G5_weak` and `leakG4brokenC1` contain simultaneous `CompressorFault` and `Leak`.
   - **Ruling**: For the primary mutually exclusive 4-class attribution task, compound scenarios are **EXCLUDED** from training to ensure mathematical validity (p(x) in simplex). They are reserved for secondary multi-label evaluation.
