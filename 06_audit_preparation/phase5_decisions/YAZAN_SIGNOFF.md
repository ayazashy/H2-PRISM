# Yazan: Sign-off Sheet (Phase 5)

15 decisions (7 P0). Joint decisions also appear on the co-owners' sheets and need every owner's signature. Recommendations are not decisions; fill the fields yourself. Full context: `TEAM_DECISION_BRIEF.md`, `DECISION_REVIEW_P5.csv`.

## F-D05 [P0 · SCIENTIFIC_CHOICE] (Faisal+Yazan+Ahmed)

- **Decision:** Pre-/post-event rows of fault runs: exclude, or label NORMAL?
- **Recommended:** exclude primary; label_normal as pre-registered secondary (raises NORMAL runs 3 -> 45 but all early-time windows: phase confound)
- **Evidence:** 06_audit_preparation/phase4_approvals/evidence/WINDOW_OPTION_COMPARISON.csv
- **Implications / main risk:** Exclude: NORMAL = 3 runs; label_normal: NORMAL confounded with time-in-run
- **Triggers / unblocks:** F-D04, F-D07, A-D01
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D01 [P0 · TECHNICAL_RECOMMENDATION] (Yazan)

- **Decision:** Accept the canonical identity model: 242 tabular files = 57 simulated runs (114 clean, 114 noise-added, 6 _noisy variant, 6 solver-export, 2 misfiled files)?
- **Recommended:** Approve 57-run identity model
- **Evidence:** 06_audit_preparation/pre_experiment_review/CANDIDATE_FILE_INVENTORY.csv; 06_audit_preparation/phase4_approvals/evidence/INVENTORY_RECONCILIATION.csv
- **Implications / main risk:** Rejection reintroduces the duplicate scenario that leaked in fold 3
- **Triggers / unblocks:** Y-D07, all folds/counts
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D05b [P0 · UNRESOLVED] (Yazan)

- **Decision:** brokenC1G5_weak: leak_G5 active on 13,000 rows while Leak=0. Compound event or annotation error?
- **Recommended:** Exclude from exclusive task (restriction). Ground truth: INSUFFICIENT_EVIDENCE
- **Evidence:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L2)
- **Implications / main risk:** Re-including would add doubtful labels to a 6-run class
- **Triggers / unblocks:** Eligible inventory (51), Y-D07
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

## Y-D07 [P0 · TECHNICAL_RECOMMENDATION] (Yazan)

- **Decision:** Issue candidate manifest v0.2 (replacing v0.1 for use; v0.1 kept traceable)
- **Recommended:** Issue manifest v0.2 after Y-D01, Y-D05*, Y-D06a
- **Evidence:** 06_audit_preparation/pre_experiment_review/CANDIDATE_SCENARIO_MANIFEST.csv; 06_audit_preparation/phase4_approvals/CANDIDATE_DATASET_FREEZE_SPEC.md
- **Implications / main risk:** Experiments on an unversioned manifest
- **Triggers / unblocks:** F-D17, everything downstream
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D08 [P0 · SCIENTIFIC_CHOICE] (Yazan)

- **Decision:** Re-issue the dataset readiness decision (current READY_WITH_EXCLUSIONS is unsupported)
- **Recommended:** READY_WITH_EXCLUSIONS (restricted): pooled LOTO; NORMAL/FAULT/DELAY descriptive only
- **Evidence:** 06_audit_preparation/phase4_approvals/YAZAN_DATASET_APPROVAL_DOSSIER.md
- **Implications / main risk:** Overstated readiness
- **Triggers / unblocks:** A-D10, experimental authorization
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D02 [P1 · VERIFIED_FACT] (Yazan)

- **Decision:** Confirm that clean, noise-added, _noisy and solver-export files are realizations of the same run and never independent evidence
- **Recommended:** Confirm (numerical evidence)
- **Evidence:** 06_audit_preparation/pre_experiment_review/FAMILY_RELATIONSHIP_EVIDENCE.csv
- **Implications / main risk:** None material; double counting if ignored
- **Triggers / unblocks:** F-D01
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D03 [P1 · UNRESOLVED] (Yazan)

