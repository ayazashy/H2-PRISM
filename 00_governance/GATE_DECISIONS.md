# H2-PRISM Research Gate Decisions Ledger
**Governance Owner**: Ahmed (Research Lead), Co-Owners: Faisal (ML Lead), Yazan (Dataset Readiness Lead)  
**Last Updated**: 2026-10-30  
**Overall Project Deadline**: 4 November 2026

---

## Gate Register & Approval Status

| Gate ID | Gate Name | Responsible Owner | Supporting Evidence Required | Decision | Decision Date |
| :--- | :--- | :--- | :--- | :---: | :---: |
| **Gate 1** | **Dataset Integrity** | Yazan | `FILE_LEVEL_AUDIT.csv`, `raw_checksums.sha256`, `DUPLICATE_EXPORT_AUDIT.csv`, `SENSOR_CHANNEL_AUDIT.csv` | **PASS** | 2026-10-30 |
| **Gate 2** | **Scenario and Label Validity** | Yazan | `DATASET_SCENARIO_MAP.csv`, `SCENARIO_RELATIONSHIP_EDGES.csv`, `LABEL_OVERLAP_MATRIX.csv`, `class_mapping.yaml` | **PASS** | 2026-10-30 |
| **Gate 3** | **Evaluation Feasibility** | Yazan | `FAMILY_CLASS_DISTRIBUTION.csv`, `SPLIT_FEASIBILITY_REPORT.md`, `DATA_LEAKAGE_ASSESSMENT.md`, `folds.csv` | **PASS** | 2026-10-30 |
| **Gate 4** | **Baseline Modeling & Leakage Assertions** | Faisal | `BASELINE_RESULTS.csv`, `BASELINE_CONFUSION_MATRIX.csv`, inner grouped CV validation | **IN PROGRESS** | — |
| **Gate 5** | **Empirical Distinguishability D(x)** | Faisal | `D_STATISTIC_DESIGN_DECISION.md`, test suite passing, permutation test invariance | **SPECIFIED** | — |
| **Gate 6** | **Selective Diagnostic Policy** | Faisal | `SELECTIVE_DIAGNOSTIC_POLICY.md`, candidate set truncation rules, threshold calibration | **SPECIFIED** | — |
| **Gate 7** | **Primary Comparison & Statistical Validation**| Faisal | Matched coverage evaluation (C vs C-D, C vs B), clustered bootstrap confidence intervals | **SPECIFIED** | — |
| **Gate 8** | **Final Scientific Closure & Methodology Freeze** | Ahmed | Final manuscript, provenance register, complete traceability matrix, reproducibility verify | **PENDING** | — |

---

## Detailed Decisions Log

### Gate 1: Dataset Integrity (Approved: 2026-10-30)
- **Reviewer**: Yazan (Lead)
- **Findings**: All 265 physical raw files inventoried with SHA-256 hashes. Sensor channels PS1–PS12 (MPa) and MFS1–MFS4 (kg/s) confirmed. Absence of temperature channels verified. All duplicate export trees classified.
- **Decision**: **PASS**.

### Gate 2: Scenario & Label Validity (Approved: 2026-10-30)
- **Reviewer**: Yazan (Lead), Approved for Scientific Modeling by Ahmed & Faisal.
- **Findings**: 242 tabular data files reconciled into 58 distinct simulation configurations and 13 defensible families. Phase-event confounding identified. Primary 4-class target frozen in `class_mapping.yaml`. Compound multi-fault scenarios excluded from primary task.
- **Decision**: **PASS**.

### Gate 3: Evaluation Feasibility (Approved: 2026-10-30)
- **Reviewer**: Yazan (Lead), Handoff to Faisal.
- **Findings**: Blind global LOFO proven mathematically invalid due to 1-family classes. 3-fold topology-stratified cross-validation proven feasible with all 4 classes present in both train and test across all folds, with zero leakage.
- **Decision**: **PASS**.

---

## Gates 1-3: evidence re-verification (A-D10), 2026-11-11

The 2026-10-30 entries above are kept unchanged as the historical record. The audit found that several of their findings were not supported by evidence:
- 265 files (the official archive has 264);
- 58 configurations and 13 families (actual: 57 runs, 39 primary families);
- "zero leakage" (in fact, every family appeared on both sides of every fold: ISS-01, ISS-02, ISS-11).

Gates 1–3 were re-verified from repository evidence on 2026-11-11. This is engineering verification only, not a named-owner attestation. Details: `06_audit_preparation/final_acceptance/FINAL_GOVERNANCE_AND_GATE_RECORD.md`.

| Gate | Engineering re-verification | Named attestation (Yazan owner; Ahmed re-record, A-D10) |
| --- | --- | --- |
| Gate 1 Dataset Integrity | PASS: official archive (MD5 `15bc64a3…`) holds 264 files, all matching `RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256`; channels PS1–PS12 and MFS1–MFS4; 1 s sampling for the modelling files; 0 non-finite features | PENDING (not recorded) |
| Gate 2 Scenario and Label Validity | CONDITIONAL: manifest v0.2 has 57 runs, 51 eligible and 39 primary families nested in topology; 6 exclusions with reasons; ancestry, location labels and annotation anomalies are restricted (Y-D03, Y-D05a/b, Y-D06a) | PENDING (not recorded) |
| Gate 3 Evaluation Feasibility | CONDITIONAL: LOTO folds are executable, with 0 family, topology or run overlap and every class in every fold; NORMAL, DELAY and FAULT per-class results are descriptive only | PENDING (not recorded) |
