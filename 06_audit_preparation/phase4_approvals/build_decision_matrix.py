#!/usr/bin/env python3
"""Generate MASTER_DECISION_MATRIX.csv/.md from the decision register below (single source of truth).
Approval fields are intentionally blank: approvals can only be recorded by the named human.
Usage (repo root): python 06_audit_preparation/phase4_approvals/build_decision_matrix.py"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent / "pre_experiment_review"
EV = "06_audit_preparation/phase4_approvals/evidence/"
PR = "06_audit_preparation/pre_experiment_review/"
H = json.loads((PKG / "OUTPUT_HASHES.json").read_text(encoding="utf-8"))


def h(name):
    return f"{name}@{H[name][:12]}" if name in H else name


VF, TR, SC, UN = "VERIFIED_FACT", "TECHNICAL_RECOMMENDATION", "SCIENTIFIC_CHOICE", "UNRESOLVED"
# (id, owner, tasks, class, question, evidence, files, options, recommended, justification, tradeoffs,
#  statistics, leakage, reproducibility, downstream, validation, proceed_without_approval, artifacts)
D = [
 ("Y-D01", "Yazan", "Y1;Y2", TR, "Accept the canonical identity model: 242 tabular files = 57 simulated runs (114 clean, 114 noise-added, 6 _noisy variant, 6 solver-export, 2 misfiled files)?",
  "Every file assigned by path or exact bytes; 0 UNRESOLVED; reconciliation table", PR + "CANDIDATE_FILE_INVENTORY.csv; " + EV + "INVENTORY_RECONCILIATION.csv",
  "accept | amend realization typing | reject", "accept", "All 60 clean-vs-noise and 121 format-twin relations explained numerically; deterministic builder",
  "Rejecting leaves Yazan's 58-scenario map with a duplicate scenario", "Prevents double counting of runs (57 not 115+)", "Removes the byte-duplicate fold-3 leak",
  "Builder is order/separator independent (13/13 identical hashes)", "All folds, families, counts", "Y-D07 manifest diff review", "YES (candidate only)", h("CANDIDATE_FILE_INVENTORY.csv")),
 ("Y-D02", "Yazan", "Y1;Y2", VF, "Confirm that clean, noise-added, _noisy and solver-export files are realizations of the same run and never independent evidence",
  "Labels identical 60/60; residual mean<0.01; lag-1 autocorr~0; solver exports match within 0.08-0.6% of range", PR + "FAMILY_RELATIONSHIP_EVIDENCE.csv",
  "confirm | dispute with evidence", "confirm", "Numerical evidence plus dataset ReadME statement on added Gaussian noise", "-", "Independent n = runs, not files",
  "Realizations must sit on the same side of every split (enforced)", "Hashes of every file kept in inventory", "F-D01", "none beyond review", "YES", h("FAMILY_RELATIONSHIP_EVIDENCE.csv")),
 ("Y-D03", "Yazan", "Y2", UN, "Resolve the 19 short shared-history relationships individually (11 identical-until-25 s start-up pairs; 8 near-identical pre-event trajectories)",
  "Per-pair segment lengths, classes, onsets; 13 cross-class pairs; none crosses topology", EV + "RELATIONSHIP_19_REVIEW.csv",
  "per pair: DEPENDENT (merge) | PLAUSIBLE (sensitivity only) | INDEPENDENT", "8 near-identical leak pairs: treat as dependent for inner splits; 11 start-up pairs: keep separate in primary, merge in sensitivity",
  "A 25-row identical start is shared initial state, not evidenced ancestry (plan Y2 step 23); 387-400 identical pre-event rows of the same valve configuration suggest a common configuration",
  "Merging all reduces LEAK families 30->26 and links FAULT with DELAY", "Affects only family-grouped inner splits and any family bootstrap", "No effect on LOTO outer folds (all within topology)",
  "Decision must be recorded per edge_id", "Y-D04, F-D03, F-D13", "Yazan inspection of simulation configuration if available", "NO (scientific)", "RELATIONSHIP_19_REVIEW.csv"),
 ("Y-D04", "Yazan", "Y2;Y5", SC, "Which family map is the dataset definition: primary (45 families /39 eligible), extended (35/32) or conservative topology-level (3)?",
  "Three maps; all nest within topology; 0/1,083 cross-topology shared rows", PR + "CANDIDATE_FAMILY_MAP.csv; " + PR + "EVALUATION_FEASIBILITY_REPORT.md",
  "primary | extended | conservative | primary + extended as registered sensitivity", "primary + extended registered as sensitivity (conservative used only as an upper-bound check)",
  "Primary merges only evidenced dependence; extended covers the unresolved 19; conservative removes all within-topology resolution",
  "Conservative gives only 3 units: no family-level uncertainty possible", "Effective n: 39 vs 32 vs 3 units over eligible runs", "Outer LOTO is leakage-safe under all three (0 issues)",
  "Maps are deterministic outputs", "F-D03, F-D13, D(x) query-family exclusion", "Re-run validator after choice", "NO (scientific)", h("CANDIDATE_FAMILY_MAP.csv")),
 ("Y-D05a", "Yazan", "Y4", UN, "leakG5G6_overlapped files: filename/ReadME say G5+G6, row labels say leak_G4+leak_G6. Which is authoritative?",
  "3 runs (+noise variants), labels identical across realizations", PR + "LABEL_AND_TIMING_CORRECTIONS.md (L1)",
  "raw labels authoritative | filename authoritative | contact dataset authors", "keep raw labels; record mismatch; contact authors before any location analysis",
  "Class LEAK unaffected; only localisation analyses depend on it", "-", "none for 4-class task", "none", "must be stated in dataset description", "A-D06", "author confirmation (optional)", "YES (class unaffected)", ""),
 ("Y-D05b", "Yazan", "Y4", UN, "brokenC1G5_weak: leak_G5 active on 13,000 rows while Leak=0. Compound event or annotation error?",
  "3 runs; CompressorFault from 25 s", PR + "LABEL_AND_TIMING_CORRECTIONS.md (L2)", "compound (exploratory) | compressor fault with stray location label | exclude",
  "exclude from exclusive 4-class task under both readings (current candidate)", "Both readings make it ineligible for a mutually exclusive target", "Including as FAULT would add 3 runs to a thin class on doubtful labels",
  "-", "-", "-", "Six runs remain excluded in total", "-", "NO for any re-inclusion", ""),
 ("Y-D05c", "Yazan", "Y4", VF, "Confirm exclusion of leakG4brokenC1 (Leak and CompressorFault simultaneously active) from the exclusive task",
  "19,900 rows with both types", PR + "LABEL_AND_TIMING_CORRECTIONS.md (L7)", "exclude | multi-label secondary only", "exclude; keep for exploratory multi-label", "Mutual exclusivity violated", "-", "-", "-", "-", "-", "-", "YES", ""),
 ("Y-D05d", "Yazan+Ahmed", "Y4;A4", SC, "Multi-location single-type leaks (15 runs): LEAK, or exclude all?",
  "G3G4 weak/strong, G3G5, G3G6, G5G6(=G4G6 labels) per topology", PR + "CANDIDATE_LABEL_MAPPING.yaml",
  "LEAK (consistent rule) | exclude all 15 | separate class", "LEAK", "Leak umbrella label is active and no other event type; target does not localise",
  "Excluding leaves 24 LEAK runs; separate class has 5 runs/topology but no plan support", "LEAK remains the only class with >3 runs", "-", "-", "LEAK counts, folds", "-", "NO", h("CANDIDATE_SCENARIO_MANIFEST.csv")),
 ("Y-D06a", "Yazan+Faisal+Ahmed", "Y3;F3;A4", SC, "CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY?",
  "Verified label transitions; ReadME says anomalies last to end", PR + "LABEL_AND_TIMING_CORRECTIONS.md (L3); " + EV + "EVENT_DURATIONS.csv",
  "exclude post-event rows | label NORMAL | relabel DELAY to end", "exclude (do not relabel, do not count as normal)", "No raw-label change; avoids inventing ground truth",
  "DELAY then contributes 31 windows per run at 60/30", "DELAY support is 3 runs regardless", "-", "-", "F-D04, F-D05", "-", "NO", ""),
 ("Y-D06b", "Yazan", "Y3", TR, "Replace folder-derived phase with verified onset time plus documented ReadME phase; folder kept as segment_dir",
  "C1 events onset 25 s in constant_segment folders; ReadME places them in ramp-up", PR + "LABEL_AND_TIMING_CORRECTIONS.md (L4-L5)", "accept | keep folder phase",
  "accept", "Folder names are not phase evidence", "-", "Phase is confounded with class by design; must not be a feature", "-", "-", "A-D06 dataset description", "-", "YES", ""),
 ("Y-D07", "Yazan", "Y8", TR, "Issue candidate manifest v0.2 (replacing v0.1 for use; v0.1 kept traceable)",
  "Candidate manifest and freeze spec", PR + "CANDIDATE_SCENARIO_MANIFEST.csv; 06_audit_preparation/phase4_approvals/CANDIDATE_DATASET_FREEZE_SPEC.md",
  "issue v0.2 as proposed | amend then issue", "issue after Y-D01..Y-D06", "Single versioned handoff with hashes", "-", "-", "-", "Hash-pinned", "F-D02..F-D17", "A12 validation on v0.2", "NO", h("CANDIDATE_SCENARIO_MANIFEST.csv")),
 ("Y-D08", "Yazan", "Y7", SC, "Re-issue the dataset readiness decision (current READY_WITH_EXCLUSIONS is unsupported)",
  "Candidate readiness evidence", "06_audit_preparation/phase4_approvals/YAZAN_DATASET_APPROVAL_DOSSIER.md", "READY_WITH_EXCLUSIONS (restricted) | EXPLORATORY_ONLY | other",
  "READY_WITH_EXCLUSIONS for a pooled LOTO evaluation, with NORMAL/FAULT/DELAY marked descriptive-only", "Leakage resolved in candidate; class support thin", "-", "-", "-", "-", "Gate 1-3 re-record", "Ahmed approval of interpretation", "NO", ""),
 ("Y-D09", "Yazan", "Y1;Y2", TR, "Fix portability/determinism of audit/ scripts or adopt src/h2prism/dataset_manifest.py as the reference builder",
  "OS-dependent canonical file choice (58/58 vs 3/58)", PR + "CROSS_PLATFORM_REPRODUCIBILITY.md", "adopt module | patch audit scripts | both", "adopt module; leave audit/ as historical", "Module is tested and hash-verified", "-", "-", "-", "Deterministic", "-", "-", "YES", ""),
 ("Y-D10", "Yazan", "Y1", VF, "Correct raw_checksums.sha256 provenance (8 files hashed after CRLF->LF; .gitkeep not in archive; 264 not 265 files)",
  "Checksum reconciliation", "06_audit_preparation/raw_verification/CHECKSUM_RECONCILIATION.csv", "regenerate from untouched archive | annotate", "regenerate", "Plan: never alter raw files", "-", "-", "-", "Archive MD5 recorded", "A10 provenance", "-", "YES", ""),
 ("F-D01", "Faisal", "F3;F4;F10", SC, "Modelling realization: clean, noise-added, or one predefined primary with the other as controlled secondary robustness",
  "Both realizations exist for every run; noise is white, ~1e-4-1e-3 of range", PR + "DATASET_RECONCILIATION_REPORT.md",
  "A clean-only | B noise-added-only | C primary noise-added + clean secondary | D primary clean + noise-added secondary", "C (noise-added primary; clean as a pre-registered secondary)",
  "Noise-added release reflects sensor uncertainty intended by the publisher; clean secondary measures sensitivity without selecting on outcomes",
  "A overstates separability; B alone loses the noise-sensitivity check; using both as training data doubles evidence (prohibited)", "Never pool realizations as independent samples",
  "Both realizations of a run always on the same side", "Choice fixed before any run", "F-D04..F-D17", "-", "NO (scientific)", ""),
 ("F-D02", "Faisal", "F4", TR, "Adopt leave-one-topology-out (3 outer folds) as the primary outer design",
  "0 validation issues under 3 family views; all classes in every train/test fold; topology carries no class information", PR + "CANDIDATE_OUTER_FOLDS.csv; " + PR + "EVALUATION_FEASIBILITY_REPORT.md",
  "LOTO | grouped K-fold over primary families mixing topologies | restricted per-class design", "LOTO",
  "Only design where every class is present in every train and test fold and no dependence crosses a split",
  "Family K-fold would test within-topology generalisation but leaves test folds without NORMAL/DELAY", "3 folds; between-fold variance = topology shift", "Verified leakage-safe",
  "Fold file hash-pinned", "F-D03, F-D13, F-D17", "-", "NO", h("CANDIDATE_OUTER_FOLDS.csv")),
 ("F-D03", "Faisal", "F4;F6;F7;F9", TR, "Inner development scheme for selection, calibration, D reference checks and threshold development",
  "LOTO_within_train: 6/6 feasible, every class in every inner train and validation; family-k3: 9/9 class-in-train feasible but some validation splits lack NORMAL/FAULT/DELAY", EV + "INNER_FOLD_SUFFICIENCY.csv",
  "LOTO_within_train | grouped_by_family_primary_k3", "LOTO_within_train", "Only scheme supporting per-class calibration and threshold development",
  "Each inner train holds 1 NORMAL run, 1 DELAY run (31 windows at 60/30)", "Development estimates rest on single runs for 3 classes", "Nested within outer train (tested)", "Deterministic", "F-D08, F-D09, F-D12", "-", "NO", h("CANDIDATE_INNER_FOLDS.csv")),
 ("F-D04", "Faisal", "F3", SC, "Window length / stride",
  "Options compared on all 51 eligible runs (windowing only)", EV + "WINDOW_OPTION_COMPARISON.csv",
  "30/15 | 60/30 | 60/60 | 120/60 | 300/150", "60/30 as primary candidate; 60/60 (non-overlapping) as dependence sensitivity",
  "1 s sampling verified; shortest event = DELAY 976 s -> 31 windows/run at 60/30 vs 6 at 300/150; boundary losses <0.3%", "30/15 doubles correlated windows without new runs; 300/150 leaves 12 DELAY windows in total",
  "Windows are repeated measures; overlap 50% at stride=w/2", "-", "Deterministic window IDs", "F-D05, F-D07", "-", "NO", "WINDOW_OPTION_COMPARISON.csv"),
 ("F-D05", "Faisal+Yazan+Ahmed", "F3;Y3;Y4", SC, "Pre-/post-event rows of fault runs: exclude, or label NORMAL?",
  "label_normal raises NORMAL contributing runs 3 -> 45 (all early-time windows)", EV + "WINDOW_OPTION_COMPARISON.csv",
  "exclude | label_normal | label_normal as secondary analysis", "exclude for primary; label_normal as pre-registered secondary",
  "Pre-event windows are early-run (ramp-up/transient) only, so NORMAL would become phase-confounded; primary avoids that",
  "Exclude keeps NORMAL at 3 independent runs (descriptive only)", "Changes NORMAL from 3 to 45 contributing runs", "Pre-event and event windows of one run share the family (never split)", "-", "F-D07, A-D01", "-", "NO", ""),
 ("F-D06", "Faisal", "F3", TR, "Candidate feature contract: 16 verified channels x {mean,std,min,max,range,last_minus_first,slope,mean_abs_diff}; no cross-channel features; offset-invariant subset as A15 arm",
  "Feature register; channel/unit audit", "02_methodology/FEATURE_DEFINITION_REGISTER.csv", "full 128 | offset-invariant 80 | subset", "full 128 primary; offset-invariant as sensitivity (A15)",
  "Absolute pressure levels can fingerprint topology/run", "-", "-", "Scaling fitted on training only (enforced); IDs never features", "Deterministic feature hash", "F-D08, A15", "-", "NO", "FEATURE_DEFINITION_REGISTER.csv"),
 ("F-D07", "Faisal+Ahmed", "F4;F10;F11", SC, "Thin-class policy: what may be inferred per class",
  "NORMAL 3, DELAY 3, FAULT 6 runs (3 families), LEAK 39 runs (30 families)", PR + "EVALUATION_FEASIBILITY_REPORT.md",
  "pooled primary + descriptive per class | per-class inference | reduce task", "pooled primary metrics with per-family tables; per-class results DESCRIPTIVE_ONLY for NORMAL/FAULT/DELAY",
  "1 run per class per test fold cannot support class-specific inference", "Reducing the task would need A-D05 approval", "No pseudo-replication via windows", "-", "-", "F-D13, A-D03", "-", "NO", ""),
 ("F-D08", "Faisal", "F7", SC, "D(x) settings: k, weighting, prior correction, scenario balancing, flag thresholds",
  "Implementation tested (17 tests); outer-train reference: NORMAL 2 runs/1330 windows, DELAY 2 runs/62 windows (60/30)", EV + "OUTER_TRAIN_REFERENCE_SUPPORT.csv; 02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md",
  "k in {10,25,50}; uniform | inverse-distance; prior correction on/off; scenario-balanced support", "pre-register k=25 uniform without prior correction as primary; flags min_distinct_scenarios=2; prior correction and k=10/50 as sensitivity",
  "k=25 is the plan default; with 31 DELAY windows per run a k-neighbourhood can be dominated by one run, so LOW_SCENARIO_DIVERSITY must be reported", "Larger k swamps DELAY", "D is per-window; dependence handled at family level",
  "Query-family exclusion and train-only reference enforced", "Config-pinned", "F-D10, F-D11", "development-only diagnostics", "NO", ""),
 ("F-D09", "Faisal", "F6", TR, "Calibration candidates and selection criterion",
  "calibration.py: none/sigmoid/isotonic, grouped cross-fitted selection keeps 'none' unless strictly better", "src/h2prism/calibration.py",
  "log-loss | Brier criterion; methods subset", "log-loss criterion over {none, sigmoid, isotonic} on inner OOF (LOTO_within_train)", "Plan F6; retains uncalibrated by default",
  "Isotonic with 1 run per class in development is fragile", "-", "Never fitted on outer test (enforced)", "-", "F-D10", "-", "NO", ""),
 ("F-D10", "Faisal", "F8;F10;A16", TR, "Comparators and combined scores: C, M, -H, D; s_C = LR[logit C, M, -H, D], s_C-D = LR[logit C, M, -H] cross-fitted on development",
  "comparators.py tested; meta-model not implemented", "src/h2prism/comparators.py", "as plan | rank-normalised", "as plan", "Plan F8/F10", "-", "-", "Meta-model must use cross-fitted development predictions only", "-", "F-D12", "implementation + tests", "YES (implementation of plan definition)", ""),
 ("F-D11", "Faisal+Ahmed", "F9", SC, "Policy parameters: candidate source, singleton handling, max set size, blocking flags",
  "policy.py tested; K=4 admits max_set_size in {2,3}", "02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md",
  "p-only | p+q candidates; expand_to_two | unresolved; 2 | 3; flags", "p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC",
  "Conservative: weak evidence never becomes SPECIFIC or a broad set", "max_set_size=3 at K=4 is near-uninformative", "-", "-", "-", "F-D12, A-D02", "-", "NO", ""),
 ("F-D12", "Faisal", "F9;F10", TR, "Threshold development: thresholds chosen on inner OOF predictions only, frozen before outer test",
  "PolicyConfig refuses non-development sources", "src/h2prism/policy.py", "target-coverage rule (0.80 primary) | risk-target rule", "target coverage 0.80 on development OOF; 0.60/0.90 secondary (plan F10)", "Plan F10 step 85", "-", "-", "Enforced in code", "-", "F-D17", "-", "NO", ""),
 ("F-D13", "Faisal+Ahmed", "F10;F11", SC, "Metric weighting and uncertainty: pooled, family-level, family-balanced; bootstrap unit",
  "39 primary families (32 extended) among eligible runs; 3 topologies", PR + "EVALUATION_FEASIBILITY_REPORT.md",
  "family bootstrap (primary map) | extended map | no inference", "paired family bootstrap on primary map, extended map as sensitivity; report per-family tables; no topology-level inference",
  "Families are the independence unit", "LEAK dominates pooled metrics", "Windows never resampled", "-", "Seeded", "A-D03, A-D11", "-", "NO", ""),
 ("F-D14", "Faisal", "F5", TR, "Accept the plan RF grid (n_estimators {300,500} x min_samples_leaf {1,5} x max_features {sqrt,0.3}), class_weight balanced_subsample, fixed seed",
  "baseline.rf_param_grid matches the plan (tested)", "src/h2prism/baseline.py", "accept | amend", "accept; seed 20261104", "Plan F5", "-", "-", "Selection on inner OOF only (tested)", "-", "F-D17", "-", "YES", ""),
 ("F-D15", "Faisal", "F3-F9;F12", TR, "Technical acceptance of new code: io (Timestamp index), windows, features, splits, baseline, calibration, distinguishability, policy, metrics, dataset_manifest",
  "158 passed / 2 skipped; real-file windowing interface tests", "06_audit_preparation/phase4_approvals/VALIDATION_AND_REGRESSION_REPORT.md", "accept | request changes", "review then accept", "-", "-", "-", "-", "-", "all", "code review", "NO", ""),
 ("F-D16", "Faisal", "F12", TR, "Amend configs/interface_contracts.yaml (manifest, window, prediction schema additions)",
  "Proposed amendments", "06_audit_preparation/MODEL_AND_EXPERIMENT_READINESS.md", "accept | amend", "accept", "Contract currently lacks fields the plan requires", "-", "-", "-", "Change-control log entry", "A12 validation", "-", "NO", ""),
 ("F-D17", "Faisal+Ahmed", "F4;A9", SC, "Freeze configs/frozen_evaluation_config.yaml from the candidate spec once all F/Y decisions are recorded",
  "Candidate spec with explicit PENDING placeholders", "06_audit_preparation/phase4_approvals/CANDIDATE_EVALUATION_FREEZE_SPEC.md", "freeze | amend", "freeze only after Y-D01..Y-D08 and F-D01..F-D16", "-", "-", "-", "-", "Hash-pinned", "experimental authorization", "-", "NO", ""),
 ("F-D18", "Faisal", "A12-A16", TR, "Technical acceptance of Ahmed's A12-A16 modules (integration gate)",
  "Synthetic tests; A12 executed", "02_methodology/SUPPORTING_MODEL_SPECS_A14_A16.md", "accept | request changes", "review then accept", "-", "-", "-", "-", "-", "A14-A16 execution", "-", "NO", ""),
 ("A-D01", "Ahmed", "A1;A2;A7", SC, "RQ1 feasibility: D(x) incremental value beyond C/M/H at matched coverage",
  "Pooled population dominated by LEAK; 3 outer folds; 39 families", "06_audit_preparation/phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md",
  "testable with restrictions | exploratory only", "TESTABLE_WITH_RESTRICTIONS (pooled C vs C-D, family-paired; per-class descriptive)", "Leakage-safe design exists; class support thin", "-", "Effect sizes with family-level intervals; null results reportable", "-", "-", "A11", "-", "NO", ""),
 ("A-D02", "Ahmed", "A1;A2", SC, "RQ2 feasibility: reproducible SPECIFIC / AMBIGUITY_SET / UNRESOLVED outcomes",
  "Policy implemented; thresholds unset", "02_methodology/SELECTIVE_DIAGNOSTIC_POLICY.md", "testable | exploratory", "TESTABLE_WITH_RESTRICTIONS (outcome rates and reproducibility); 'meaningful' ambiguity sets EXPLORATORY", "-", "-", "-", "-", "-", "-", "-", "NO", ""),
 ("A-D03", "Ahmed", "A3;A7", SC, "Scope of generalisation: held-out withdrawal topology of one simulated network",
  "3 topologies, simulated only", "06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md", "accept stated scope | narrower", "accept: 'generalisation to an unseen withdrawal topology of the H2-SimNet simulated network'", "-", "No inference across topologies (n=3)", "-", "-", "-", "A11", "-", "NO", ""),
 ("A-D04", "Ahmed+Faisal", "A7;F11", SC, "Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run",
  "Plan F11 text", "assets (Faisal New Plan 2)", "25% | other | none (effect sizes only)", "effect sizes only, unless both approve a justified threshold now", "Avoids post-hoc thresholds", "-", "-", "-", "-", "F-D17", "-", "NO", ""),
 ("A-D05", "Ahmed", "A4", SC, "Final class definitions (joint with Y-D05d, Y-D06a, F-D05)", "Candidate label mapping", PR + "CANDIDATE_LABEL_MAPPING.yaml",
  "as candidate | amend", "as candidate", "-", "-", "-", "-", "-", "all", "-", "NO", h("CANDIDATE_LABEL_MAPPING.yaml") if "CANDIDATE_LABEL_MAPPING.yaml" in H else "CANDIDATE_LABEL_MAPPING.yaml"),
 ("A-D06", "Ahmed", "A3;A10", TR, "Dataset description corrections: files vs runs, clean vs noise-added, 1 s verified for Parquet, H2 fraction UNVERIFIED, exclusions",
  "Verification and reconciliation reports", "06_audit_preparation/RAW_DATASET_VERIFICATION_REPORT.md", "adopt | amend", "adopt", "Evidence-based", "-", "-", "-", "-", "A11", "-", "YES (drafting)", ""),
 ("A-D07", "Ahmed", "A4", TR, "Mathematical consistency sign-off (p, q, D, C, M, H, coverage, risk, sets, thresholds vs code)",
  "Symbol register and equation tests", "06_audit_preparation/phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md", "sign off | request changes", "sign off after review", "No inconsistency found in code vs register", "-", "-", "-", "-", "A8", "-", "NO", ""),
 ("A-D08", "Ahmed", "A7", TR, "Adopt the claim and limitation register", "Register", "06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md", "adopt | amend", "adopt", "-", "-", "-", "-", "-", "A8;A11", "-", "NO", ""),
 ("A-D09", "Ahmed", "A5;A9", TR, "Documentation reconciliation: README sections 2/6/7, FIGURE_SPECIFICATION.md, fate of quarantined illustrative figures",
  "Issues ISS-03, ISS-08", "06_audit_preparation/SCIENTIFIC_AND_TECHNICAL_ISSUES.md", "apply candidate edits | own rewrite; keep | delete quarantine", "own rewrite using the claim register; keep quarantine until README is fixed", "-", "-", "-", "-", "-", "-", "-", "YES (drafting)", ""),
 ("A-D10", "Ahmed", "A9", SC, "Re-record Gates 1-3 in GATE_DECISIONS.md and adopt plan status vocabulary in MASTER_TASK_REGISTER.csv",
  "Current PASS records unsupported", "00_governance/GATE_DECISIONS.md", "re-record | keep", "re-record from Phase 2-4 evidence after Yazan/Faisal decisions", "-", "-", "-", "-", "-", "experimental authorization", "-", "NO", ""),
 ("A-D11", "Ahmed", "A9", VF, "Add the authoritative New Plan 2 PDFs to assets/", "Only older plans tracked", "assets/", "add | not", "add", "Traceability", "-", "-", "-", "-", "-", "-", "YES", ""),
 ("G-D01", "User", "-", TR, "Approve the proposed local commit plan (no push)", "Staging review", "06_audit_preparation/phase4_approvals/GIT_BACKUP_AND_CHANGE_REVIEW.md",
  "approve | amend | defer", "approve", "Protects work in history; backup exists", "-", "-", "-", "-", "-", "-", "NO", ""),
]
COLS = ["decision_id", "owner", "related_tasks", "evidence_class", "question", "available_evidence", "evidence_files", "valid_options",
        "recommended_option", "justification", "alternatives_and_limitations", "statistical_implications", "leakage_implications",
        "reproducibility_implications", "downstream_effect", "required_validation", "implementation_may_proceed_without_approval",
        "affected_artifact_hash", "approval_status", "human_reviewer", "final_decision", "approval_date", "approval_evidence_reference"]


def main():
    rows = []
    for d in D:
        (i, o, t, c, q, e, f, opt, rec, j, alt, st, lk, rp, ds, val, pro, art) = d
        rows.append(dict(zip(COLS, [i, o, t, c, q, e, f, opt, rec, j, alt, st, lk, rp, ds, val, pro, art,
                                    "PENDING_HUMAN_APPROVAL", o, "", "", ""])))
    assert len({r["decision_id"] for r in rows}) == len(rows)
    with open(HERE / "MASTER_DECISION_MATRIX.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    md = ["# Master Decision Matrix (generated from build_decision_matrix.py; do not edit by hand)", "",
          "Every approval field is `PENDING_HUMAN_APPROVAL`. A recommendation is **not** a decision.", "",
          f"Decisions: **{len(rows)}**. By owner: " + ", ".join(f"{k}: {v}" for k, v in sorted(
              {o: sum(1 for r in rows if r['owner'] == o) for o in {r['owner'] for r in rows}}.items())), "",
          "By evidence class: " + ", ".join(f"{k}: {sum(1 for r in rows if r['evidence_class'] == k)}" for k in (VF, TR, SC, UN)), "",
          "| ID | Owner | Class | Question | Recommended | May proceed without approval |", "| --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        md.append(f"| {r['decision_id']} | {r['owner']} | {r['evidence_class']} | {r['question']} | {r['recommended_option']} | {r['implementation_may_proceed_without_approval']} |")
    md += ["", "## Details", ""]
    for r in rows:
        md.append(f"### {r['decision_id']} ({r['owner']}; tasks {r['related_tasks']}; {r['evidence_class']})")
        for k in COLS[4:18]:
            md.append(f"- **{k.replace('_', ' ')}:** {r[k]}")
        md.append("- **approval:** PENDING_HUMAN_APPROVAL. Final decision: ____ Approver: ____ Date: ____ Evidence: ____")
        md.append("")
    (HERE / "MASTER_DECISION_MATRIX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(len(rows))


if __name__ == "__main__":
    main()