- **Decision:** Resolve the 19 short shared-history relationships individually (11 identical-until-25 s start-up pairs; 8 near-identical pre-event trajectories)
- **Recommended:** 11 start-up pairs separate; 8 near-identical pairs grouped conservatively in sensitivity view. Ancestry itself: INSUFFICIENT_EVIDENCE (needs .slx inspection)
- **Evidence:** 06_audit_preparation/phase4_approvals/evidence/RELATIONSHIP_19_REVIEW.csv
- **Implications / main risk:** Treating signal similarity as ancestry (or ignoring it) mis-sizes families
- **Triggers / unblocks:** Y-D04, F-D13 only. Phase-5 finding: no effect on LOTO outer or LOTO inner splits (all pairs within topology), so not P0
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D04 [P1 · SCIENTIFIC_CHOICE] (Yazan)

- **Decision:** Which family map is the dataset definition: primary (45 families /39 eligible), extended (35/32) or conservative topology-level (3)?
- **Recommended:** Primary map (39 eligible families) + extended map (32) as registered sensitivity
- **Evidence:** 06_audit_preparation/pre_experiment_review/CANDIDATE_FAMILY_MAP.csv; 06_audit_preparation/pre_experiment_review/EVALUATION_FEASIBILITY_REPORT.md
- **Implications / main risk:** Family count drives bootstrap precision; over-splitting understates dependence
- **Triggers / unblocks:** F-D13, D(x) development query-family exclusion. Not split assignment under LOTO
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D05c [P1 · VERIFIED_FACT] (Yazan)

- **Decision:** Confirm exclusion of leakG4brokenC1 (Leak and CompressorFault simultaneously active) from the exclusive task
- **Recommended:** Exclude compound runs; exploratory multi-label only
- **Evidence:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L7)
- **Implications / main risk:** None
- **Triggers / unblocks:** Y-D07
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D06b [P2 · TECHNICAL_RECOMMENDATION] (Yazan)

- **Decision:** Replace folder-derived phase with verified onset time plus documented ReadME phase; folder kept as segment_dir
- **Recommended:** Use verified onset; folder name only as segment_dir
- **Evidence:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L4-L5)
- **Implications / main risk:** Phase used as feature or stratum would be wrong for C1 runs
- **Triggers / unblocks:** A-D06
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D09 [P2 · TECHNICAL_RECOMMENDATION] (Yazan)

- **Decision:** Fix portability/determinism of audit/ scripts or adopt src/h2prism/dataset_manifest.py as the reference builder
- **Recommended:** Adopt src/h2prism/dataset_manifest.py as reference builder
- **Evidence:** 06_audit_preparation/pre_experiment_review/CROSS_PLATFORM_REPRODUCIBILITY.md
- **Implications / main risk:** Divergent IDs if audit/ scripts reused
- **Triggers / unblocks:** Reproducibility only
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D10 [P2 · VERIFIED_FACT] (Yazan)

- **Decision:** Correct raw_checksums.sha256 provenance (8 files hashed after CRLF->LF; .gitkeep not in archive; 264 not 265 files)
- **Recommended:** Regenerate raw_checksums.sha256 from untouched archive
- **Evidence:** 06_audit_preparation/raw_verification/CHECKSUM_RECONCILIATION.csv
- **Implications / main risk:** Provenance mismatch on re-verification
- **Triggers / unblocks:** A10 provenance
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

## Y-D05a [P3 · UNRESOLVED] (Yazan)

- **Decision:** leakG5G6_overlapped files: filename/ReadME say G5+G6, row labels say leak_G4+leak_G6. Which is authoritative?
- **Recommended:** Keep raw labels; record mismatch; prohibit location analyses. Ground truth: INSUFFICIENT_EVIDENCE
- **Evidence:** 06_audit_preparation/pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md (L1)
- **Implications / main risk:** Wrong location semantics if localisation is ever attempted
- **Triggers / unblocks:** None for 4-class task
- **Approve (exact option, artifact hash/version, conditions):** ______________________
- **Reject / alternative / send back for evidence (reason):** ______________________
- **Signature / date / evidence reference:** ______________________

