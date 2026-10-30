# H2-PRISM Split Feasibility Report (Task Y5)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Consumer**: Faisal (ML & Experiments Lead)  
**Date**: 2026-10-30 18:22:44 UTC  
**Status**: VERIFIED & AUDITED (Gate 3 Deliverable)

---

## 1. Feasibility Analysis of Grouped Splits

### The Fundamental Obstacle of Conservative Global LOFO:
In the conservative view where all topologies are pooled into single global families:
- `NORMAL` has only **1 family** (`FAM_NORMALITY`).
- `COMPRESSOR_FAULT` has only **1 family** (`FAM_COMPRESSOR_FAULT_C1`).
- `COMPRESSOR_DELAY` has only **1 family** (`FAM_COMPRESSOR_DELAY_C1`).
- `LEAK` has **5 families** (`FAM_LEAK_G3`, `G4`, `G5`, `G6`, `G3G4_COMBINED`).

> [!CAUTION]
> **Why Blind Global LOFO Fails Mathematically**:
> If Faisal runs Leave-One-Family-Out holding out `FAM_NORMALITY`, the training set contains **zero normal samples**!
> A classifier cannot train without negative class representation. Conversely, holding out any leak family means test has only leaks.

### The Mathematically Defensible Solution: Topology-Stratified 3-Fold CV
The H2-SimNet dataset was generated across three distinct withdrawal topologies: `Downstream`, `Center`, and `Upstream`.
Every fault and normal baseline was simulated independently under each topology.

**Recommended Evaluation Design**:
- **Outer Fold 1**: Hold out `Downstream` (Train on `Center` + `Upstream`)
- **Outer Fold 2**: Hold out `Center` (Train on `Downstream` + `Upstream`)
- **Outer Fold 3**: Hold out `Upstream` (Train on `Downstream` + `Center`)

**Proof of Feasibility**:
1. All 4 classes (`NORMAL`, `LEAK`, `COMPRESSOR_FAULT`, `COMPRESSOR_DELAY`) are present in **both train and test** in every fold!
2. Zero scenario or topology overlap between train and test.
3. Tests true out-of-distribution generalization across network configurations.
