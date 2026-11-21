# Final Governance and Gate Record (Phase 9)

- **Verification date:** 2026-11-11.
- **Reviewer:** the independent engineering and methodology review (AI-assisted), working under the project lead's Phase-7 delegation for protocol selection.
- That delegation **does not** authorise signatures. No Yazan, Faisal or Ahmed attestation is recorded or implied anywhere in this package.

## 1. Governance items from Phase 7/8

| ID | Technical work (evidence) | Status | Remaining named action |
| --- | --- | --- | --- |
| Y-D10 | `phase8_execution_readiness/RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256` re-verified on 2026-11-11: 264/264 match the untouched extract (`sha256sum -c`). Yazan's `01_dataset_audit/raw_checksums.sha256` is unchanged since `b9a0560` (preserved) | TECHNICALLY_CLOSED | Yazan adopts it (replace, or annotate the original) |
| A-D11 | `assets/Ahmed New Plan 2.pdf` `0d838036…` and `assets/Faisal New Plan 2.pdf` `ce419091…` match the Phase-4 record. No raw data, archive or parquet file was added on this branch (`git diff --name-only 13c5512 HEAD`) | TECHNICALLY_CLOSED | Ahmed acknowledges |
| F-D15 | Independent code review done (`FINAL_CODE_AND_METHOD_AUDIT.md`): 6 defects fixed, each with tests; full suite passes | REQUIRES_HUMAN_ATTESTATION | **Faisal accepts the code, or the project lead waives in writing** |
| F-D16 | `configs/interface_contracts.yaml` v2.0.0 now matches the implementation and is enforced by `tests/test_interface_contract.py` (5 tests). Change logged as CC-005 | REQUIRES_HUMAN_ATTESTATION | **Faisal accepts contract v2, or the project lead waives** |
| F-D18 | A12 33/33; A13–A16 tests pass | REQUIRES_HUMAN_ATTESTATION | Faisal accepts A12–A16. This does not block the primary run |
| A-D09 | Replacement text exists (`phase6_resolution/AHMED_RESOLUTION.md` C5); `FIGURE_SPECIFICATION.md` is still stale | OPEN (owner) | Ahmed applies it before any publication. Does not block execution |
| A-D10 | Gates 1–3 re-verified from evidence (below); section appended to `00_governance/GATE_DECISIONS.md` | REQUIRES_HUMAN_ATTESTATION | **Ahmed (and Yazan as gate owner) attest, or the project lead waives** |
| PA-1 | Matched-coverage tie rule pre-registered in config 1.1 (`f788b6d8…`) and recorded in `FINAL_PROTOCOL_DECISION.md` | RECORDED_PENDING_OWNER_ACCEPTANCE | Faisal (F10 owner) accepts, or the project lead approves under the delegation |

## 2. Gate re-verification (engineering evidence only)

Decision rules are from the Yazan plan §4.

| Gate | Required checks (plan) | Evidence (re-run 2026-11-11) | Engineering result | Deviations / dependencies |
| --- | --- | --- | --- | --- |
| 1 Dataset Integrity | File audit, checksums, duplicates, channels, sampling and missingness | Archive MD5 `15bc64a3…`; 264/264 SHA-256; manifest file hashes are checked per run inside the preflight (51/51 noise_added and 51/51 clean); 16 channels; 1 s parquet index; 0 non-finite features; 0 duplicate raw hashes; 0 duplicate feature vectors | **PASS** | Y1 documents keep refuted claims (ISS-05/06/08/21); text-only |
| 2 Scenario and Label Validity | Scenario map, relationship evidence, overlap, frozen mapping | Manifest v0.2 (`36bcbaf9…`): 57 runs, 51 eligible, 4 classes, 39 primary families nested in topology, 6 exclusions with reasons; label mapping pinned (`61a3182b…`) | **CONDITIONAL** (restricted) | Ancestry unknown (Y-D03); location and annotation evidence insufficient (Y-D05a/b, Y-D06a), so there are no location claims and compound runs are excluded |
| 3 Evaluation Feasibility | Family-class table, fold feasibility, leakage, exact folds | Preflight fold checks: exact coverage, family and topology isolation; runner `assert_group_disjoint` on family, topology and run; inner LOTO within training | **CONDITIONAL** (pooled primary; per-class NORMAL/FAULT/DELAY descriptive only) | 1 NORMAL, 1 DELAY and 2 FAULT runs per test fold (ISS-20); DELAY is confounded with start-up phase |

**Reviewer authority.** These are engineering checks. Gate decisions belong to Yazan, with re-recording by Ahmed under A-D10, so the attestation fields stay **PENDING**.

## 3. What would clear the governance blockers

Either of these two routes is enough:
1. **Named attestations:** Faisal for F-D15, F-D16 and PA-1; Ahmed and Yazan for A-D10, recorded with names and dates in `phase5_decisions/*_SIGNOFF.md` or `GATE_DECISIONS.md`.
2. **Explicit written waiver by the project lead** that names each item. The project lead's authorization file can carry it (see `NEXT_PHASE_EXECUTION_HANDOFF.md`).
