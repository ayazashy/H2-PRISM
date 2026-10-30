# H2-PRISM Scenario Identification & Family Grouping Report (Task Y2)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30 18:22:42 UTC  
**Status**: VERIFIED & FROZEN (Gate 2: Scenario and Label Validity)

---

## 1. Disentangling Physical Files, Scenarios, and Families

To eliminate temporal autocorrelation leakage and prevent artificial sample inflation, H2-PRISM establishes a strict 3-tier hierarchy:

1. **Physical Artifacts (Files)**: 242 tabular data files (CSV and Parquet mirrors across `H2-SimNet-clean/` and `anomalous-scenarios/`).
2. **Underlying Scenarios (`Scenario_ID`)**: **61 distinct physical simulation experiments** after reconciling exact format duplicates.
3. **Scenario Families (`Scenario_Family_ID`)**: **13 defensible independent families** grouping weak/strong parameter variants, noisy perturbations, and shared underlying fault mechanisms.

---

## 2. Verified Scenario Family Distribution

| Scenario Family ID | Primary Physical Event | Unique Scenarios | Topologies Represented | Primary Target Class |
| :--- | :--- | :---: | :---: | :--- |
| **FAM_LEAK_G4** | Leak_G4 | 10 | Center, Downstream, Unknown, Upstream | Leak_G4 |
| **FAM_LEAK_G5G6_COMBINED** | Leak_G5_G6 | 6 | Center, Downstream, Upstream | Leak_G5_G6 |
| **FAM_COMPRESSOR_FAULT_C1** | CompressorFault | 6 | Center, Downstream, Upstream | CompressorFault |
| **FAM_LEAK_G3** | Leak_G3 | 6 | Center, Downstream, Upstream | Leak_G3 |
| **FAM_LEAK_G3G4_COMBINED** | Leak_G3_G4 | 6 | Center, Downstream, Upstream | Leak_G3_G4 |
| **FAM_LEAK_G5** | Leak_G5 | 6 | Center, Downstream, Upstream | Leak_G5 |
| **FAM_COMBINED_BROKEN_C1_LEAK_G5** | Combined_CompressorFault_LeakG5 | 3 | Center, Downstream, Upstream | Combined_CompressorFault_LeakG5 |
| **FAM_LEAK_G3G5_COMBINED** | Leak_G3_G5 | 3 | Center, Downstream, Upstream | Leak_G3_G5 |
| **FAM_LEAK_G3G6_COMBINED** | Leak_G3_G6 | 3 | Center, Downstream, Upstream | Leak_G3_G6 |
| **FAM_LEAK_G6** | Leak_G6 | 3 | Center, Downstream, Upstream | Leak_G6 |
| **FAM_COMPRESSOR_DELAY_C1** | CompressorDelay | 3 | Center, Downstream, Upstream | CompressorDelay |
| **FAM_COMBINED_LEAK_G4_BROKEN_C1** | Combined_LeakG4_CompressorFault | 3 | Center, Downstream, Upstream | Combined_LeakG4_CompressorFault |
| **FAM_NORMALITY** | NORMAL | 3 | Center, Downstream, Upstream | NORMAL |

---

## 3. Strict Rules for Faisal & Ahmed (Model Splits)

> [!WARNING]
> **Non-Negotiable Leakage Prevention Rules**:
> 1. **Primary Splitting Unit**: All grouped cross-validation, outer test holdouts, and reference sets **MUST** split strictly on `Scenario_Family_ID` (or `Scenario_ID` under declared sensitivity).
> 2. **Never Split Across Windows of the Same Scenario**: Consecutive time windows share >99% temporal autocorrelation. Window splitting causes catastrophic optimistic bias.
> 3. **Weak and Strong Variants Cannot Be Separated**: `leakG4_weak` and `leakG4_strong` share identical pipeline geometry, initial conditions, and simulator state. They belong to `FAM_LEAK_G4`. Putting one in train and the other in test invalidates out-of-distribution evaluation!
