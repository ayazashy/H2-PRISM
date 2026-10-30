# H2-PRISM Dataset Inventory & Integrity Specification (Task Y1)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Verification Date**: 2026-10-30 18:22:42 UTC  
**Status**: VERIFIED & REPRODUCIBLE (Gate 1: Dataset Integrity Audit)

---

## 1. Executive Summary & File-Level Inventory

A forensic inventory of all physical files under `data/raw/` was executed deterministically via `audit/01_inventory_integrity.py`. All SHA-256 hashes are persisted in `raw_checksums.sha256`.

| Metric / Dimension | Verified Value | Evidence Status | Notes |
| :--- | :--- | :--- | :--- |
| **Total Physical Files** | **265** | **VERIFIED** | Encompasses data, models, scripts, and documentation. |
| **Total Raw Storage** | **997.96 MB** (1046436669 bytes) | **VERIFIED** | Complete byte count across all extensions. |
| **CSV Files (`.csv`)** | **123** | **VERIFIED** | Tabular raw/clean simulation exports. |
| **Parquet Files (`.parquet`)** | **119** | **VERIFIED** | Compressed columnar simulation exports. |
| **Simscape/Simulink Models (`.slx`)** | **9** | **VERIFIED** | Original physical gas network simulation models. |
| **MATLAB Code (`.m` / `.asv`)** | **7** (5 .m, 2 .asv) | **VERIFIED** | Simulation drivers and parameters. |
| **Documentation & Schematics (`.pdf`, `.txt`)** | **6** (5 PDF, 1 TXT) | **VERIFIED** | ReadME and network topology schematics. |

---

## 2. Forensic Reconciliation of Inherited Preliminary Claims

The inherited preliminary claims listed in Section 1.2 of Yazan's Plan were audited against ground truth:

| Preliminary Claim | Inherited Specification | Audited Ground Truth | Reconciliation Status | Forensic Finding & Calculation Method |
| :--- | :--- | :--- | :---: | :--- |
| **Dataset Source** | H2-SimNet (Zenodo 17871393) | H2-SimNet (Zenodo 17871393) | **CONFIRMED** | `ReadME.txt` confirms Acampora et al., 2025. |
| **Total File Count** | 121 files | **265 physical files** | **REFUTED** | Actual repository contains 265 files (including model files and duplicate trees). |
| **CSV / Parquet Breakdown** | 60 CSV / 61 Parquet | **123 CSV / 119 Parquet** | **REFUTED** | Found 123 CSVs and 119 Parquets across duplicate export directories. |
| **Sensor Channels** | PS1–PS12, MFS1–MFS4 | **PS1–PS12, MFS1–MFS4** | **CONFIRMED** | 12 pressure sensors, 4 mass flow sensors verified across data files. |
| **Temperature Channels** | No temperature channels | **Zero temperature channels** | **CONFIRMED** | Regex scan across all 242 data files confirmed 0 temperature channels. |
| **Sampling Interval** | ~1-second sampling | **Median dt = 1.0 s** | **CONFIRMED** | All timestamps advance monotonically by exactly 1.0 s; duration ~20,000 s. |
| **Reported Units** | MPa (PS), kg/s (MFS) | **MPa (PS), kg/s (MFS)** | **VERIFIED_FROM_DOCS** | Explicitly stated in `ReadME.txt` (Table: Network Components). |
| **Fluid Composition** | ~10% H2 / 90% CH4 | **10% H2 / 90% CH4 blend** | **REPORTED_UNVERIFIED** | Stated in proposal / Simscape gas fluids configuration; not explicit in raw data columns. |

---

## 3. Duplicate Export Audit Findings

A critical finding of Task Y1 is the presence of duplicate export trees in `data/raw/H2-SimNet-Dataset/`:
1. **Tree A**: `H2-SimNet-clean/` (contains both `csv/` and `parquet/`)
2. **Tree B**: `anomalous-scenarios/` and `normality-scenarios/` (contains parallel `csv/` and `parquet/`)
3. **Tree C**: `MATLAB_SIMSCAPE_Simulation/normality_scenarios/` (contains CSVs of normal runs)

