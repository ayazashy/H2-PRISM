# Team Sign-off Checklist (blank: to be completed only by the named person)

Rules: an approval needs the decision ID, approver, the exact selected option, date, the version/hash of affected artifacts, conditions, and an evidence reference (e.g. signed message, meeting minutes, PR review). Claude must not fill these fields.

Generated from `MASTER_DECISION_MATRIX.csv` (44 decisions). Joint decisions list all owners; every listed owner must sign.

## Yazan (15 decisions)

| ID | Question | Recommended (not a decision) | Selected option | Approver | Date | Artifact hash/version | Conditions | Evidence ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Y-D01 | Accept the canonical identity model: 242 tabular files = 57 simulated runs (114 clean, 114 noise-added, 6 _noisy variant, 6 solver-export, 2 misfiled files)? | accept | | | | | | |
| Y-D02 | Confirm that clean, noise-added, _noisy and solver-export files are realizations of the same run and never independent evidence | confirm | | | | | | |
| Y-D03 | Resolve the 19 short shared-history relationships individually (11 identical-until-25 s start-up pairs; 8 near-identical pre-event trajectories) | 8 near-identical leak pairs: treat as dependent for inner splits; 11 start-up pairs: keep separate in primary, merge in sensitivity | | | | | | |
| Y-D04 | Which family map is the dataset definition: primary (45 families /39 eligible), extended (35/32) or conservative topology-level (3)? | primary + extended registered as sensitivity (conservative used only as an upper-bound check) | | | | | | |
| Y-D05a | leakG5G6_overlapped files: filename/ReadME say G5+G6, row labels say leak_G4+leak_G6. Which is authoritative? | keep raw labels; record mismatch; contact authors before any location analysis | | | | | | |
| Y-D05b | brokenC1G5_weak: leak_G5 active on 13,000 rows while Leak=0. Compound event or annotation error? | exclude from exclusive 4-class task under both readings (current candidate) | | | | | | |
| Y-D05c | Confirm exclusion of leakG4brokenC1 (Leak and CompressorFault simultaneously active) from the exclusive task | exclude; keep for exploratory multi-label | | | | | | |
| Y-D05d | Multi-location single-type leaks (15 runs): LEAK, or exclude all? | LEAK | | | | | | |
| Y-D06a | CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY? | exclude (do not relabel, do not count as normal) | | | | | | |
| Y-D06b | Replace folder-derived phase with verified onset time plus documented ReadME phase; folder kept as segment_dir | accept | | | | | | |
| Y-D07 | Issue candidate manifest v0.2 (replacing v0.1 for use; v0.1 kept traceable) | issue after Y-D01..Y-D06 | | | | | | |
| Y-D08 | Re-issue the dataset readiness decision (current READY_WITH_EXCLUSIONS is unsupported) | READY_WITH_EXCLUSIONS for a pooled LOTO evaluation, with NORMAL/FAULT/DELAY marked descriptive-only | | | | | | |
| Y-D09 | Fix portability/determinism of audit/ scripts or adopt src/h2prism/dataset_manifest.py as the reference builder | adopt module; leave audit/ as historical | | | | | | |
| Y-D10 | Correct raw_checksums.sha256 provenance (8 files hashed after CRLF->LF; .gitkeep not in archive; 264 not 265 files) | regenerate | | | | | | |
| F-D05 | Pre-/post-event rows of fault runs: exclude, or label NORMAL? | exclude for primary; label_normal as pre-registered secondary | | | | | | |

## Faisal (20 decisions)

| ID | Question | Recommended (not a decision) | Selected option | Approver | Date | Artifact hash/version | Conditions | Evidence ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Y-D06a | CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY? | exclude (do not relabel, do not count as normal) | | | | | | |
| F-D01 | Modelling realization: clean, noise-added, or one predefined primary with the other as controlled secondary robustness | C (noise-added primary; clean as a pre-registered secondary) | | | | | | |
| F-D02 | Adopt leave-one-topology-out (3 outer folds) as the primary outer design | LOTO | | | | | | |
| F-D03 | Inner development scheme for selection, calibration, D reference checks and threshold development | LOTO_within_train | | | | | | |
| F-D04 | Window length / stride | 60/30 as primary candidate; 60/60 (non-overlapping) as dependence sensitivity | | | | | | |
| F-D05 | Pre-/post-event rows of fault runs: exclude, or label NORMAL? | exclude for primary; label_normal as pre-registered secondary | | | | | | |
| F-D06 | Candidate feature contract: 16 verified channels x {mean,std,min,max,range,last_minus_first,slope,mean_abs_diff}; no cross-channel features; offset-invariant subset as A15 arm | full 128 primary; offset-invariant as sensitivity (A15) | | | | | | |
| F-D07 | Thin-class policy: what may be inferred per class | pooled primary metrics with per-family tables; per-class results DESCRIPTIVE_ONLY for NORMAL/FAULT/DELAY | | | | | | |
| F-D08 | D(x) settings: k, weighting, prior correction, scenario balancing, flag thresholds | pre-register k=25 uniform without prior correction as primary; flags min_distinct_scenarios=2; prior correction and k=10/50 as sensitivity | | | | | | |
| F-D09 | Calibration candidates and selection criterion | log-loss criterion over {none, sigmoid, isotonic} on inner OOF (LOTO_within_train) | | | | | | |
| F-D10 | Comparators and combined scores: C, M, -H, D; s_C = LR[logit C, M, -H, D], s_C-D = LR[logit C, M, -H] cross-fitted on development | as plan | | | | | | |
| F-D11 | Policy parameters: candidate source, singleton handling, max set size, blocking flags | p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC | | | | | | |
| F-D12 | Threshold development: thresholds chosen on inner OOF predictions only, frozen before outer test | target coverage 0.80 on development OOF; 0.60/0.90 secondary (plan F10) | | | | | | |
| F-D13 | Metric weighting and uncertainty: pooled, family-level, family-balanced; bootstrap unit | paired family bootstrap on primary map, extended map as sensitivity; report per-family tables; no topology-level inference | | | | | | |
| F-D14 | Accept the plan RF grid (n_estimators {300,500} x min_samples_leaf {1,5} x max_features {sqrt,0.3}), class_weight balanced_subsample, fixed seed | accept; seed 20261104 | | | | | | |
| F-D15 | Technical acceptance of new code: io (Timestamp index), windows, features, splits, baseline, calibration, distinguishability, policy, metrics, dataset_manifest | review then accept | | | | | | |
| F-D16 | Amend configs/interface_contracts.yaml (manifest, window, prediction schema additions) | accept | | | | | | |
| F-D17 | Freeze configs/frozen_evaluation_config.yaml from the candidate spec once all F/Y decisions are recorded | freeze only after Y-D01..Y-D08 and F-D01..F-D16 | | | | | | |
| F-D18 | Technical acceptance of Ahmed's A12-A16 modules (integration gate) | review then accept | | | | | | |
| A-D04 | Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run | effect sizes only, unless both approve a justified threshold now | | | | | | |

