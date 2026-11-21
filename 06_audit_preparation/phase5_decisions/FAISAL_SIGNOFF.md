# Faisal: Sign-off Sheet (Phase 5)

20 decisions (15 P0). Joint decisions also appear on the co-owners' sheets and need every owner's signature. Recommendations are not decisions; fill the fields yourself. Full context: `TEAM_DECISION_BRIEF.md`, `DECISION_REVIEW_P5.csv`.

## A-D04 [P0 · SCIENTIFIC_CHOICE] (Ahmed+Faisal)

- **Decision:** Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run
- **Recommended:** Effect sizes only, unless a justified threshold is approved BEFORE any outer-test run
- **Evidence:** assets (Faisal New Plan 2)
- **Implications / main risk:** Post-hoc significance threshold
- **Triggers / unblocks:** F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D01 [P0 · SCIENTIFIC_CHOICE] (Faisal)

- **Decision:** Modelling realization: clean, noise-added, or one predefined primary with the other as controlled secondary robustness
- **Recommended:** Noise-added primary + clean pre-registered secondary. Evidence does not prove one realization 'better'; rationale is realism stated by the publisher. Never pool
- **Evidence:** 06_audit_preparation/pre_experiment_review/DATASET_RECONCILIATION_REPORT.md
- **Implications / main risk:** Choosing after seeing results; pooling duplicates runs
- **Triggers / unblocks:** F-D04, window table, F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D02 [P0 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Adopt leave-one-topology-out (3 outer folds) as the primary outer design
- **Recommended:** LOTO (only design with every class in every train/test fold and no cross-split dependence)
- **Evidence:** 06_audit_preparation/pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv; 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **Implications / main risk:** Estimand is narrow: unseen withdrawal topology of one simulated network; n=3 folds
- **Triggers / unblocks:** F-D03, F-D13, A-D03
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D03 [P0 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Inner development scheme for selection, calibration, D reference checks and threshold development
- **Recommended:** LOTO_within_train (the family-k3 scheme lacks thin classes in some validation splits). Restriction: each inner train has 1 NORMAL and 1 DELAY run, so per-class development estimates rest on single runs
- **Evidence:** 06_audit_preparation/phase4_approvals/evidence/INNER_FOLD_SUFFICIENCY.csv
- **Implications / main risk:** Development selection driven by one run per thin class
- **Triggers / unblocks:** F-D08, F-D09, F-D12
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D04 [P0 · SCIENTIFIC_CHOICE] (Faisal)

- **Decision:** Window length / stride
- **Recommended:** 60/30 primary, 60/60 non-overlapping sensitivity (DELAY keeps 31 windows/run; boundary loss <0.3%). No physical derivation of 60 s exists; it is a sampling/support compromise
- **Evidence:** 06_audit_preparation/phase4_approvals/evidence/WINDOW_OPTION_COMPARISON.csv
- **Implications / main risk:** Window length interacts with event dynamics; overlap inflates apparent n (not used for inference)
- **Triggers / unblocks:** F-D06, window table
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

## F-D06 [P0 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Candidate feature contract: 16 verified channels x {mean,std,min,max,range,last_minus_first,slope,mean_abs_diff}; no cross-channel features; offset-invariant subset as A15 arm
- **Recommended:** 128 features primary; 80 offset-invariant as A15 sensitivity; no cross-channel features
- **Evidence:** 02_methodology/FEATURE_DEFINITION_REGISTER.csv
- **Implications / main risk:** Absolute levels may fingerprint topology/run
- **Triggers / unblocks:** Window table, F-D08
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

## F-D08 [P0 · SCIENTIFIC_CHOICE] (Faisal)

- **Decision:** D(x) settings: k, weighting, prior correction, scenario balancing, flag thresholds
- **Recommended:** k=25 uniform, no prior correction primary; k=10/50 and prior correction as sensitivity. Restriction: outer-train DELAY reference = 62 windows from 2 runs, so DELAY neighbourhoods will carry LOW_SCENARIO_DIVERSITY; D for thin classes interpreted descriptively
- **Evidence:** 06_audit_preparation/phase4_approvals/evidence/OUTER_TRAIN_REFERENCE_SUPPORT.csv; 02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md
- **Implications / main risk:** D dominated by one run for thin classes
- **Triggers / unblocks:** F-D11, F-D12, RQ1
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D10 [P0 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Comparators and combined scores: C, M, -H, D; s_C = LR[logit C, M, -H, D], s_C-D = LR[logit C, M, -H] cross-fitted on development
- **Recommended:** Implement cross-fitted s_C / s_C-D meta-model (plan definition; implementation may proceed now)
- **Evidence:** src/h2prism/comparators.py
- **Implications / main risk:** Without it RQ1 (C vs C-D) cannot be run
- **Triggers / unblocks:** F-D12, F-D17, RQ1
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

## F-D12 [P0 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Threshold development: thresholds chosen on inner OOF predictions only, frozen before outer test
- **Recommended:** Development-only thresholds; target coverage 0.80 primary, 0.60/0.90 secondary - prespecified in the Faisal plan (F10 step 85), not chosen from results; report realized coverage
- **Evidence:** src/h2prism/policy.py
- **Implications / main risk:** Threshold transfer may not reach 0.80 on held-out topology
- **Triggers / unblocks:** F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D15 [P0 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Technical acceptance of new code: io (Timestamp index), windows, features, splits, baseline, calibration, distinguishability, policy, metrics, dataset_manifest
- **Recommended:** Code review then technical acceptance of new modules
- **Evidence:** 06_audit_preparation/phase4_approvals/VALIDATION_AND_REGRESSION_REPORT.md
- **Implications / main risk:** Unreviewed code in primary pipeline
- **Triggers / unblocks:** All execution
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

## Y-D06a [P0 · UNRESOLVED] (Yazan+Faisal+Ahmed)

- **Decision:** CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY?
- **Recommended:** Exclude post-delay rows (no relabelling). Why labels end at 1000 s: INSUFFICIENT_EVIDENCE
- **Evidence:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L3); 06_audit_preparation/phase4_approvals/evidence/EVENT_DURATIONS.csv
- **Implications / main risk:** Relabelling would invent ground truth; counting as NORMAL adds phase-confounded windows
- **Triggers / unblocks:** F-D05, F-D04, window table
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D09 [P1 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Calibration candidates and selection criterion
- **Recommended:** Log-loss criterion over {none, sigmoid}; isotonic NOT recommended (one run per thin class in inner folds)
- **Evidence:** src/h2prism/calibration.py
- **Implications / main risk:** Isotonic overfits single-run classes
- **Triggers / unblocks:** F-D12
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

## F-D14 [P1 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Accept the plan RF grid (n_estimators {300,500} x min_samples_leaf {1,5} x max_features {sqrt,0.3}), class_weight balanced_subsample, fixed seed
- **Recommended:** Accept plan RF grid, seed 20261104
- **Evidence:** src/h2prism/baseline.py
- **Implications / main risk:** None material
- **Triggers / unblocks:** F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D16 [P1 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Amend configs/interface_contracts.yaml (manifest, window, prediction schema additions)
- **Recommended:** Amend interface contracts; open change-control log
- **Evidence:** 06_audit_preparation/MODEL_AND_EXPERIMENT_READINESS.md
- **Implications / main risk:** Schema drift
- **Triggers / unblocks:** F-D17
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## F-D18 [P1 · TECHNICAL_RECOMMENDATION] (Faisal)

- **Decision:** Technical acceptance of Ahmed's A12-A16 modules (integration gate)
- **Recommended:** Review A12-A16 after F3/F4 exist
- **Evidence:** 02_methodology/SUPPORTING_MODEL_SPECS_A14_A16.md
- **Implications / main risk:** Supporting runs integrated without acceptance
- **Triggers / unblocks:** A14-A16 execution
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

