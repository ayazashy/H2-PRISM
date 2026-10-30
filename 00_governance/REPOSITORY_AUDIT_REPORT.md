# H2-PRISM Repository Audit & Clean Architecture Report (Task F1 / Stage 2 Transition)
**Auditor**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Co-Reviewers**: Faisal (ML Lead), Ahmed (Research Lead)  
**Date**: 2026-10-30  
**Branch**: `main` (Legacy Stage 1 preserved in `old-main` on remote origin)  
**Status**: APPROVED & CLEANED

---

## 1. Executive Summary & Rationale

At the conclusion of Stage 1, H2-PRISM established an initial prototype dashboard and preliminary baseline models. With the transition to Stage 2 (*Identifiability-Aware Event Attribution and Selective Diagnosis in Hydrogen-Blend Pipeline Networks*), the repository has been cleaned, aligned, and restructured to eliminate legacy technical debt and provide a crystal-clear, professional workspace for any incoming researcher or evaluator.

All legacy Stage 1 artifacts have been safely and permanently preserved in the **`old-main`** Git branch on the remote origin:
`git checkout old-main` (or visit GitHub `ayazashy/H2-PRISM/tree/old-main`).

---

## 2. Directory Layout & Functional Division

| Directory | Functional Role | Primary Owner | Status |
| :--- | :--- | :--- | :---: |
| **`00_governance/`** | Central task register, repository classifications, gate decisions, and change-control logs. | Ahmed / Faisal / Yazan | **ACTIVE** |
| **`01_dataset_audit/`** | Verified dataset inventory, checksums, duplicate reconciliations, scenario family mappings, and provisional freezes. | Yazan | **VERIFIED & FROZEN** |
| **`02_methodology/`** | Mathematical problem formulations, windowing specs, baseline specs, calibration specs, and selective policy designs. | Ahmed / Faisal | **IN PROGRESS** |
| **`03_results/`** | Machine-readable experimental outputs, baseline comparisons, matched coverage results, and ablation data. | Faisal | **PENDING EXECUTION** |
| **`04_validation/`** | Test execution reports, leakage verification reports, and reproducibility audits. | Faisal | **IN PROGRESS** |
| **`05_documentation/`** | Scientific manuscript draft, technical report, provenance register, and claim/limitation ledgers. | Ahmed | **IN PROGRESS** |
| **`assets/`** | Official Stage 2 signed plans (`Ahmed new plan.pdf`, `Faisal new plan.pdf`, `Yazan new plan.pdf`), Proposal, and Authorship agreement. | Team | **FROZEN** |
| **`audit/`** | Deterministic Python audit suite (`run_all_audits.py`) reproducing all dataset readiness findings from scratch in <15s. | Yazan | **VERIFIED** |
| **`configs/`** | YAML configuration files and interface contracts (`interface_contracts.yaml`). | Faisal / Yazan | **ACTIVE** |
| **`data/raw/`** | Primary untouched H2-SimNet dataset (Zenodo record 17871393). | Public Benchmark | **PRESERVED** |
| **`src/h2prism/`** | Clean modular Python package implementing I/O, windowing, features, empirical distinguishability $D(x)$, and selective policy. | Faisal | **IN PROGRESS** |
| **`tests/`** | Automated test suite verifying data integrity, zero leakage, and module correctness. | Team | **ACTIVE** |

---

## 3. Retired Components & Safeguards

The following legacy components were retired from the active `main` branch to prevent confusion, clutter, and unverified assumptions:
- **`UPLOADED_APPLICATION/`** (67 MB): Temporary export folder from initial registration; retired.
- **`video-general/`** (1.1 GB): Node.js Remotion video generator and `node_modules`; retired.
- **`run_prototype.py` & `run_scenario.py`**: Stage 1 prototype scripts; retired.
- **`results/`**: Stage 1 preliminary figures and HTML dashboard; retired.
- **`data/processed/` & `data/selected/`**: Duplicate pre-processed subsets; retired in favor of direct streaming/windowing from raw data.
- **`AUDIT.md`, `ASSUMPTIONS.md`, `MATERIALS.md`**: Superseded by the comprehensive, deterministic specifications in `01_dataset_audit/`.
