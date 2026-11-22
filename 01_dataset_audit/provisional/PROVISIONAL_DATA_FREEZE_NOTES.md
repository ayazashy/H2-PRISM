# H2-PRISM Provisional Data Freeze Notes (Task Y8)
**Version**: `v0.1-provisional-2026-10-30`  
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Consumer**: Faisal (ML & Experiments Lead)  
**Reviewer**: Ahmed (Research Lead & Provenance)  
**Date**: 2026-10-30 18:22:44 UTC  
**Status**: **PROVISIONAL / DEVELOPMENT ONLY**

---

## 1. Scope & Objective of Early Handoff

This package enables **Faisal** to begin controlled pipeline development, window generation, and feature extraction immediately, without waiting for the final dataset readiness freeze (Y7).

### Key Rules of Engagement:
1. **Scope of Use**: Faisal may use this package for interface testing, feature extraction, windowing experiments, and baseline exploratory code.
2. **Never Represent as Final**: Any experimental output generated from this package must be marked `PROVISIONAL` or `DEVELOPMENT_ONLY`.
3. **No Outer-Test Tuning**: Grouped splits must respect the declared `Scenario_Family_ID`.

---

## 2. Package Summary & Metrics

| Entity | Count | Notes |
| :--- | :---: | :--- |
| **Total Physical Data Files** | **242** | 123 CSV + 119 Parquet files |
| **Underlying Scenarios (`Scenario_ID`)** | **58** | Distinct simulation configurations |
| **Defensible Families (`Scenario_Family_ID`)** | **13** | Primary grouped independence unit |
| **Eligible Files for Primary 4-Class** | **188** | Single-fault & normal scenarios |
| **Compound Fault Files (Reserved)** | **54** | Simultaneous Leak + Compressor faults |

---

## 3. Verified Channels & Loading Rules for Faisal

1. **Pressure Transmitters**: `PS1` through `PS12` (Unit: MPa, float64).
2. **Mass Flow Meters**: `MFS1` through `MFS4` (Unit: kg/s, float64).
3. **Temperature**: **ZERO localized temperature sensors exist**. Faisal must NOT assume or invent localized temperature columns!
4. **Time & Sampling**:
   - `Timestamp` column in seconds (or 1.0s implicit index).
   - Sampling rate is strictly 1 Hz (dt = 1.0 s).
   - Total duration per run is ~20,000 seconds.
5. **Exact Onset Timings**:
   - Available in `PROVISIONAL_DATA_FREEZE_MANIFEST.csv` under columns `event_onset_s` and `event_offset_s`.
   - Windows crossing the onset boundary should be labeled carefully or flagged as `BOUNDARY_CROSSING`.

---

## 4. Known Data-Quality Issues & Warnings

- **Phase-Event Confounding**: Compressor faults were only injected in initial ramp-up; leaks at steady state. Do NOT use phase as an ML feature.
- **Duplicate Exports**: Parquet and CSV files share identical underlying numerical signals. Faisal must train on ONE format (recommended: canonical Parquet) to avoid duplicate leakage.
