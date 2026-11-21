# Dataset Audit Amendment, 2026-11 (supersedes specific statements in Y1–Y7; originals preserved)

- **Status:** TECHNICAL AMENDMENT prepared by the independent review (Phases 2–10). Yazan's adoption is NOT_RECORDED.
- **Rule:** the 2026-10-30 documents in `01_dataset_audit/` stay unchanged as the historical record. Each one now opens with a pointer to this file. When a statement below conflicts with an original, **this amendment governs** for any pre-experiment or experimental use.
- **Evidence base:** the official Zenodo V2 archive `H2-SimNet-Dataset.zip` (509,236,976 bytes; MD5 `15bc64a3afc9e2990c9db66eb37617de`, equal to the Zenodo checksum), re-extracted untouched (`06_audit_preparation/RAW_DATASET_VERIFICATION_REPORT.md`, `raw_verification/`).

## A1. Y1: inherited preliminary claims (corrects `DATASET_INVENTORY.md` §2 and `Y1_AUDIT_LOG.md` step 4)

| Claim | Original status | Amended status | Corrected value and method | Evidence |
| --- | --- | --- | --- | --- |
| 121 files | REFUTED ("265 physical files") | **REVISED (scope)** | The clean subtree `H2-SimNet-clean/` holds exactly 121 tabular files. The archive holds **264** files; the 265th in the original list is a local `.gitkeep` | RAW_DATASET_VERIFICATION_REPORT §3; `raw_verification/CHECKSUM_RECONCILIATION.csv` |
| 60 CSV / 61 Parquet | REFUTED | **REVISED (scope)** | 60 CSV + 61 Parquet in the clean subtree; 123 CSV / 119 Parquet across both release trees | same |
| ≈2.42 M rows | not assessed | **CONFIRMED (clean subtree)** | 2,420,000 rows in the clean subtree | same |
| ~1 s sampling | CONFIRMED ("all timestamps advance by exactly 1.0 s") | **REVISED** | Parquet files store a 1.0 s `Timestamp` index (VERIFIED for every modelling file). The 6 MATLAB solver CSVs have dt 0.8 or 0.9 s; most CSVs carry no time column | `raw_verification/TIME_AXIS_AUDIT.csv` |
| No temperature channels | CONFIRMED | CONFIRMED | unchanged | — |
| PS1–PS12 MPa, MFS1–MFS4 kg/s | VERIFIED_FROM_DOCS | VERIFIED_FROM_DOCS | unchanged; units are documentary, not measured | — |
| ~10% H2 / 90% CH4 | REPORTED_UNVERIFIED | REPORTED_UNVERIFIED | unchanged; no blend-percentage claim is permitted | — |
| Checksums (`raw_checksums.sha256`, 265 lines) | VERIFIED | **SUPERSEDED for the archive** | 256 lines match the official bytes; 8 are hashes of the same files after CRLF→LF conversion in the local copy; 1 is `.gitkeep` (not in the archive). Authoritative list: `06_audit_preparation/phase8_execution_readiness/RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256` (264 entries), re-verified 264/264 on 2026-11-11. The original file is kept byte-for-byte because the sample-data validator still uses it | CHECKSUM_RECONCILIATION.csv |
| Gate 1 PASS (2026-10-30) | PASS | **Engineering re-verification PASS; attestation pending** | see `00_governance/GATE_DECISIONS.md` (2026-11-11 section) | — |

## A2. Y2–Y5, Y7: superseded statements

| Document | Original statement | Amended statement | Evidence |
| --- | --- | --- | --- |
| `SCENARIO_FAMILY_REPORT.md`, `DATASET_SCENARIO_MAP.csv` | 58 configurations / 13 families. Families merge the same event label across topologies; IDs come from paths | **57 underlying runs** (one Scenario_ID per run, two realizations each); **39 primary families**, all nested in topology. Cross-topology merges are not supported by signals (0 shared pre-event segments across topologies) | manifest v0.2 (`36bcbaf9…`); `pre_experiment_review/FAMILY_RELATIONSHIP_EVIDENCE.csv` |
| `SCENARIO_INDEPENDENCE_AUDIT.md` | Independence established | `SCEN_UNKNOWN_UNKNOWN_LEAKG4` ≡ `SCEN_UPSTREAM_TRANSIENT_LEAKG4` (byte-identical, ISS-02), resolved by run identity. **Simulation ancestry of 19 run pairs is UNRESOLVED** (Y-D03) | RAW_DATASET_VERIFICATION_REPORT §6 |
| `PHASE_AND_LABEL_DISTRIBUTION.md`, `PHASE_CONFOUNDING_REPORT.md` | Phase from directory names; compressor files "Steady State" | Directory phase is wrong for compressor files (onset row 25; ISS-23). Phase is **not** used as a model input (`phase_used=False`). COMPRESSOR_DELAY eligible windows all fall in the start-up segment (median window start 480 s) | `pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md`; Phase-9 read-only scan |
| `LABEL_MAPPING_SPEC.md`, `class_mapping.yaml` | `Leak` is the umbrella of `leak_G*`; compound rule partly inconsistent | `brokenC1G5_weak`: `leak_G5` is active while `Leak=0` (annotation conflict → **excluded**). `leakG5G6_overlapped` is labelled G4+G6 (**no location analysis**). CompressorDelay label ends at row 1000 (post-delay rows **excluded**). `leakG4brokenC1` is a compound (**excluded**). Authoritative mapping: `pre_experiment_review/CANDIDATE_LABEL_MAPPING.yaml` (`61a3182b…`) | LABEL_CONSISTENCY.csv; manifest exclusion_reason |
| `SPLIT_FEASIBILITY_REPORT.md`, `DATA_LEAKAGE_ASSESSMENT.md`, `folds.csv` | 3-fold topology-stratified CV with "zero leakage"; LOFO "mathematically invalid" | `folds.csv` put every family on both sides of every fold (ISS-01) and lists 2 files per scenario (ISS-04). Authoritative folds: leave-one-topology-out `pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv` (`3b21d823…`), validated with 0 family/topology/run overlap. The LOFO conclusion came from families equated with classes | `06_audit_preparation/FOLD_VALIDATION_SUMMARY.csv`; preflight 26/26 |
| `DATASET_READINESS_REPORT.md` | READY_WITH_EXCLUSIONS on the old map | **READY_WITH_EXCLUSIONS (restricted)** on manifest v0.2: pooled LOTO primary; NORMAL/FAULT/DELAY per-class results descriptive only; LEAK restricted; no location, field or blend claims | `YAZAN_TECHNICAL_ACCEPTANCE_PACKAGE.md` |

## A3. Unresolved source-data ambiguities (kept as restrictions; no ground truth invented)

| ID | Ambiguity | Handling |
| --- | --- | --- |
| Y-D03 | Shared simulation ancestry of 19 run pairs | Primary map keeps them separate; `family_extended_sensitivity` merges them (registered sensitivity analysis `extended_family_map`) |
| Y-D05a | `leakG5G6_overlapped` location labels | No location analysis |
| Y-D05b | `brokenC1G5_weak` annotation conflict | Excluded (3 runs) |
| Y-D06a | CompressorDelay label ends at row 1000 although the ReadME says anomalies persist | Post-delay rows excluded; DELAY descriptive only |
| — | Compound `leakG4brokenC1` | Excluded (3 runs) |
| — | H2 blend percentage, units | REPORTED_UNVERIFIED / VERIFIED_FROM_DOCS only |
