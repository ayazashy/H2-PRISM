# Master Decision Matrix (generated from build_decision_matrix.py; do not edit by hand)

Every approval field is `PENDING_HUMAN_APPROVAL`. A recommendation is **not** a decision.

Decisions: **44**. By owner: Ahmed: 10, Ahmed+Faisal: 1, Faisal: 13, Faisal+Ahmed: 4, Faisal+Yazan+Ahmed: 1, User: 1, Yazan: 12, Yazan+Ahmed: 1, Yazan+Faisal+Ahmed: 1

By evidence class: VERIFIED_FACT: 4, TECHNICAL_RECOMMENDATION: 19, SCIENTIFIC_CHOICE: 18, UNRESOLVED: 3

| ID | Owner | Class | Question | Recommended | May proceed without approval |
| --- | --- | --- | --- | --- | --- |
| Y-D01 | Yazan | TECHNICAL_RECOMMENDATION | Accept the canonical identity model: 242 tabular files = 57 simulated runs (114 clean, 114 noise-added, 6 _noisy variant, 6 solver-export, 2 misfiled files)? | accept | YES (candidate only) |
| Y-D02 | Yazan | VERIFIED_FACT | Confirm that clean, noise-added, _noisy and solver-export files are realizations of the same run and never independent evidence | confirm | YES |
| Y-D03 | Yazan | UNRESOLVED | Resolve the 19 short shared-history relationships individually (11 identical-until-25 s start-up pairs; 8 near-identical pre-event trajectories) | 8 near-identical leak pairs: treat as dependent for inner splits; 11 start-up pairs: keep separate in primary, merge in sensitivity | NO (scientific) |
| Y-D04 | Yazan | SCIENTIFIC_CHOICE | Which family map is the dataset definition: primary (45 families /39 eligible), extended (35/32) or conservative topology-level (3)? | primary + extended registered as sensitivity (conservative used only as an upper-bound check) | NO (scientific) |
| Y-D05a | Yazan | UNRESOLVED | leakG5G6_overlapped files: filename/ReadME say G5+G6, row labels say leak_G4+leak_G6. Which is authoritative? | keep raw labels; record mismatch; contact authors before any location analysis | YES (class unaffected) |
| Y-D05b | Yazan | UNRESOLVED | brokenC1G5_weak: leak_G5 active on 13,000 rows while Leak=0. Compound event or annotation error? | exclude from exclusive 4-class task under both readings (current candidate) | NO for any re-inclusion |
| Y-D05c | Yazan | VERIFIED_FACT | Confirm exclusion of leakG4brokenC1 (Leak and CompressorFault simultaneously active) from the exclusive task | exclude; keep for exploratory multi-label | YES |
| Y-D05d | Yazan+Ahmed | SCIENTIFIC_CHOICE | Multi-location single-type leaks (15 runs): LEAK, or exclude all? | LEAK | NO |
| Y-D06a | Yazan+Faisal+Ahmed | SCIENTIFIC_CHOICE | CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY? | exclude (do not relabel, do not count as normal) | NO |
| Y-D06b | Yazan | TECHNICAL_RECOMMENDATION | Replace folder-derived phase with verified onset time plus documented ReadME phase; folder kept as segment_dir | accept | YES |
| Y-D07 | Yazan | TECHNICAL_RECOMMENDATION | Issue candidate manifest v0.2 (replacing v0.1 for use; v0.1 kept traceable) | issue after Y-D01..Y-D06 | NO |
| Y-D08 | Yazan | SCIENTIFIC_CHOICE | Re-issue the dataset readiness decision (current READY_WITH_EXCLUSIONS is unsupported) | READY_WITH_EXCLUSIONS for a pooled LOTO evaluation, with NORMAL/FAULT/DELAY marked descriptive-only | NO |
| Y-D09 | Yazan | TECHNICAL_RECOMMENDATION | Fix portability/determinism of audit/ scripts or adopt src/h2prism/dataset_manifest.py as the reference builder | adopt module; leave audit/ as historical | YES |
| Y-D10 | Yazan | VERIFIED_FACT | Correct raw_checksums.sha256 provenance (8 files hashed after CRLF->LF; .gitkeep not in archive; 264 not 265 files) | regenerate | YES |
| F-D01 | Faisal | SCIENTIFIC_CHOICE | Modelling realization: clean, noise-added, or one predefined primary with the other as controlled secondary robustness | C (noise-added primary; clean as a pre-registered secondary) | NO (scientific) |
| F-D02 | Faisal | TECHNICAL_RECOMMENDATION | Adopt leave-one-topology-out (3 outer folds) as the primary outer design | LOTO | NO |
| F-D03 | Faisal | TECHNICAL_RECOMMENDATION | Inner development scheme for selection, calibration, D reference checks and threshold development | LOTO_within_train | NO |
| F-D04 | Faisal | SCIENTIFIC_CHOICE | Window length / stride | 60/30 as primary candidate; 60/60 (non-overlapping) as dependence sensitivity | NO |
| F-D05 | Faisal+Yazan+Ahmed | SCIENTIFIC_CHOICE | Pre-/post-event rows of fault runs: exclude, or label NORMAL? | exclude for primary; label_normal as pre-registered secondary | NO |
| F-D06 | Faisal | TECHNICAL_RECOMMENDATION | Candidate feature contract: 16 verified channels x {mean,std,min,max,range,last_minus_first,slope,mean_abs_diff}; no cross-channel features; offset-invariant subset as A15 arm | full 128 primary; offset-invariant as sensitivity (A15) | NO |
| F-D07 | Faisal+Ahmed | SCIENTIFIC_CHOICE | Thin-class policy: what may be inferred per class | pooled primary metrics with per-family tables; per-class results DESCRIPTIVE_ONLY for NORMAL/FAULT/DELAY | NO |
| F-D08 | Faisal | SCIENTIFIC_CHOICE | D(x) settings: k, weighting, prior correction, scenario balancing, flag thresholds | pre-register k=25 uniform without prior correction as primary; flags min_distinct_scenarios=2; prior correction and k=10/50 as sensitivity | NO |
| F-D09 | Faisal | TECHNICAL_RECOMMENDATION | Calibration candidates and selection criterion | log-loss criterion over {none, sigmoid, isotonic} on inner OOF (LOTO_within_train) | NO |
| F-D10 | Faisal | TECHNICAL_RECOMMENDATION | Comparators and combined scores: C, M, -H, D; s_C = LR[logit C, M, -H, D], s_C-D = LR[logit C, M, -H] cross-fitted on development | as plan | YES (implementation of plan definition) |
| F-D11 | Faisal+Ahmed | SCIENTIFIC_CHOICE | Policy parameters: candidate source, singleton handling, max set size, blocking flags | p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC | NO |
| F-D12 | Faisal | TECHNICAL_RECOMMENDATION | Threshold development: thresholds chosen on inner OOF predictions only, frozen before outer test | target coverage 0.80 on development OOF; 0.60/0.90 secondary (plan F10) | NO |
| F-D13 | Faisal+Ahmed | SCIENTIFIC_CHOICE | Metric weighting and uncertainty: pooled, family-level, family-balanced; bootstrap unit | paired family bootstrap on primary map, extended map as sensitivity; report per-family tables; no topology-level inference | NO |
| F-D14 | Faisal | TECHNICAL_RECOMMENDATION | Accept the plan RF grid (n_estimators {300,500} x min_samples_leaf {1,5} x max_features {sqrt,0.3}), class_weight balanced_subsample, fixed seed | accept; seed 20261104 | YES |
| F-D15 | Faisal | TECHNICAL_RECOMMENDATION | Technical acceptance of new code: io (Timestamp index), windows, features, splits, baseline, calibration, distinguishability, policy, metrics, dataset_manifest | review then accept | NO |
| F-D16 | Faisal | TECHNICAL_RECOMMENDATION | Amend configs/interface_contracts.yaml (manifest, window, prediction schema additions) | accept | NO |
| F-D17 | Faisal+Ahmed | SCIENTIFIC_CHOICE | Freeze configs/frozen_evaluation_config.yaml from the candidate spec once all F/Y decisions are recorded | freeze only after Y-D01..Y-D08 and F-D01..F-D16 | NO |
| F-D18 | Faisal | TECHNICAL_RECOMMENDATION | Technical acceptance of Ahmed's A12-A16 modules (integration gate) | review then accept | NO |
| A-D01 | Ahmed | SCIENTIFIC_CHOICE | RQ1 feasibility: D(x) incremental value beyond C/M/H at matched coverage | TESTABLE_WITH_RESTRICTIONS (pooled C vs C-D, family-paired; per-class descriptive) | NO |
| A-D02 | Ahmed | SCIENTIFIC_CHOICE | RQ2 feasibility: reproducible SPECIFIC / AMBIGUITY_SET / UNRESOLVED outcomes | TESTABLE_WITH_RESTRICTIONS (outcome rates and reproducibility); 'meaningful' ambiguity sets EXPLORATORY | NO |
| A-D03 | Ahmed | SCIENTIFIC_CHOICE | Scope of generalisation: held-out withdrawal topology of one simulated network | accept: 'generalisation to an unseen withdrawal topology of the H2-SimNet simulated network' | NO |
| A-D04 | Ahmed+Faisal | SCIENTIFIC_CHOICE | Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run | effect sizes only, unless both approve a justified threshold now | NO |
| A-D05 | Ahmed | SCIENTIFIC_CHOICE | Final class definitions (joint with Y-D05d, Y-D06a, F-D05) | as candidate | NO |
| A-D06 | Ahmed | TECHNICAL_RECOMMENDATION | Dataset description corrections: files vs runs, clean vs noise-added, 1 s verified for Parquet, H2 fraction UNVERIFIED, exclusions | adopt | YES (drafting) |
| A-D07 | Ahmed | TECHNICAL_RECOMMENDATION | Mathematical consistency sign-off (p, q, D, C, M, H, coverage, risk, sets, thresholds vs code) | sign off after review | NO |
| A-D08 | Ahmed | TECHNICAL_RECOMMENDATION | Adopt the claim and limitation register | adopt | NO |
| A-D09 | Ahmed | TECHNICAL_RECOMMENDATION | Documentation reconciliation: README sections 2/6/7, FIGURE_SPECIFICATION.md, fate of quarantined illustrative figures | own rewrite using the claim register; keep quarantine until README is fixed | YES (drafting) |
| A-D10 | Ahmed | SCIENTIFIC_CHOICE | Re-record Gates 1-3 in GATE_DECISIONS.md and adopt plan status vocabulary in MASTER_TASK_REGISTER.csv | re-record from Phase 2-4 evidence after Yazan/Faisal decisions | NO |
| A-D11 | Ahmed | VERIFIED_FACT | Add the authoritative New Plan 2 PDFs to assets/ | add | YES |
| G-D01 | User | TECHNICAL_RECOMMENDATION | Approve the proposed local commit plan (no push) | approve | NO |

