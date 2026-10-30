# H2-PRISM Proposed Grouped Evaluation Design (Task Y5)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Target Consumer**: Faisal (ML Lead)  
**Date**: 2026-10-30 18:22:44 UTC

### Exact Outer Fold Specifications (Handoff to Faisal):
- **Fold 1**:
  - Test Topology: `DOWNSTREAM` (17 scenarios, all 4 classes present)
  - Train Topologies: `CENTER` + `UPSTREAM` (34 scenarios, all 4 classes present)
- **Fold 2**:
  - Test Topology: `CENTER` (17 scenarios, all 4 classes present)
  - Train Topologies: `DOWNSTREAM` + `UPSTREAM` (34 scenarios, all 4 classes present)
- **Fold 3**:
  - Test Topology: `UPSTREAM` (17 scenarios, all 4 classes present)
  - Train Topologies: `DOWNSTREAM` + `CENTER` (34 scenarios, all 4 classes present)

Full scenario-by-fold mapping is persisted in `01_dataset_audit/folds.csv`.