## Ahmed (18 decisions)

| ID | Question | Recommended (not a decision) | Selected option | Approver | Date | Artifact hash/version | Conditions | Evidence ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Y-D05d | Multi-location single-type leaks (15 runs): LEAK, or exclude all? | LEAK | | | | | | |
| Y-D06a | CompressorDelay is labelled only 25-1000 s (976 s). Are post-delay rows NORMAL, excluded, or still DELAY? | exclude (do not relabel, do not count as normal) | | | | | | |
| F-D05 | Pre-/post-event rows of fault runs: exclude, or label NORMAL? | exclude for primary; label_normal as pre-registered secondary | | | | | | |
| F-D07 | Thin-class policy: what may be inferred per class | pooled primary metrics with per-family tables; per-class results DESCRIPTIVE_ONLY for NORMAL/FAULT/DELAY | | | | | | |
| F-D11 | Policy parameters: candidate source, singleton handling, max set size, blocking flags | p-only candidates; singleton -> UNRESOLVED; max_set_size=2; OUT_OF_SUPPORT/INVALID/NO_REFERENCE -> UNRESOLVED; LOW_SCENARIO_DIVERSITY blocks SPECIFIC | | | | | | |
| F-D13 | Metric weighting and uncertainty: pooled, family-level, family-balanced; bootstrap unit | paired family bootstrap on primary map, extended map as sensitivity; report per-family tables; no topology-level inference | | | | | | |
| F-D17 | Freeze configs/frozen_evaluation_config.yaml from the candidate spec once all F/Y decisions are recorded | freeze only after Y-D01..Y-D08 and F-D01..F-D16 | | | | | | |
| A-D01 | RQ1 feasibility: D(x) incremental value beyond C/M/H at matched coverage | TESTABLE_WITH_RESTRICTIONS (pooled C vs C-D, family-paired; per-class descriptive) | | | | | | |
| A-D02 | RQ2 feasibility: reproducible SPECIFIC / AMBIGUITY_SET / UNRESOLVED outcomes | TESTABLE_WITH_RESTRICTIONS (outcome rates and reproducibility); 'meaningful' ambiguity sets EXPLORATORY | | | | | | |
| A-D03 | Scope of generalisation: held-out withdrawal topology of one simulated network | accept: 'generalisation to an unseen withdrawal topology of the H2-SimNet simulated network' | | | | | | |
| A-D04 | Practical-significance threshold (plan candidate: 25% relative risk reduction) - accept, change, or report effect sizes only; must be fixed before any outer-test run | effect sizes only, unless both approve a justified threshold now | | | | | | |
| A-D05 | Final class definitions (joint with Y-D05d, Y-D06a, F-D05) | as candidate | | | | | | |
| A-D06 | Dataset description corrections: files vs runs, clean vs noise-added, 1 s verified for Parquet, H2 fraction UNVERIFIED, exclusions | adopt | | | | | | |
| A-D07 | Mathematical consistency sign-off (p, q, D, C, M, H, coverage, risk, sets, thresholds vs code) | sign off after review | | | | | | |
| A-D08 | Adopt the claim and limitation register | adopt | | | | | | |
| A-D09 | Documentation reconciliation: README sections 2/6/7, FIGURE_SPECIFICATION.md, fate of quarantined illustrative figures | own rewrite using the claim register; keep quarantine until README is fixed | | | | | | |
| A-D10 | Re-record Gates 1-3 in GATE_DECISIONS.md and adopt plan status vocabulary in MASTER_TASK_REGISTER.csv | re-record from Phase 2-4 evidence after Yazan/Faisal decisions | | | | | | |
| A-D11 | Add the authoritative New Plan 2 PDFs to assets/ | add | | | | | | |

## User (1 decisions)

| ID | Question | Recommended (not a decision) | Selected option | Approver | Date | Artifact hash/version | Conditions | Evidence ref |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G-D01 | Approve the proposed local commit plan (no push) | approve | | | | | | |