## Details

### Y-D01 (Yazan; tasks Y1;Y2; TECHNICAL_RECOMMENDATION)
- **question:** Accept the canonical identity model: 242 tabular files = 57 simulated runs (114 clean, 114 noise-added, 6 _noisy variant, 6 solver-export, 2 misfiled files)?
- **available evidence:** Every file assigned by path or exact bytes; 0 UNRESOLVED; reconciliation table
- **evidence files:** 06_audit_preparation/pre_experiment_review/CANDIDATE_FILE_INVENTORY.csv; 06_audit_preparation/phase4_approvals/evidence/INVENTORY_RECONCILIATION.csv
- **valid options:** accept | amend realization typing | reject
- **recommended option:** accept
- **justification:** All 60 clean-vs-noise and 121 format-twin relations explained numerically; deterministic builder
- **alternatives and limitations:** Rejecting leaves Yazan's 58-scenario map with a duplicate scenario
- **statistical implications:** Prevents double counting of runs (57 not 115+)
- **leakage implications:** Removes the byte-duplicate fold-3 leak
- **reproducibility implications:** Builder is order/separator independent (13/13 identical hashes)
- **downstream effect:** All folds, families, counts
- **required validation:** Y-D07 manifest diff review
- **implementation may proceed without approval:** YES (candidate only)
- **affected artifact hash:** CANDIDATE_FILE_INVENTORY.csv@6b56c846a103
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D02 (Yazan; tasks Y1;Y2; VERIFIED_FACT)
- **question:** Confirm that clean, noise-added, _noisy and solver-export files are realizations of the same run and never independent evidence
- **available evidence:** Labels identical 60/60; residual mean<0.01; lag-1 autocorr~0; solver exports match within 0.08-0.6% of range
- **evidence files:** 06_audit_preparation/pre_experiment_review/FAMILY_RELATIONSHIP_EVIDENCE.csv
- **valid options:** confirm | dispute with evidence
- **recommended option:** confirm
- **justification:** Numerical evidence plus dataset ReadME statement on added Gaussian noise
- **alternatives and limitations:** -
- **statistical implications:** Independent n = runs, not files
- **leakage implications:** Realizations must sit on the same side of every split (enforced)
- **reproducibility implications:** Hashes of every file kept in inventory
- **downstream effect:** F-D01
- **required validation:** none beyond review
- **implementation may proceed without approval:** YES
- **affected artifact hash:** FAMILY_RELATIONSHIP_EVIDENCE.csv@47898bd681b2
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D03 (Yazan; tasks Y2; UNRESOLVED)
- **question:** Resolve the 19 short shared-history relationships individually (11 identical-until-25 s start-up pairs; 8 near-identical pre-event trajectories)
- **available evidence:** Per-pair segment lengths, classes, onsets; 13 cross-class pairs; none crosses topology
- **evidence files:** 06_audit_preparation/phase4_approvals/evidence/RELATIONSHIP_19_REVIEW.csv
- **valid options:** per pair: DEPENDENT (merge) | PLAUSIBLE (sensitivity only) | INDEPENDENT
- **recommended option:** 8 near-identical leak pairs: treat as dependent for inner splits; 11 start-up pairs: keep separate in primary, merge in sensitivity
- **justification:** A 25-row identical start is shared initial state, not evidenced ancestry (plan Y2 step 23); 387-400 identical pre-event rows of the same valve configuration suggest a common configuration
- **alternatives and limitations:** Merging all reduces LEAK families 30->26 and links FAULT with DELAY
- **statistical implications:** Affects only family-grouped inner splits and any family bootstrap
- **leakage implications:** No effect on LOTO outer folds (all within topology)
- **reproducibility implications:** Decision must be recorded per edge_id
- **downstream effect:** Y-D04, F-D03, F-D13
- **required validation:** Yazan inspection of simulation configuration if available
- **implementation may proceed without approval:** NO (scientific)
- **affected artifact hash:** RELATIONSHIP_19_REVIEW.csv
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D04 (Yazan; tasks Y2;Y5; SCIENTIFIC_CHOICE)
- **question:** Which family map is the dataset definition: primary (45 families /39 eligible), extended (35/32) or conservative topology-level (3)?
- **available evidence:** Three maps; all nest within topology; 0/1,083 cross-topology shared rows
- **evidence files:** 06_audit_preparation/pre_experiment_review/CANDIDATE_FAMILY_MAP.csv; 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **valid options:** primary | extended | conservative | primary + extended as registered sensitivity
- **recommended option:** primary + extended registered as sensitivity (conservative used only as an upper-bound check)
- **justification:** Primary merges only evidenced dependence; extended covers the unresolved 19; conservative removes all within-topology resolution
- **alternatives and limitations:** Conservative gives only 3 units: no family-level uncertainty possible
- **statistical implications:** Effective n: 39 vs 32 vs 3 units over eligible runs
- **leakage implications:** Outer LOTO is leakage-safe under all three (0 issues)
- **reproducibility implications:** Maps are deterministic outputs
- **downstream effect:** F-D03, F-D13, D(x) query-family exclusion
- **required validation:** Re-run validator after choice
- **implementation may proceed without approval:** NO (scientific)
- **affected artifact hash:** CANDIDATE_FAMILY_MAP.csv@950cef8b3217
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D05a (Yazan; tasks Y4; UNRESOLVED)
- **question:** leakG5G6_overlapped files: filename/ReadME say G5+G6, row labels say leak_G4+leak_G6. Which is authoritative?
- **available evidence:** 3 runs (+noise variants), labels identical across realizations
- **evidence files:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L1)
- **valid options:** raw labels authoritative | filename authoritative | contact dataset authors
- **recommended option:** keep raw labels; record mismatch; contact authors before any location analysis
- **justification:** Class LEAK unaffected; only localisation analyses depend on it
- **alternatives and limitations:** -
- **statistical implications:** none for 4-class task
- **leakage implications:** none
- **reproducibility implications:** must be stated in dataset description
- **downstream effect:** A-D06
- **required validation:** author confirmation (optional)
- **implementation may proceed without approval:** YES (class unaffected)
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D05b (Yazan; tasks Y4; UNRESOLVED)
- **question:** brokenC1G5_weak: leak_G5 active on 13,000 rows while Leak=0. Compound event or annotation error?
- **available evidence:** 3 runs; CompressorFault from 25 s
- **evidence files:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L2)
- **valid options:** compound (exploratory) | compressor fault with stray location label | exclude
- **recommended option:** exclude from exclusive 4-class task under both readings (current candidate)
- **justification:** Both readings make it ineligible for a mutually exclusive target
- **alternatives and limitations:** Including as FAULT would add 3 runs to a thin class on doubtful labels
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** Six runs remain excluded in total
- **required validation:** -
- **implementation may proceed without approval:** NO for any re-inclusion
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D05c (Yazan; tasks Y4; VERIFIED_FACT)
- **question:** Confirm exclusion of leakG4brokenC1 (Leak and CompressorFault simultaneously active) from the exclusive task
- **available evidence:** 19,900 rows with both types
- **evidence files:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L7)
- **valid options:** exclude | multi-label secondary only
- **recommended option:** exclude; keep for exploratory multi-label
- **justification:** Mutual exclusivity violated
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** -
- **required validation:** -
- **implementation may proceed without approval:** YES
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D05d (Yazan+Ahmed; tasks Y4;A4; SCIENTIFIC_CHOICE)
- **question:** Multi-location single-type leaks (15 runs): LEAK, or exclude all?
- **available evidence:** G3G4 weak/strong, G3G5, G3G6, G5G6(=G4G6 labels) per topology
- **evidence files:** 06_audit_preparation/pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml
- **valid options:** LEAK (consistent rule) | exclude all 15 | separate class
- **recommended option:** LEAK
- **justification:** Leak umbrella label is active and no other event type; target does not localise
- **alternatives and limitations:** Excluding leaves 24 LEAK runs; separate class has 5 runs/topology but no plan support
- **statistical implications:** LEAK remains the only class with >3 runs
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** LEAK counts, folds
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** CANDIDATE_SCENARIO_MANIFEST.csv@29b8b3cc018a
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D06a (Yazan+Faisal+Ahmed; tasks Y3;F3;A4; SCIENTIFIC_CHOICE)
- **question:** CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY?
- **available evidence:** Verified label transitions; ReadME says anomalies last to end
- **evidence files:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L3); 06_audit_preparation/phase4_approvals/evidence/EVENT_DURATIONS.csv
- **valid options:** exclude post-event rows | label NORMAL | relabel DELAY to end
- **recommended option:** exclude (do not relabel, do not count as normal)
- **justification:** No raw-label change; avoids inventing ground truth
- **alternatives and limitations:** DELAY then contributes 31 windows per run at 60/30
- **statistical implications:** DELAY support is 3 runs regardless
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** F-D04, F-D05
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D06b (Yazan; tasks Y3; TECHNICAL_RECOMMENDATION)
- **question:** Replace folder-derived phase with verified onset time plus documented ReadME phase; folder kept as segment_dir
- **available evidence:** C1 events onset 25 s in constant_segment folders; ReadME places them in ramp-up
- **evidence files:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L4-L5)
- **valid options:** accept | keep folder phase
- **recommended option:** accept
- **justification:** Folder names are not phase evidence
- **alternatives and limitations:** -
- **statistical implications:** Phase is confounded with class by design; must not be a feature
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A-D06 dataset description
- **required validation:** -
- **implementation may proceed without approval:** YES
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D07 (Yazan; tasks Y8; TECHNICAL_RECOMMENDATION)
- **question:** Issue candidate manifest v0.2 (replacing v0.1 for use; v0.1 kept traceable)
- **available evidence:** Candidate manifest and freeze spec
- **evidence files:** 06_audit_preparation/pre_experiment_review/CANDIDATE_SCENARIO_MANIFEST.csv; 06_audit_preparation/phase4_approvals/CANDIDATE_DATASET_FREEZE_SPEC.md
- **valid options:** issue v0.2 as proposed | amend then issue
- **recommended option:** issue after Y-D01..Y-D06
- **justification:** Single versioned handoff with hashes
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** Hash-pinned
- **downstream effect:** F-D02..F-D17
- **required validation:** A12 validation on v0.2
- **implementation may proceed without approval:** NO
- **affected artifact hash:** CANDIDATE_SCENARIO_MANIFEST.csv@29b8b3cc018a
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D08 (Yazan; tasks Y7; SCIENTIFIC_CHOICE)
- **question:** Re-issue the dataset readiness decision (current READY_WITH_EXCLUSIONS is unsupported)
- **available evidence:** Candidate readiness evidence
- **evidence files:** 06_audit_preparation/phase4_approvals/YAZAN_DATASET_APPROVAL_DOSSIER.md
- **valid options:** READY_WITH_EXCLUSIONS (restricted) | EXPLORATORY_ONLY | other
- **recommended option:** READY_WITH_EXCLUSIONS for a pooled LOTO evaluation, with NORMAL/FAULT/DELAY marked descriptive-only
- **justification:** Leakage resolved in candidate; class support thin
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** Gate 1-3 re-record
- **required validation:** Ahmed approval of interpretation
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D09 (Yazan; tasks Y1;Y2; TECHNICAL_RECOMMENDATION)
- **question:** Fix portability/determinism of audit/ scripts or adopt src/h2prism/dataset_manifest.py as the reference builder
- **available evidence:** OS-dependent canonical file choice (58/58 vs 3/58)
- **evidence files:** 06_audit_preparation/pre_experiment_review/CROSS_PLATFORM_REPRODUCIBILITY.md
- **valid options:** adopt module | patch audit scripts | both
- **recommended option:** adopt module; leave audit/ as historical
- **justification:** Module is tested and hash-verified
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** Deterministic
- **downstream effect:** -
- **required validation:** -
- **implementation may proceed without approval:** YES
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### Y-D10 (Yazan; tasks Y1; VERIFIED_FACT)
- **question:** Correct raw_checksums.sha256 provenance (8 files hashed after CRLF->LF; .gitkeep not in archive; 264 not 265 files)
- **available evidence:** Checksum reconciliation
- **evidence files:** 06_audit_preparation/raw_verification/CHECKSUM_RECONCILIATION.csv
- **valid options:** regenerate from untouched archive | annotate
- **recommended option:** regenerate
- **justification:** Plan: never alter raw files
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** Archive MD5 recorded
- **downstream effect:** A10 provenance
- **required validation:** -
- **implementation may proceed without approval:** YES
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D01 (Faisal; tasks F3;F4;F10; SCIENTIFIC_CHOICE)
- **question:** Modelling realization: clean, noise-added, or one predefined primary with the other as controlled secondary robustness
- **available evidence:** Both realizations exist for every run; noise is white, ~1e-4-1e-3 of range
- **evidence files:** 06_audit_preparation/pre_experiment_review/DATASET_RECONCILIATION_REPORT.md
- **valid options:** A clean-only | B noise-added-only | C primary noise-added + clean secondary | D primary clean + noise-added secondary
- **recommended option:** C (noise-added primary; clean as a pre-registered secondary)
- **justification:** Noise-added release reflects sensor uncertainty intended by the publisher; clean secondary measures sensitivity without selecting on outcomes
- **alternatives and limitations:** A overstates separability; B alone loses the noise-sensitivity check; using both as training data doubles evidence (prohibited)
- **statistical implications:** Never pool realizations as independent samples
- **leakage implications:** Both realizations of a run always on the same side
- **reproducibility implications:** Choice fixed before any run
- **downstream effect:** F-D04..F-D17
- **required validation:** -
- **implementation may proceed without approval:** NO (scientific)
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D02 (Faisal; tasks F4; TECHNICAL_RECOMMENDATION)
- **question:** Adopt leave-one-topology-out (3 outer folds) as the primary outer design
- **available evidence:** 0 validation issues under 3 family views; all classes in every train/test fold; topology carries no class information
- **evidence files:** 06_audit_preparation/pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv; 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **valid options:** LOTO | grouped K-fold over primary families mixing topologies | restricted per-class design
- **recommended option:** LOTO
- **justification:** Only design where every class is present in every train and test fold and no dependence crosses a split
- **alternatives and limitations:** Family K-fold would test within-topology generalisation but leaves test folds without NORMAL/DELAY
- **statistical implications:** 3 folds; between-fold variance = topology shift
- **leakage implications:** Verified leakage-safe
- **reproducibility implications:** Fold file hash-pinned
- **downstream effect:** F-D03, F-D13, F-D17
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** CANDIDATE_OUTER_FOLDS.csv@3b21d8231a40
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D03 (Faisal; tasks F4;F6;F7;F9; TECHNICAL_RECOMMENDATION)
- **question:** Inner development scheme for selection, calibration, D reference checks and threshold development
- **available evidence:** LOTO_within_train: 6/6 feasible, every class in every inner train and validation; family-k3: 9/9 class-in-train feasible but some validation splits lack NORMAL/FAULT/DELAY
- **evidence files:** 06_audit_preparation/phase4_approvals/evidence/INNER_FOLD_SUFFICIENCY.csv
- **valid options:** LOTO_within_train | grouped_by_family_primary_k3
- **recommended option:** LOTO_within_train
- **justification:** Only scheme supporting per-class calibration and threshold development
- **alternatives and limitations:** Each inner train holds 1 NORMAL run, 1 DELAY run (31 windows at 60/30)
- **statistical implications:** Development estimates rest on single runs for 3 classes
- **leakage implications:** Nested within outer train (tested)
- **reproducibility implications:** Deterministic
- **downstream effect:** F-D08, F-D09, F-D12
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** CANDIDATE_INNER_FOLDS.csv@ebff65da38a5
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D04 (Faisal; tasks F3; SCIENTIFIC_CHOICE)
- **question:** Window length / stride
- **available evidence:** Options compared on all 51 eligible runs (windowing only)
- **evidence files:** 06_audit_preparation/phase4_approvals/evidence/WINDOW_OPTION_COMPARISON.csv
- **valid options:** 30/15 | 60/30 | 60/60 | 120/60 | 300/150
- **recommended option:** 60/30 as primary candidate; 60/60 (non-overlapping) as dependence sensitivity
- **justification:** 1 s sampling verified; shortest event = DELAY 976 s -> 31 windows/run at 60/30 vs 6 at 300/150; boundary losses <0.3%
- **alternatives and limitations:** 30/15 doubles correlated windows without new runs; 300/150 leaves 12 DELAY windows in total
- **statistical implications:** Windows are repeated measures; overlap 50% at stride=w/2
- **leakage implications:** -
- **reproducibility implications:** Deterministic window IDs
- **downstream effect:** F-D05, F-D07
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** WINDOW_OPTION_COMPARISON.csv
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D05 (Faisal+Yazan+Ahmed; tasks F3;Y3;Y4; SCIENTIFIC_CHOICE)
- **question:** Pre-/post-event rows of fault runs: exclude, or label NORMAL?
- **available evidence:** label_normal raises NORMAL contributing runs 3 -> 45 (all early-time windows)
- **evidence files:** 06_audit_preparation/phase4_approvals/evidence/WINDOW_OPTION_COMPARISON.csv
- **valid options:** exclude | label_normal | label_normal as secondary analysis
- **recommended option:** exclude for primary; label_normal as pre-registered secondary
- **justification:** Pre-event windows are early-run (ramp-up/transient) only, so NORMAL would become phase-confounded; primary avoids that
- **alternatives and limitations:** Exclude keeps NORMAL at 3 independent runs (descriptive only)
- **statistical implications:** Changes NORMAL from 3 to 45 contributing runs
- **leakage implications:** Pre-event and event windows of one run share the family (never split)
- **reproducibility implications:** -
- **downstream effect:** F-D07, A-D01
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D06 (Faisal; tasks F3; TECHNICAL_RECOMMENDATION)
- **question:** Candidate feature contract: 16 verified channels x {mean,std,min,max,range,last_minus_first,slope,mean_abs_diff}; no cross-channel features; offset-invariant subset as A15 arm
- **available evidence:** Feature register; channel/unit audit
- **evidence files:** 02_methodology/FEATURE_DEFINITION_REGISTER.csv
- **valid options:** full 128 | offset-invariant 80 | subset
- **recommended option:** full 128 primary; offset-invariant as sensitivity (A15)
- **justification:** Absolute pressure levels can fingerprint topology/run
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** Scaling fitted on training only (enforced); IDs never features
- **reproducibility implications:** Deterministic feature hash
- **downstream effect:** F-D08, A15
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** FEATURE_DEFINITION_REGISTER.csv
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D07 (Faisal+Ahmed; tasks F4;F10;F11; SCIENTIFIC_CHOICE)
- **question:** Thin-class policy: what may be inferred per class
- **available evidence:** NORMAL 3, DELAY 3, FAULT 6 runs (3 families), LEAK 39 runs (30 families)
- **evidence files:** 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **valid options:** pooled primary + descriptive per class | per-class inference | reduce task
- **recommended option:** pooled primary metrics with per-family tables; per-class results DESCRIPTIVE_ONLY for NORMAL/FAULT/DELAY
- **justification:** 1 run per class per test fold cannot support class-specific inference
- **alternatives and limitations:** Reducing the task would need A-D05 approval
- **statistical implications:** No pseudo-replication via windows
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** F-D13, A-D03
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D08 (Faisal; tasks F7; SCIENTIFIC_CHOICE)
- **question:** D(x) settings: k, weighting, prior correction, scenario balancing, flag thresholds
- **available evidence:** Implementation tested (17 tests); outer-train reference: NORMAL 2 runs/1330 windows, DELAY 2 runs/62 windows (60/30)
- **evidence files:** 06_audit_preparation/phase4_approvals/evidence/OUTER_TRAIN_REFERENCE_SUPPORT.csv; 02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md
- **valid options:** k in {10,25,50}; uniform | inverse-distance; prior correction on/off; scenario-balanced support
- **recommended option:** pre-register k=25 uniform without prior correction as primary; flags min_distinct_scenarios=2; prior correction and k=10/50 as sensitivity
- **justification:** k=25 is the plan default; with 31 DELAY windows per run a k-neighbourhood can be dominated by one run, so LOW_SCENARIO_DIVERSITY must be reported
- **alternatives and limitations:** Larger k swamps DELAY
- **statistical implications:** D is per-window; dependence handled at family level
- **leakage implications:** Query-family exclusion and train-only reference enforced
- **reproducibility implications:** Config-pinned
- **downstream effect:** F-D10, F-D11
- **required validation:** development-only diagnostics
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D09 (Faisal; tasks F6; TECHNICAL_RECOMMENDATION)
- **question:** Calibration candidates and selection criterion
- **available evidence:** calibration.py: none/sigmoid/isotonic, grouped cross-fitted selection keeps 'none' unless strictly better
- **evidence files:** src/h2prism/calibration.py
- **valid options:** log-loss | Brier criterion; methods subset
- **recommended option:** log-loss criterion over {none, sigmoid, isotonic} on inner OOF (LOTO_within_train)
- **justification:** Plan F6; retains uncalibrated by default
- **alternatives and limitations:** Isotonic with 1 run per class in development is fragile
- **statistical implications:** -
- **leakage implications:** Never fitted on outer test (enforced)
- **reproducibility implications:** -
- **downstream effect:** F-D10
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D10 (Faisal; tasks F8;F10;A16; TECHNICAL_RECOMMENDATION)
- **question:** Comparators and combined scores: C, M, -H, D; s_C = LR[logit C, M, -H, D], s_C-D = LR[logit C, M, -H] cross-fitted on development
- **available evidence:** comparators.py tested; meta-model not implemented
- **evidence files:** src/h2prism/comparators.py
- **valid options:** as plan | rank-normalised
- **recommended option:** as plan
- **justification:** Plan F8/F10
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** Meta-model must use cross-fitted development predictions only
- **reproducibility implications:** -
- **downstream effect:** F-D12
- **required validation:** implementation + tests
- **implementation may proceed without approval:** YES (implementation of plan definition)
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D11 (Faisal+Ahmed; tasks F9; SCIENTIFIC_CHOICE)
- **question:** Policy parameters: candidate source, singleton handling, max set size, blocking flags
- **available evidence:** policy.py tested; K=4 admits max_set_size in {2,3}
- **evidence files:** 02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md
- **valid options:** p-only | p+q candidates; expand_to_two | unresolved; 2 | 3; flags
- **recommended option:** p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC
- **justification:** Conservative: weak evidence never becomes SPECIFIC or a broad set
- **alternatives and limitations:** max_set_size=3 at K=4 is near-uninformative
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** F-D12, A-D02
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D12 (Faisal; tasks F9;F10; TECHNICAL_RECOMMENDATION)
- **question:** Threshold development: thresholds chosen on inner OOF predictions only, frozen before outer test
- **available evidence:** PolicyConfig refuses non-development sources
- **evidence files:** src/h2prism/policy.py
- **valid options:** target-coverage rule (0.80 primary) | risk-target rule
- **recommended option:** target coverage 0.80 on development OOF; 0.60/0.90 secondary (plan F10)
- **justification:** Plan F10 step 85
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** Enforced in code
- **reproducibility implications:** -
- **downstream effect:** F-D17
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D13 (Faisal+Ahmed; tasks F10;F11; SCIENTIFIC_CHOICE)
- **question:** Metric weighting and uncertainty: pooled, family-level, family-balanced; bootstrap unit
- **available evidence:** 39 primary families (32 extended) among eligible runs; 3 topologies
- **evidence files:** 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **valid options:** family bootstrap (primary map) | extended map | no inference
- **recommended option:** paired family bootstrap on primary map, extended map as sensitivity; report per-family tables; no topology-level inference
- **justification:** Families are the independence unit
- **alternatives and limitations:** LEAK dominates pooled metrics
- **statistical implications:** Windows never resampled
- **leakage implications:** -
- **reproducibility implications:** Seeded
- **downstream effect:** A-D03, A-D11
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D14 (Faisal; tasks F5; TECHNICAL_RECOMMENDATION)
- **question:** Accept the plan RF grid (n_estimators {300,500} x min_samples_leaf {1,5} x max_features {sqrt,0.3}), class_weight balanced_subsample, fixed seed
- **available evidence:** baseline.rf_param_grid matches the plan (tested)
- **evidence files:** src/h2prism/baseline.py
- **valid options:** accept | amend
- **recommended option:** accept; seed 20261104
- **justification:** Plan F5
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** Selection on inner OOF only (tested)
- **reproducibility implications:** -
- **downstream effect:** F-D17
- **required validation:** -
- **implementation may proceed without approval:** YES
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D15 (Faisal; tasks F3-F9;F12; TECHNICAL_RECOMMENDATION)
- **question:** Technical acceptance of new code: io (Timestamp index), windows, features, splits, baseline, calibration, distinguishability, policy, metrics, dataset_manifest
- **available evidence:** 158 passed / 2 skipped; real-file windowing interface tests
- **evidence files:** 06_audit_preparation/phase4_approvals/VALIDATION_AND_REGRESSION_REPORT.md
- **valid options:** accept | request changes
- **recommended option:** review then accept
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** all
- **required validation:** code review
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D16 (Faisal; tasks F12; TECHNICAL_RECOMMENDATION)
- **question:** Amend configs/interface_contracts.yaml (manifest, window, prediction schema additions)
- **available evidence:** Proposed amendments
- **evidence files:** 06_audit_preparation/MODEL_AND_EXPERIMENT_READINESS.md
- **valid options:** accept | amend
- **recommended option:** accept
- **justification:** Contract currently lacks fields the plan requires
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** Change-control log entry
- **downstream effect:** A12 validation
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D17 (Faisal+Ahmed; tasks F4;A9; SCIENTIFIC_CHOICE)
- **question:** Freeze configs/frozen_evaluation_config.yaml from the candidate spec once all F/Y decisions are recorded
- **available evidence:** Candidate spec with explicit PENDING placeholders
- **evidence files:** 06_audit_preparation/phase4_approvals/CANDIDATE_EVALUATION_FREEZE_SPEC.md
- **valid options:** freeze | amend
- **recommended option:** freeze only after Y-D01..Y-D08 and F-D01..F-D16
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** Hash-pinned
- **downstream effect:** experimental authorization
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### F-D18 (Faisal; tasks A12-A16; TECHNICAL_RECOMMENDATION)
- **question:** Technical acceptance of Ahmed's A12-A16 modules (integration gate)
- **available evidence:** Synthetic tests; A12 executed
- **evidence files:** 02_methodology/SUPPORTING_MODEL_SPECS_A14_A16.md
- **valid options:** accept | request changes
- **recommended option:** review then accept
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A14-A16 execution
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D01 (Ahmed; tasks A1;A2;A7; SCIENTIFIC_CHOICE)
- **question:** RQ1 feasibility: D(x) incremental value beyond C/M/H at matched coverage
- **available evidence:** Pooled population dominated by LEAK; 3 outer folds; 39 families
- **evidence files:** 06_audit_preparation/phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md
- **valid options:** testable with restrictions | exploratory only
- **recommended option:** TESTABLE_WITH_RESTRICTIONS (pooled C vs C-D, family-paired; per-class descriptive)
- **justification:** Leakage-safe design exists; class support thin
- **alternatives and limitations:** -
- **statistical implications:** Effect sizes with family-level intervals; null results reportable
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A11
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D02 (Ahmed; tasks A1;A2; SCIENTIFIC_CHOICE)
- **question:** RQ2 feasibility: reproducible SPECIFIC / AMBIGUITY_SET / UNRESOLVED outcomes
- **available evidence:** Policy implemented; thresholds unset
- **evidence files:** 02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md
- **valid options:** testable | exploratory
- **recommended option:** TESTABLE_WITH_RESTRICTIONS (outcome rates and reproducibility); 'meaningful' ambiguity sets EXPLORATORY
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** -
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D03 (Ahmed; tasks A3;A7; SCIENTIFIC_CHOICE)
- **question:** Scope of generalisation: held-out withdrawal topology of one simulated network
- **available evidence:** 3 topologies, simulated only
- **evidence files:** 06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md
- **valid options:** accept stated scope | narrower
- **recommended option:** accept: 'generalisation to an unseen withdrawal topology of the H2-SimNet simulated network'
- **justification:** -
- **alternatives and limitations:** No inference across topologies (n=3)
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A11
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D04 (Ahmed+Faisal; tasks A7;F11; SCIENTIFIC_CHOICE)
- **question:** Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run
- **available evidence:** Plan F11 text
- **evidence files:** assets (Faisal New Plan 2)
- **valid options:** 25% | other | none (effect sizes only)
- **recommended option:** effect sizes only, unless both approve a justified threshold now
- **justification:** Avoids post-hoc thresholds
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** F-D17
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D05 (Ahmed; tasks A4; SCIENTIFIC_CHOICE)
- **question:** Final class definitions (joint with Y-D05d, Y-D06a, F-D05)
- **available evidence:** Candidate label mapping
- **evidence files:** 06_audit_preparation/pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml
- **valid options:** as candidate | amend
- **recommended option:** as candidate
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** all
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** CANDIDATE_LABEL_MAPPING.yaml
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D06 (Ahmed; tasks A3;A10; TECHNICAL_RECOMMENDATION)
- **question:** Dataset description corrections: files vs runs, clean vs noise-added, 1 s verified for Parquet, H2 fraction UNVERIFIED, exclusions
- **available evidence:** Verification and reconciliation reports
- **evidence files:** 06_audit_preparation/RAW_DATASET_VERIFICATION_REPORT.md
- **valid options:** adopt | amend
- **recommended option:** adopt
- **justification:** Evidence-based
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A11
- **required validation:** -
- **implementation may proceed without approval:** YES (drafting)
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D07 (Ahmed; tasks A4; TECHNICAL_RECOMMENDATION)
- **question:** Mathematical consistency sign-off (p, q, D, C, M, H, coverage, risk, sets, thresholds vs code)
- **available evidence:** Symbol register and equation tests
- **evidence files:** 06_audit_preparation/phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md
- **valid options:** sign off | request changes
- **recommended option:** sign off after review
- **justification:** No inconsistency found in code vs register
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A8
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D08 (Ahmed; tasks A7; TECHNICAL_RECOMMENDATION)
- **question:** Adopt the claim and limitation register
- **available evidence:** Register
- **evidence files:** 06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md
- **valid options:** adopt | amend
- **recommended option:** adopt
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** A8;A11
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D09 (Ahmed; tasks A5;A9; TECHNICAL_RECOMMENDATION)
- **question:** Documentation reconciliation: README sections 2/6/7, FIGURE_SPECIFICATION.md, fate of quarantined illustrative figures
- **available evidence:** Issues ISS-03, ISS-08
- **evidence files:** 06_audit_preparation/SCIENTIFIC_AND_TECHNICAL_ISSUES.md
- **valid options:** apply candidate edits | own rewrite; keep | delete quarantine
- **recommended option:** own rewrite using the claim register; keep quarantine until README is fixed
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** -
- **required validation:** -
- **implementation may proceed without approval:** YES (drafting)
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D10 (Ahmed; tasks A9; SCIENTIFIC_CHOICE)
- **question:** Re-record Gates 1-3 in GATE_DECISIONS.md and adopt plan status vocabulary in MASTER_TASK_REGISTER.csv
- **available evidence:** Current PASS records unsupported
- **evidence files:** 00_governance/GATE_DECISIONS.md
- **valid options:** re-record | keep
- **recommended option:** re-record from Phase 2-4 evidence after Yazan/Faisal decisions
- **justification:** -
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** experimental authorization
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### A-D11 (Ahmed; tasks A9; VERIFIED_FACT)
- **question:** Add the authoritative New Plan 2 PDFs to assets/
- **available evidence:** Only older plans tracked
- **evidence files:** assets/
- **valid options:** add | not
- **recommended option:** add
- **justification:** Traceability
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** -
- **required validation:** -
- **implementation may proceed without approval:** YES
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

### G-D01 (User; tasks -; TECHNICAL_RECOMMENDATION)
- **question:** Approve the proposed local commit plan (no push)
- **available evidence:** Staging review
- **evidence files:** 06_audit_preparation/phase4_approvals/GIT_BACKUP_AND_CHANGE_REVIEW.md
- **valid options:** approve | amend | defer
- **recommended option:** approve
- **justification:** Protects work in history; backup exists
- **alternatives and limitations:** -
- **statistical implications:** -
- **leakage implications:** -
- **reproducibility implications:** -
- **downstream effect:** -
- **required validation:** -
- **implementation may proceed without approval:** NO
- **affected artifact hash:** 
- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____