### Cross-Format & Tree Reconciliation:
- **Total Pairwise Comparison Records**: 1423
- **Exact Byte Duplicates**: 12 pairs
- **Numerically Equivalent Exports**: 113 pairs (sensor values match within absolute tolerance 0.0001)
- **Metadata / Column Differences**: 6 pairs (e.g., Parquet contains explicit multi-label binary columns `Leak`, `CompressorFault`, `CompressorDelay`, while corresponding CSVs contain raw sensor signals with implicit labels encoded in directory paths).

> [!IMPORTANT]
> **Duplicate Export Implication for Faisal**:
> CSV and Parquet files represent identical physical simulation runs. They **MUST NEVER** be treated as independent experiments in train/test splits. Counting both CSV and Parquet would double-count data and artificially inflate sample sizes.

---

## 4. Sensor Channel Audit Summary

| Channel | Type | Total Files Present | Reported Unit | Global Min | Global Max | Global Mean ± Std | Missing % |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **MFS1** | mass_flow | 242 | kg/s | -1.0524 | 67.4469 | 12.9483 ± 18.8318 | 0.00% |
| **MFS2** | mass_flow | 242 | kg/s | -1.1832 | 1.1879 | -0.0000 ± 0.1772 | 0.00% |
| **MFS3** | mass_flow | 242 | kg/s | -1.1271 | 70.3054 | 21.1707 ± 26.6112 | 0.00% |
| **MFS4** | mass_flow | 238 | kg/s | 0.0000 | 37.8361 | 9.9923 ± 15.1736 | 0.00% |
| **PS1** | pressure | 242 | MPa | 2.6867 | 7.1118 | 6.4958 ± 1.0700 | 0.00% |
| **PS10** | pressure | 242 | MPa | 0.3167 | 6.5365 | 5.1657 ± 1.4851 | 0.00% |
| **PS11** | pressure | 238 | MPa | 1.3188 | 6.6676 | 4.0325 ± 1.3905 | 0.00% |
| **PS12** | pressure | 238 | MPa | 2.1799 | 6.7349 | 3.5205 ± 1.7743 | 0.00% |
| **PS2** | pressure | 242 | MPa | 2.6389 | 7.0616 | 6.1682 ± 1.1089 | 0.00% |
| **PS3** | pressure | 242 | MPa | 2.1155 | 6.7351 | 5.6524 ± 1.1617 | 0.00% |
| **PS4** | pressure | 242 | MPa | 1.1828 | 6.6420 | 5.1380 ± 1.6894 | 0.00% |
| **PS5** | pressure | 242 | MPa | 0.0977 | 0.7411 | 0.4939 ± 0.2861 | 0.00% |
| **PS6** | pressure | 242 | MPa | 0.2934 | 6.5911 | 4.0456 ± 2.5230 | 0.00% |
| **PS7** | pressure | 242 | MPa | 2.1840 | 7.1224 | 6.3603 ± 1.1433 | 0.00% |
| **PS8** | pressure | 242 | MPa | 1.1828 | 7.1225 | 5.6618 ± 1.4686 | 0.00% |
| **PS9** | pressure | 242 | MPa | 1.2109 | 6.6419 | 5.1785 ± 1.6962 | 0.00% |

---

## 5. Gate 1 Evaluation Decision

- **Gate ID**: `Gate 1 — Dataset Integrity`
- **Owner**: Yazan
- **Decision**: **PASS (with documented duplicate reconciliation)**
- **Justification**:
  1. Every raw file is hashed, categorized, and recorded in `01_dataset_audit/raw_checksums.sha256` and `FILE_LEVEL_AUDIT.csv`.
  2. The relationship between CSV and Parquet exports is mathematically established in `DUPLICATE_EXPORT_AUDIT.csv`.
  3. All sensor channels (`PS1–PS12`, `MFS1–MFS4`) are verified; the absence of temperature channels is confirmed.
  4. Rules for loading data and preventing duplicate inflation are ready for handoff to Faisal and Ahmed.
