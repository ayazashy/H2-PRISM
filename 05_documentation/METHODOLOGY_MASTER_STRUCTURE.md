# Methodology Master Structure (A1)

- **Status:** PRE-EXPERIMENT DRAFT prepared by the technical review from the original plans and the implemented protocol. **Ahmed's approval NOT_RECORDED.**
- No experiment has been executed. Nothing here reports a result.

**Working title:** H₂-PRISM: Identifiability-Aware Event Attribution and Selective Diagnosis in Hydrogen-Blend Pipeline Networks.

- "Identifiability-aware" refers to the **empirical** distinguishability statistic D(x), not to physical identifiability.

## Research questions (primary)

- **RQ1:** Does D(x) provide incremental decision value beyond calibrated confidence, probability margin and entropy at matched coverage?
  - Operationalised as the selective-risk difference s_C vs s_C−D at matched coverage (`02_methodology/STATISTICAL_ANALYSIS_PLAN.md`).
- **RQ2:** Can a selective policy reproducibly produce specific diagnoses, informative ambiguity sets and unresolved outcomes?
  - Operationalised as the per-class outcome shares, ambiguity inclusion and size, and reproducibility under the frozen protocol.

**Exploratory or secondary (never confirmatory):** C vs B and the other indicators, threshold transfer, the warning-only policy, the 9 sensitivity analyses, tie-order sensitivity, and per-class results for NORMAL, FAULT and DELAY.

**Removed promises:** metric leak localisation, physics-constrained diagnosis, field or industrial validation, pure-hydrogen or verified blend-percentage claims, and D(x) superiority or novelty before evidence.

## Architecture → task → evidence → owner

| # | Methodology section | Tasks | Evidence / artifact | Owner | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Data audit and provenance | Y1, Y6→A10 | `01_dataset_audit/DATASET_AUDIT_AMENDMENT_2026-11.md`; `05_documentation/DATA_PROVENANCE.md` | Yazan / Ahmed | VERIFIED (attestation pending) |
| 2 | Scenario and family identification | Y2 | manifest v0.2; `CANDIDATE_FAMILY_MAP.csv` | Yazan | VERIFIED with restriction (Y-D03) |
| 3 | Label mapping and feasibility | Y3, Y4, Y5, Y7 | `CANDIDATE_LABEL_MAPPING.yaml`; `YAZAN_TECHNICAL_ACCEPTANCE_PACKAGE.md` | Yazan | VERIFIED with restrictions |
| 4 | Grouped experimental design | F4 | `02_methodology/GROUPED_EVALUATION_PROTOCOL.md`, `FOLD_VALIDATION_REPORT.md` | Faisal | IMPLEMENTED, TESTED |
| 5 | Preprocessing and windowing | F3 | `PREPROCESSING_SPEC.md`, `WINDOWING_SPEC.md` | Faisal | IMPLEMENTED, TESTED |
| 6 | Time-domain features | F3, A15 | `FEATURE_EXTRACTION_SPEC.md`, `FEATURE_DEFINITION_REGISTER.csv` | Faisal | IMPLEMENTED, TESTED |
| 7 | Random Forest baseline | F5 (LR secondary A14) | `BASELINE_MODEL_SPEC.md` | Faisal | IMPLEMENTED, TESTED |
| 8 | Probability calibration | F6 | `PROBABILITY_CALIBRATION_SPEC.md` | Faisal | IMPLEMENTED, TESTED |
| 9 | kNN reference support q(x), D(x) | F7 | `DISTINGUISHABILITY_MATHEMATICAL_SPEC.md`, `D_STATISTIC_*` | Faisal | IMPLEMENTED, TESTED |
| 10 | Comparators and combined scores | F8, A16 | `UNCERTAINTY_AND_DISTINGUISHABILITY_COMPARATORS.md` | Faisal / Ahmed | IMPLEMENTED, TESTED |
| 11 | Three-outcome selective policy | F9 | `SELECTIVE_DIAGNOSTIC_POLICY.md`, `DECISION_POLICY_PSEUDOCODE.md`, `AMBIGUITY_SET_CONSTRUCTION.md`, `POLICY_THRESHOLD_SELECTION.md` | Faisal | IMPLEMENTED, TESTED |
| 12 | Experimental evaluation (RQ1/RQ2) | F10, F11 | runner; `STATISTICAL_ANALYSIS_PLAN.md`; `SENSITIVITY_ANALYSIS_SPEC.md` | Faisal | IMPLEMENTED, TESTED; **EXECUTED: no** |
| 13 | Integration and reproducibility | F12, F13 | `configs/interface_contracts.yaml`; `04_validation/` | Faisal | IMPLEMENTED, TESTED |
| 14 | Reporting and claims | A5, A7, A13 | `RESULTS_REPORTING_TEMPLATE.md`, `SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md` | Ahmed | SPECIFIED (templates only) |

Full component traceability: `METHOD_IMPLEMENTATION_TRACEABILITY.md`.
