# Ahmed: Sign-off Sheet (Phase 5)

18 decisions (9 P0). Joint decisions also appear on the co-owners' sheets and need every owner's signature. Recommendations are not decisions; fill the fields yourself. Full context: `TEAM_DECISION_BRIEF.md`, `DECISION_REVIEW_P5.csv`.

## A-D04 [P0 · SCIENTIFIC_CHOICE] (Ahmed+Faisal)

- **Decision:** Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run
- **Recommended:** Effect sizes only, unless a justified threshold is approved BEFORE any outer-test run
- **Evidence:** assets (Faisal New Plan 2)
- **Implications / main risk:** Post-hoc significance threshold
- **Triggers / unblocks:** F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D05 [P0 · SCIENTIFIC_CHOICE] (Ahmed)

- **Decision:** Final class definitions (joint with Y-D05d, Y-D06a, F-D05)
- **Recommended:** Adopt candidate class definitions (with Y-D05d, Y-D06a, F-D05)
- **Evidence:** 06_audit_preparation/pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml
- **Implications / main risk:** Class construct validity
- **Triggers / unblocks:** Y-D07, F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D10 [P0 · SCIENTIFIC_CHOICE] (Ahmed)

- **Decision:** Re-record Gates 1-3 in GATE_DECISIONS.md and adopt plan status vocabulary in MASTER_TASK_REGISTER.csv
- **Recommended:** Re-record Gates 1-3 after Y/F decisions
- **Evidence:** 00_governance/GATE_DECISIONS.md
- **Implications / main risk:** Experiments under unsupported PASS records
- **Triggers / unblocks:** Experimental authorization
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D05 [P0 · SCIENTIFIC_CHOICE] (Faisal+Yazan+Ahmed)

- **Decision:** Pre-/post-event rows of fault runs: exclude, or label NORMAL?
- **Recommended:** exclude primary; label_normal as pre-registered secondary (raises NORMAL runs 3 -> 45 but all early-time windows: phase confound)
- **Evidence:** 06_audit_preparation/phase4_approvals/evidence/WINDOW_OPTION_COMPARISON.csv
- **Implications / main risk:** Exclude: NORMAL = 3 runs; label_normal: NORMAL confounded with time-in-run
- **Triggers / unblocks:** F-D04, F-D07, A-D01
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D07 [P0 · SCIENTIFIC_CHOICE] (Faisal+Ahmed)

- **Decision:** Thin-class policy: what may be inferred per class
- **Recommended:** Pooled primary metrics; per-family tables; NORMAL/FAULT/DELAY DESCRIPTIVE_ONLY
- **Evidence:** 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **Implications / main risk:** Class-level claims from 1 test run per fold
- **Triggers / unblocks:** F-D13, A-D01, A-D03
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D11 [P0 · SCIENTIFIC_CHOICE] (Faisal+Ahmed)

- **Decision:** Policy parameters: candidate source, singleton handling, max set size, blocking flags
- **Recommended:** p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC. Consistent with RQ2 (informative pairs, explicit abstention); max_set_size=3 is the alternative if Ahmed wants broader sets
- **Evidence:** 02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md
- **Implications / main risk:** Policy too strict -> few SPECIFIC outcomes; too loose -> uninformative sets
- **Triggers / unblocks:** F-D12, A-D02
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D17 [P0 · SCIENTIFIC_CHOICE] (Faisal+Ahmed)

- **Decision:** Freeze configs/frozen_evaluation_config.yaml from the candidate spec once all F/Y decisions are recorded
- **Recommended:** Freeze only when no PENDING placeholder remains (29 open)
- **Evidence:** 06_audit_preparation/phase4_approvals/CANDIDATE_EVALUATION_FREEZE_SPEC.md
- **Implications / main risk:** Premature freeze
- **Triggers / unblocks:** A-D10, experimental authorization
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D05d [P0 · SCIENTIFIC_CHOICE] (Yazan+Ahmed)

- **Decision:** Multi-location single-type leaks (15 runs): LEAK, or exclude all?
- **Recommended:** Multi-location single-type leaks = LEAK (consistent rule); alternative excludes 15 runs
- **Evidence:** 06_audit_preparation/pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml
- **Implications / main risk:** Construct validity of LEAK class
- **Triggers / unblocks:** Class counts, folds, A-D05
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D06a [P0 · UNRESOLVED] (Yazan+Faisal+Ahmed)

