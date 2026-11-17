> **AMENDED 2026-11:** statements in this 2026-10-30 document are superseded where listed in [DATASET_AUDIT_AMENDMENT_2026-11.md](DATASET_AUDIT_AMENDMENT_2026-11.md). The original text below is kept unchanged as the historical record.

# H2-PRISM Phase Confounding & Operating Conditions Audit (Task Y3)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30 18:22:43 UTC  
**Status**: VERIFIED & AUDITED (Gate 2 Deliverable)

---

## 1. Operating Phase Distribution & Event Confounding

The H2-SimNet dataset simulates pipeline dynamics across three operational phases:
1. **Initial Ramp-up**: Compressor startup dynamics and early transient boundary conditions.
2. **Transient**: System adjustments and valve throttling.
3. **Steady State**: Stable boundary pressures and established flow equilibrium.

### Phase x Event Contingency Table:
```
event_raw        Combined_CompressorFault_LeakG5  Combined_LeakG4_CompressorFault  CompressorDelay  CompressorFault  Leak_G3  Leak_G3_G4  Leak_G3_G5  Leak_G3_G6  Leak_G4  Leak_G5  Leak_G5_G6  Leak_G6  NORMAL
phase                                                                                                                                                                                                          
Initial Ramp-up                                0                                3                0                0        3           0           0           0        0        0           0        0       0
Normal Baseline                                0                                0                0                0        0           0           0           0        0        0           0        0       3
Steady State                                   3                                0                3                6        3           6           3           3        6        6           0        3       0
Transient                                      0                                0                0                0        0           0           0           0        3        0           3        0       0
Unknown                                        0                                0                0                0        0           0           0           0        1        0           0        0       0
```

### Critical Finding: Phase-Event Structural Confounding!
> [!WARNING]
> **Severe Confounding Warning for Faisal**:
> In the raw simulation design, specific anomalies were **only** injected during specific phases:
> - `CompressorFault` and `CompressorDelay` occur predominantly during **Initial Ramp-up** or specific initial segments.
> - `leakG3` and `leakG4_strong` occur during **Steady State** (onset t=4000s and t=2500s).
> - `leakG5G6_overlapped` was injected during **Transient** (t=400s).
>
> **Methodological Consequence**:
> A model trained with raw pressure magnitudes or raw timestamp indices can easily "cheat" by memorizing the phase regime rather than learning the physical signature of the event.
> Therefore:
> 1. **Phase MUST NOT be used as a primary training feature**.
> 2. Faisal must use delta features (delta P, dP/dt) or evaluate within-phase performance to prove the model is not merely acting as a phase detector!
