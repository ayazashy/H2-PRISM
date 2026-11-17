# Yazan Technical Acceptance Package (Y1–Y8, Gates 1–3)

- **Prepared:** 2026-11-11 by the independent technical review.
- **Yazan attestation: NOT_RECORDED.** This package gathers the evidence Yazan needs to accept or reject. It is not his signature.

## 1. Verified dataset facts (re-run 2026-11-11)

| Item | Value | Verification |
| --- | --- | --- |
| Source | Zenodo V2 `H2-SimNet-Dataset.zip`, MD5 `15bc64a3…` (= Zenodo) | `raw_verification/ZENODO_SOURCE_PROVENANCE.json` |
| Archive files | 264; all match `RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256` | `sha256sum -c` 264/264 |
| Underlying runs | 57 (each in a clean and a noise-added realization; 57/57 unique hashes per realization; no hash shared across realizations) | manifest v0.2 |
| Eligible runs | 51 = per topology NORMAL 1, LEAK 13, COMPRESSOR_FAULT 2, COMPRESSOR_DELAY 1 | preflight `eligible_count` |
| Excluded runs | 6: `brokenC1G5_weak` ×3 (annotation conflict), `leakG4brokenC1` ×3 (simultaneous events) | `exclusion_reason` |
| Families | 39 primary (13 per topology), all nested in topology; extended map 32; conservative 3 | preflight `families_nest_in_topology` |
| Eligible windows (60 s / 30 s) | 27,993 per realization: NORMAL 1,995, LEAK 21,921, FAULT 3,984, DELAY 93 | preflight (noise_added `4d1310a6…`, clean `3bc7e712…`) |
| Missing values in features | 0 non-finite | preflight |
| Duplicates | 0 duplicate feature vectors; no window spans two runs | Phase-9 read-only scan |
| Folds | LOTO, 3 folds, every class in every train/test fold, 0 family/topology/run overlap | preflight fold checks |
| Deterministic rebuild | feature-table hash identical across the Phase 8 and Phase 9 rebuilds; `tools/dataset/build_manifest_v02.py` reproduces the manifest | Phase-8/9 evidence |

## 2. Requirement-by-requirement status

| Task | Plan acceptance criterion | Evidence | Technical status |
| --- | --- | --- | --- |
| Y1 | Each prior claim CONFIRMED/REFUTED/REVISED/UNVERIFIED with values and method | `DATASET_AUDIT_AMENDMENT_2026-11.md` §A1 (corrected statuses); original files preserved behind amendment banners | complete (amended) |
| Y2 | A reviewer can reconstruct every family assignment; uncertainties explicit | `pre_experiment_review/CANDIDATE_FAMILY_MAP.csv`, `FAMILY_RELATIONSHIP_EVIDENCE.csv`; ancestry of 19 pairs unresolved (Y-D03) | complete with restriction; Ahmed's sample review NOT_RECORDED |
| Y3 | Phase source, topology source, granularity and timing status per scenario; boundary feasibility explicit | manifest v0.2 `timing_status`, `onset_s`, `delay_last_active_s`, `phase_used`; `LABEL_AND_TIMING_CORRECTIONS.md`; DELAY/start-up confounding recorded | complete with limitation |
| Y4 | Every label mapped, kept as secondary, or excluded with a reason; mutual exclusivity evidenced | `CANDIDATE_LABEL_MAPPING.yaml` (`61a3182b…`); 6 exclusions with reasons | complete with restriction (Y-D05a/b) |
| Y5 | Folds executable from saved definitions; supportable, descriptive-only and unevaluable claims identified | `CANDIDATE_OUTER_FOLDS.csv`, `CANDIDATE_INNER_FOLDS.csv`, `EVALUATION_FEASIBILITY_REPORT.md`; preflight | complete |
| Y6 | Transferred to Ahmed (A10); Yazan supplies evidence | evidence supplied; see `05_documentation/DATA_PROVENANCE.md` | not applicable (transferred) |
| Y7 | Task-specific readiness decision supported by an evidence table | §3 below | **technical recommendation ready; Yazan decision NOT_RECORDED** |
| Y8 | Versioned provisional package | `01_dataset_audit/provisional/` v0.1, superseded by v0.2 (CHANGE_CONTROL_LOG CC-001) | complete |
| Risk register | Every risk has a mitigation or a documented consequence | `00_governance/RISK_REGISTER.csv` (17 risks, plan fields) | complete; owner confirmation pending |
| Gates 1–3 | Plan §4 decision rules | Gate 1 PASS; Gates 2–3 CONDITIONAL (`00_governance/GATE_DECISIONS.md`) | **attestation NOT_RECORDED** |

## 3. Readiness decision (Y7), evidence-backed recommendation

**READY_WITH_EXCLUSIONS (restricted).** Defensible primary task:
- 4-class window attribution;
- pooled leave-one-topology-out evaluation on noise-added data;
- the clean realization as a separate robustness run, never pooled.

| Analysis | Status |
| --- | --- |
| Pooled RQ1 (C vs C−D at matched coverage) | supportable, with effect sizes conditional on 3 simulated topologies |
| Per-class NORMAL / FAULT / DELAY | descriptive only (1–2 runs per topology) |
| LEAK per-class | restricted |
| DELAY as an event (separate from start-up) | unevaluable |
| Leak location (G3–G6) | unevaluable |
| Field, industrial or blend-percentage claims | unsupported |

## 4. Action required from Yazan

Accept or amend the following, with name and date:
- `DATASET_AUDIT_AMENDMENT_2026-11.md`;
- the readiness decision above;
- the Gate 1–3 records;
- the risk register.

Adopt `RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256` as the archive checksum list (Y-D10).
