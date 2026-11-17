# Phase 4 Final Readiness Report

**Technical readiness ≠ scientific approval.** No decision in this package is approved.

| Question | Answer | Evidence |
| --- | --- | --- |
| 1. Are the data correction candidates technically validated? | **Yes**, as candidates: deterministic, hash-pinned, 33/33 schema checks, every relationship explained | `VALIDATION_AND_REGRESSION_REPORT.md` |
| 2. Are the grouped folds leakage-safe? | **Yes** (candidate LOTO): 0 issues under 3 family views; no byte-identical file across a split; inner splits independent. The original `folds.csv` is **not** | tests; `pre_experiment_review/` |
| 3. Is the final dataset scientifically approved? | **No.** Y-D01…Y-D10 are pending (Yazan); A-D05 pending (Ahmed) | `TEAM_SIGNOFF_CHECKLIST.md` |
| 4. Is the experimental design approved? | **No.** F-D01…F-D18 are pending (Faisal) | same |
| 5. Is the research framing aligned with the evidence? | **Partially.** The RQs are testable with restrictions. README and governance documents still contain unsupported claims (A-D09, A-D10) | `AHMED_SCIENTIFIC_REVIEW_DOSSIER.md`, claim register |
| 6. Are all required freezes ready? | **Prepared, not issued.** The dataset freeze spec is fully hash-pinned. The evaluation spec contains 29 explicit `PENDING_*` placeholders | the two freeze specs |
| 7. Can the team authorise primary experiments now? | **No** | — |
| 8. What is missing? | see below | `APPROVAL_DEPENDENCY_GRAPH.md` |

## Missing before any primary experiment

1. **Human decisions:**
   - Yazan: Y-D03, Y-D04, Y-D05a–d, Y-D06a/b, Y-D07, Y-D08.
   - Faisal: F-D01–F-D09, F-D11–F-D13, F-D15–F-D17.
   - Ahmed: A-D01–A-D05, A-D07, A-D10.
2. **Implementation:**
   - correctness meta-model (F-D10);
   - manifest-driven window and feature table builder;
   - F11 family bootstrap.
3. **Freeze issue:** manifest v0.2 and `configs/frozen_evaluation_config.yaml`, both hash-recorded.
4. **Explicit user authorisation** for the experimental phase.

## Decision counts

- 44 decisions in total. Yazan 15, Faisal 20, Ahmed 18, User 1; joint decisions are counted for each owner.
- By evidence class: 4 VERIFIED_FACT, 19 TECHNICAL_RECOMMENDATION, 18 SCIENTIFIC_CHOICE, **3 UNRESOLVED** for lack of evidence:
  - Y-D03: the 19 short-history links;
  - Y-D05a: leakG5G6 location;
  - Y-D05b: brokenC1G5 annotation.
