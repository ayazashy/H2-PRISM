# H₂-PRISM Team Decision Brief (Phase 5). All decisions PENDING_HUMAN_APPROVAL

Sources: `phase4_approvals/MASTER_DECISION_MATRIX.csv` (44 decisions), evidence in `phase4_approvals/evidence/` and `pre_experiment_review/`. The Phase-5 layer is in `DECISION_REVIEW_P5.csv` and `CRITICAL_PATH_DECISIONS.md`. Sign-off sheets: `YAZAN_SIGNOFF.md`, `FAISAL_SIGNOFF.md`, `AHMED_SIGNOFF.md`.

## 1. Current state

- Branch `audit/preparation-integration` at `df4c539`, local only.
- Candidate data package: hash-pinned, and 17/17 pinned hashes reproduce on a fresh Windows checkout.
- Candidate folds are leakage-free.
- Last full validation: 158 passed, 2 skipped.
- Nothing is approved or frozen. No experiment has been run.

**Populations (do not mix them):**

| Population | Count |
| --- | --- |
| Tabular files | 242 |
| Simulated runs | 57 (each run exists as a clean simulation and a noise-added release; plus 3 `_noisy` variants, 3 solver exports and 1 misfiled copy) |
| Eligible runs | 51 = 57 − 3 compound − 3 annotation-conflict |
| Eligible runs per class | NORMAL 3, LEAK 39, COMPRESSOR_FAULT 6, COMPRESSOR_DELAY 3 |
| Families among eligible runs | primary 39 / extended 32 / conservative 3 (45 / 35 / 3 over all 57 runs) |

## 2. Critical blockers (P0, 22)

- **Data definition:** Y-D01, Y-D05b, Y-D05d, Y-D06a, Y-D07, Y-D08, A-D05.
- **Design:** F-D01–F-D08, F-D11, F-D12.
- **Implementation:** F-D10 (correctness meta-model), F-D15 (code acceptance).
- **Freeze and governance:** F-D17, A-D04, A-D10.

**Phase-5 re-assessment:** the family-map choices (Y-D03, Y-D04) are **not** P0. Under LOTO outer and LOTO-within-train inner splits every family nests inside one topology, so the choice changes no split. It changes only the uncertainty unit (F-D13).

## 3. Recommended dataset decisions (Yazan)

- **Accept the identity model** (Y-D01) and **the realization relationships** (Y-D02, numerically verified).
- **19 relationships (Y-D03):**
  - keep the 11 pairs that share only a 25 s start-up separate in the primary map;
  - group the 8 near-identical pre-event pairs in the extended/sensitivity map.
  - Whether these pairs share simulation ancestry is **INSUFFICIENT_EVIDENCE**; settling it needs the `.slx` models.
- **Family view (Y-D04):** primary map with the extended map as a registered sensitivity.
- **Labels:**
  - G5G6 location mismatch (Y-D05a): keep the raw labels and prohibit location analysis.
  - `brokenC1G5_weak` (Y-D05b): exclude.
  - Compound runs (Y-D05c): exclude.
  - Multi-location single-type leaks (Y-D05d): count as LEAK.
  - Post-delay rows (Y-D06a): exclude; why the label ends at 1000 s is **INSUFFICIENT_EVIDENCE**.
  - Phase (Y-D06b): use the verified onset, not folder names.
- **Then** issue manifest v0.2 (Y-D07) and re-issue readiness as **READY_WITH_EXCLUSIONS (restricted)** (Y-D08).

## 4. Recommended experimental settings (Faisal), with restrictions