- **Decision:** CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY?
- **Recommended:** Exclude post-delay rows (no relabelling). Why labels end at 1000 s: INSUFFICIENT_EVIDENCE
- **Evidence:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L3); 06_audit_preparation/phase4_approvals/evidence/EVENT_DURATIONS.csv
- **Implications / main risk:** Relabelling would invent ground truth; counting as NORMAL adds phase-confounded windows
- **Triggers / unblocks:** F-D05, F-D04, window table
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D01 [P1 · SCIENTIFIC_CHOICE] (Ahmed)

- **Decision:** RQ1 feasibility: D(x) incremental value beyond C/M/H at matched coverage
- **Recommended:** RQ1 TESTABLE_WITH_RESTRICTIONS (pooled, family-paired, LEAK-dominated)
- **Evidence:** 06_audit_preparation/phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md
- **Implications / main risk:** Over-reading a pooled effect as class-general
- **Triggers / unblocks:** A-D08, manuscript
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D02 [P1 · SCIENTIFIC_CHOICE] (Ahmed)

- **Decision:** RQ2 feasibility: reproducible SPECIFIC / AMBIGUITY_SET / UNRESOLVED outcomes
- **Recommended:** RQ2 TESTABLE_WITH_RESTRICTIONS; 'meaningful' ambiguity EXPLORATORY unless criterion fixed in advance
- **Evidence:** 02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md
- **Implications / main risk:** Post-hoc meaning attached to ambiguity sets
- **Triggers / unblocks:** F-D11, manuscript
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D03 [P1 · SCIENTIFIC_CHOICE] (Ahmed)

- **Decision:** Scope of generalisation: held-out withdrawal topology of one simulated network
- **Recommended:** Scope = unseen withdrawal topology of the H2-SimNet simulated network; no industrial/field claim
- **Evidence:** 06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md
- **Implications / main risk:** Overgeneralisation
- **Triggers / unblocks:** A-D08
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D07 [P1 · TECHNICAL_RECOMMENDATION] (Ahmed)

- **Decision:** Mathematical consistency sign-off (p, q, D, C, M, H, coverage, risk, sets, thresholds vs code)
- **Recommended:** Sign off; document tie-inclusive neighbourhood and natural-log entropy
- **Evidence:** 06_audit_preparation/phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md
- **Implications / main risk:** Undocumented deviations
- **Triggers / unblocks:** A8
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D13 [P1 · SCIENTIFIC_CHOICE] (Faisal+Ahmed)

- **Decision:** Metric weighting and uncertainty: pooled, family-level, family-balanced; bootstrap unit
- **Recommended:** Phase-5 refinement: paired family bootstrap STRATIFIED WITHIN TOPOLOGY on pooled C vs C-D difference; per-fold estimates reported; no class-level or topology-level intervals. Families nest in only 3 topologies, so intervals are conditional on these topologies
- **Evidence:** 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **Implications / main risk:** Unstratified bootstrap over 39 families ignores topology clustering and model-per-fold structure
- **Triggers / unblocks:** A-D03, A-D04, F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D06 [P2 · TECHNICAL_RECOMMENDATION] (Ahmed)

- **Decision:** Dataset description corrections: files vs runs, clean vs noise-added, 1 s verified for Parquet, H2 fraction UNVERIFIED, exclusions
- **Recommended:** Adopt corrected dataset description (57 runs, realizations, 1 s verified, H2 fraction unverified)
- **Evidence:** 06_audit_preparation/RAW_DATASET_VERIFICATION_REPORT.md
- **Implications / main risk:** Inaccurate dataset section
- **Triggers / unblocks:** A11
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D08 [P2 · TECHNICAL_RECOMMENDATION] (Ahmed)

- **Decision:** Adopt the claim and limitation register
- **Recommended:** Adopt claim register
- **Evidence:** 06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md
- **Implications / main risk:** Overclaiming
- **Triggers / unblocks:** A8, A11
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D09 [P3 · TECHNICAL_RECOMMENDATION] (Ahmed)

- **Decision:** Documentation reconciliation: README sections 2/6/7, FIGURE_SPECIFICATION.md, fate of quarantined illustrative figures
- **Recommended:** Rewrite README 2/6/7 and FIGURE_SPECIFICATION; keep quarantine until then
- **Evidence:** 06_audit_preparation/SCIENTIFIC_AND_TECHNICAL_ISSUES.md
- **Implications / main risk:** Public docs still show fabricated figures and 'zero leakage'
- **Triggers / unblocks:** None (documentation)
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## A-D11 [P3 · VERIFIED_FACT] (Ahmed)

- **Decision:** Add the authoritative New Plan 2 PDFs to assets/
- **Recommended:** Add Plan 2 PDFs to assets/
- **Evidence:** assets/
- **Implications / main risk:** Traceability gap
- **Triggers / unblocks:** None
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

