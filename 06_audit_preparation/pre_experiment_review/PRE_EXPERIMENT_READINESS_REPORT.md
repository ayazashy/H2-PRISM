# Pre-Experiment Readiness Report: CANDIDATE_NOT_APPROVED

## Verdict

The **technical preparation is complete for review**. **Primary experiments are not yet authorisable**: they require the owner decisions in `TEAM_APPROVAL_PACKAGE.md` and an explicit user authorisation.

| Area | Implemented | Tested | Independently verified on raw data | Pending scientific approval | Blocked |
| --- | --- | --- | --- | --- | --- |
| Canonical inventory and realizations | ✔ `dataset_manifest.py` + builder | ✔ 11 unit tests | ✔ 242 files, 57 runs, all relationships explained | Yazan | — |
| Duplicate / misfiled reconciliation | ✔ | ✔ regression test | ✔ SHA-256 | Yazan | — |
| Scenario families (3 views) | ✔ | ✔ | ✔ 0/1,083 cross-topology shared rows; 12 weak/strong dependence edges | Yazan (view choice; 19 unresolved) | — |
| Label and timing corrections | ✔ (interpretations, raw labels untouched) | ✔ | ✔ row-level | Yazan + Ahmed (L1–L8) | — |
| Candidate outer / inner folds | ✔ | ✔ 0 issues, 3 views | ✔ byte-identity isolation | Faisal (design), Ahmed (estimand) | — |
| Cross-platform determinism | ✔ | ✔ 13/13 identical hashes | ✔ (Windows; simulated POSIX inputs) | — | — |
| Interface compatibility F3–F9, A12–A16 | ✔ (one fix: Timestamp index) | ✔ real-file windowing/features; synthetic model paths | partly (no model run, by design) | Faisal | — |
| Full window/feature table | ✗ | — | — | — | Faisal decisions F-A, F-C |
| Frozen evaluation config | ✗ | — | — | — | F-B, Ahmed A-B |
| Any model run on real data | ✗ (not authorised) | — | — | — | user authorisation and the freezes above |

## Remaining scientific issues

1. NORMAL, COMPRESSOR_DELAY and COMPRESSOR_FAULT rest on 3 independent runs (or weak/strong pairs) each, so per-class results are descriptive only.
2. The estimand is generalisation to an unseen topology, with only 3 topologies.
3. Annotation conflicts L1 and L2 sit in the source data.
4. The H₂ fraction is unverified.
5. Phase and event type are confounded by design.
6. The pre/post-event policy changes the NORMAL support substantially.

## Exact next actions

1. Yazan Y-A…Y-G, then manifest v0.2.
2. Faisal F-A…F-F, then `frozen_evaluation_config.yaml`.
3. Ahmed A-A…A-E, then gate re-record.
4. User authorises the next phase: build the window/feature table, then development-only F5–F9 runs.