| Item | Recommendation | Restriction or caveat |
| --- | --- | --- |
| Realization (F-D01) | noise-added primary, clean as a pre-registered secondary | The evidence does not show one is "better". The rationale is realism as described by the publisher. Never pool them |
| Outer split (F-D02) | leave-one-topology-out | Estimand = an unseen withdrawal topology of one simulated network; only 3 folds |
| Inner split (F-D03) | LOTO within the training set | 1 NORMAL run and 1 DELAY run per inner training set, so development choices for thin classes rest on single runs |
| Windows (F-D04) | 60 s / 30 s, with 60 / 60 as sensitivity | No physical derivation of 60 s; it is a compromise between sampling and DELAY support (31 windows per run) |
| Pre/post-event rows (F-D05) | exclude; `label_normal` as secondary | `label_normal` would make NORMAL depend on time in run |
| Features (F-D06) | all 128; the 80 offset-invariant features as sensitivity | possible fingerprinting through absolute levels |
| Thin classes (F-D07) | pooled primary metrics; NORMAL, FAULT, DELAY descriptive only | — |
| D(x) (F-D08) | k = 25, uniform, no prior correction; k = 10 / 50 as sensitivity | DELAY reference = 62 windows from 2 runs, so its D values carry low-diversity flags |
| Calibration (F-D09) | none vs sigmoid, chosen by log loss | isotonic not recommended |
| Policy (F-D11) | p-only candidates; a singleton becomes UNRESOLVED; maximum set size 2 | consistent with RQ2's informative sets and explicit abstention; a maximum of 3 is the alternative |
| Thresholds (F-D12) | development data only; coverage 0.80 primary, 0.60 / 0.90 secondary | **prespecified in the Faisal plan (F10 step 85)**, not chosen from results; report the realized coverage |
| Uncertainty (F-D13) | paired family bootstrap **stratified within topology**, pooled only, plus per-fold estimates | refines Phase 4: intervals are conditional on the 3 topologies; no class-level intervals |
| Implementation (F-D10) | correctness meta-model | still missing; can start now |

## 5. Scientific restrictions (Ahmed)

- **RQ1 and RQ2** are TESTABLE_WITH_RESTRICTIONS. RQ1 is pooled and LEAK-dominated. Whether RQ2's ambiguity sets are "meaningful" is EXPLORATORY unless a criterion is fixed beforehand.
- **Prohibited claims:** industrial deployment readiness, field validation, physical identifiability, metric leak localisation, pure-hydrogen behaviour, a verified 10% H₂ blend, and superiority of D(x).
- **Statistical reporting:**
  - pooled comparisons and family-level tables are supported;
  - class-level inference is not supported for NORMAL, FAULT and DELAY;
  - confidence intervals only from the stratified family bootstrap, stated as conditional on 3 topologies;
  - no topology-level generalisation interval.
- **Practical significance (A-D04):** report effect sizes only, unless a threshold is approved before any outer-test run.
- **Documentation (A-D09):**
  - README §2: remove the "23 passing tests" claim.
  - README §6: describe figures 3–6 and the dashboard as quarantined illustrations.
  - README §7: remove "zero leakage" and the 3-fold claim, or point them at the candidate folds.
  - `05_documentation/FIGURE_SPECIFICATION.md`: same correction.
  - Methodology: add the tie-inclusive neighbourhood and natural-log entropy (A-D07).
  - Adopt the claim register (A-D08) and re-record gates (A-D10).

## 6. Decisions needing more evidence

| ID | What is missing | Interim recommendation |
| --- | --- | --- |
| Y-D03 | simulation ancestry of the 19 pairs | sensitivity view; unaffected by LOTO |
| Y-D05a | true leak location of the G5G6 files | no location analysis |
| Y-D05b | correct annotation of `brokenC1G5_weak` | exclude |
| Y-D06a | why the delay label ends at 1000 s | exclude post-delay rows |

## 7. Parallel tasks (no upstream dependency)

- **Yazan:** Y-D01, Y-D02, Y-D05a–c, Y-D09, Y-D10.
- **Faisal:** F-D01, F-D02, F-D11, F-D14, F-D15, F-D16, F-D18, and **implementing F-D10**.
- **Ahmed:** A-D01–A-D04, A-D06–A-D09, A-D11.

## 8. Required approval sequence

1. Y-D01, then Y-D05b/d with A-D05, then Y-D06a.
2. F-D05.
3. F-D01 and F-D04, then F-D06.
4. F-D02, then F-D03, then F-D08 / F-D09 / F-D11.
5. F-D12.
6. Y-D07 (manifest v0.2) and Y-D08.
7. F-D13 (needs Y-D04) and A-D04.
8. F-D17 (frozen config, no PENDING left).
9. A-D10 (gates).
10. Explicit user authorisation.

## 9. Exact requirements for the next phase

1. All 22 P0 decisions signed on the sheets, with hashes and versions recorded.
2. Manifest v0.2 and `configs/frozen_evaluation_config.yaml` issued with recorded SHA-256.
3. Implementation done and tested:
   - F-D10 meta-model;
   - manifest-driven window and feature table builder;
   - F-D13 stratified bootstrap.
4. Gates 1–3 re-recorded.
5. The user's explicit authorisation for development-only runs, then for the outer-test evaluation.
