> **AMENDED 2026-11:** statements in this 2026-10-30 document are superseded where listed in [DATASET_AUDIT_AMENDMENT_2026-11.md](DATASET_AUDIT_AMENDMENT_2026-11.md). The original text below is kept unchanged as the historical record.

# H2-PRISM Dataset Readiness Decision Report (Task Y7)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Collaborators / Reviewers**: Faisal (Technical Integration Reviewer); Ahmed (Scientific Interpretation Approval)  
**Evaluation Date**: 2026-10-30 18:22:44 UTC  
**Status**: **FINAL AUDIT DECISION — READY_WITH_EXCLUSIONS**

---

## 1. Formal Readiness Decision

```
========================================================================================
                          DATASET READINESS DECISION
========================================================================================
  [+] DECISION:            READY_WITH_EXCLUSIONS
  [+] PRIMARY TASK TARGET: 4-Class Mutually Exclusive Attribution
                           (NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY)
  [+] PRIMARY EVALUATION:  3-Fold Topology-Stratified Grouped Cross-Validation
  [+] INDEPENDENCE UNIT:   Scenario_Family_ID (Zero Scenario/Topology Leakage)
  [+] STATUS FOR FAISAL:   UNBLOCKED FOR PRIMARY PIPELINE & MODELING
  [+] STATUS FOR AHMED:    APPROVED FOR SCIENTIFIC PROVENANCE & CLAIMS
========================================================================================
```

---

## 2. Audit Evidence Table Linking Findings to Deliverables

| Workstream | Key Verified Finding | Supporting Audit Artifact | Verification Status |
| :--- | :--- | :--- | :---: |
| **Y1: Inventory & Integrity** | 265 physical files, 242 tabular data files (123 CSV, 119 Parquet), exact SHA-256 for all. | `01_dataset_audit/raw_checksums.sha256`<br>`FILE_LEVEL_AUDIT.csv` | **VERIFIED** |
| **Y1: Channels & Units** | Confirmed PS1–PS12 (MPa), MFS1–MFS4 (kg/s); verified 0 temperature channels exist. | `SENSOR_CHANNEL_AUDIT.csv` | **VERIFIED** |
| **Y1: Duplicate Reconciliation** | Identified mirror export trees; resolved 113 numerically equivalent CSV/Parquet pairs. | `DUPLICATE_EXPORT_AUDIT.csv` | **VERIFIED** |
| **Y2: Scenarios & Families** | Reconciled 242 data files into 58 distinct simulation runs and 13 defensible families. | `DATASET_SCENARIO_MAP.csv`<br>`SCENARIO_FAMILY_REPORT.md` | **VERIFIED** |
| **Y3: Timing & Operating Regimes** | Ground truth event onsets verified in Parquet; identified critical Phase-Event Confounding. | `EVENT_TIMING_AUDIT.csv`<br>`PHASE_CONFOUNDING_REPORT.md` | **VERIFIED** |
| **Y4: Label Hierarchy & Mapping** | Documented parent/child structure; generated frozen YAML class mapping. | `ORIGINAL_LABEL_INVENTORY.csv`<br>`class_mapping.yaml` | **VERIFIED** |
| **Y8: Provisional Data Freeze** | Issued versioned manifest (`v0.1-provisional-2026-10-30`) to unblock Faisal. | `provisional/` bundle | **VERIFIED** |
| **Y5: Split Feasibility & Folds** | Proved global LOFO invalid; proved 3-fold topology-stratified CV feasible with 0 leakage. | `SPLIT_FEASIBILITY_REPORT.md`<br>`folds.csv` | **VERIFIED** |

---

## 3. Explicit List of Exclusions & Restrictions

To preserve complete scientific integrity, the following 5 exclusions are strictly enforced:

1. **Exclusion of Compound Multi-Fault Scenarios from Primary Task**:
   - Scenarios `brokenC1G5_weak` and `leakG4brokenC1` contain simultaneous `CompressorFault` and `Leak`.
   - **Restriction**: They are excluded from the primary 4-class mutually exclusive attribution task (p(x) in simplex) and reserved strictly for secondary exploratory multi-label evaluation.
2. **Exclusion of CSV Duplicate Exports from Model Training**:
   - CSV and Parquet files represent identical physical simulation runs.
   - **Restriction**: Faisal must train on canonical Parquet files only to prevent duplicate sample inflation.
3. **Exclusion of Unsupported Continuous Localization Claims**:
   - The dataset contains categorical valve restriction labels (`leak_G3` through `leak_G6`).
   - **Restriction**: These labels represent categorical valve zones, not metric millimeter coordinates.
4. **Exclusion of Pure-Hydrogen Thermodynamic Assumptions**:
   - The H2-SimNet dataset simulates a 10% H2 / 90% CH4 blend in Simscape Gas Fluids R2025a.
   - **Restriction**: Scientific writing must refer strictly to hydrogen-blend networks.
5. **Exclusion of Phase as a Machine Learning Feature**:
   - Compressor faults occur only in initial ramp-up; leaks in steady state.
   - **Restriction**: Operational phase must not be passed as a feature to prevent trivial shortcut learning.

---

## 4. Handoff to Faisal & Ahmed

- **Handoff to Faisal (ML & Experiments Lead)**:
  - You are officially unblocked to execute `F3` (preprocessing/windows), `F4` (evaluation splits using `folds.csv`), `F5` (baseline classifier), and `F7` ($D(x)$ distinguishability).
  - Use `01_dataset_audit/folds.csv` and `01_dataset_audit/class_mapping.yaml` as frozen contracts.
- **Handoff to Ahmed (Research Leadership & Provenance Lead)**:
  - All audit artifacts, SHA-256 hashes, duplicate analyses, and readiness decisions are frozen and ready for citation in `DATA_PROVENANCE.md` (A10), `SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md` (A7), and `METHODOLOGY_MASTER_STRUCTURE.md` (A1).
