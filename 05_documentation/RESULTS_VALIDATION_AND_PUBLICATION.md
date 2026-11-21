# Results validation and publication lifecycle (A13; 2026-11-12)

The red "PRELIMINARY … NOT A VALIDATED RESULT" watermark is a **consequence** of an artifact's lifecycle state. It is not an editable setting. It disappears only when every required owner has recorded a scoped approval bound to the artifact's exact evidence.

## 1. What was wrong with the previous mechanism

Before this change, the watermark was decided by a free-text `evidence_status` in the YAML config, or by a global `build_results.py --evidence-status VALIDATED` flag. That had three consequences:

- The flag removed the watermark from **every** artifact at once.
- No reviewer identity, claim scope or binding to the reviewed data was recorded.
- Approvals could not go stale.

The dataset artifacts (Fig. 1, T1–T3) had been placed in `final/` on a self-declared `VERIFIED` that no owner gave. They are retired, unchanged, under `*/dataset_design/superseded_unapproved_final_20261111/`.

## 2. Lifecycle

Implemented in `tools/reporting/publication.py`; policy in `configs/publication_policy.yaml`.

| State | Meaning | Output |
| --- | --- | --- |
| INVALID | source run invalid or archived invalid, or a reviewer REJECTED the claim | refused |
| EXECUTION_COMPLETED | run completed; technical validation record missing or not VALID | `preliminary/` + watermark |
| SCIENTIFIC_REVIEW_PENDING | technically validated; a required approval is missing or stale | `preliminary/` + watermark |
| SCIENTIFICALLY_VALIDATED | every required role validated the claim; publication not cleared | `preliminary/` + "validated – not approved for publication" |
| APPROVED_FOR_PUBLICATION | every required role approved publication of this exact version | `final/`, no watermark |

**Technical validation** is the lifecycle validator's VALID record for the source run (`03_results/validation/`). Dataset artifacts use their complete preflight record instead.

**Approval records** live in `06_audit_preparation/publication_approvals/<artifact>/*.yaml`. Each record states:

- reviewer name and role;
- claim scope;
- decision;
- date;
- statement;
- a **binding**:
  - SHA-256 of every source input;
  - the artifact spec, including caption and limitations;
  - the renderer source (plot function and style module, or table renderer);
  - the source run keys.

**Invalidation rule.** Any change to any bound item makes the approval STALE: it is reported as a blocker and never reused. Every build is versioned by a fingerprint of reporting code, configs, policy and approvals (`…_b<hash>`). Earlier versions are never overwritten, so the preliminary original stays next to each published version.

**Claim scopes and required roles:**

| Scope | Required approvers |
| --- | --- |
| DESCRIPTIVE | science owner |
| CONFIRMATORY | science owner + methods owner |
| DATASET | dataset owner + science owner |

Each artifact lists the scopes it may ever be approved for.

**Tests:** `tests/test_publication_workflow.py`, 16 tests:

- watermark removed after valid approval, and kept while pending;
- forged or wrong-role reviewers rejected;
- stale source data and changed captions rejected;
- tampered hashes rejected;
- missing technical validation blocks publication;
- an archived invalid run is refused;
- a rejected claim is refused;
- scope rules (confirmatory needs both owners);
- per-artifact isolation;
- a NOT_ESTIMABLE result can be published;
- deterministic regeneration.

## 3. Acceptance review of every current artifact

Source run R2 = `a10530f1fcf2`. Current build `a10530f1fcf2_s4228b6c8_b200fcdac`; preliminary original `…_b5ddfbcfa`.

| Artifact | Source | Numerical validity | Claim validity | Required approvals | Status | Watermark |
| --- | --- | --- | --- | --- | --- | --- |
| Fig. 1 dataset & design | dataset preflight | counts equal source tables (test) | topology labels follow the disputed release attribution (caption states L12/R-18) | Yazan + Ahmed (DATASET) | SCIENTIFIC_REVIEW_PENDING | **yes** |
| T1–T3 dataset tables | dataset preflight | verbatim | same as Fig. 1 | Yazan + Ahmed | SCIENTIFIC_REVIEW_PENDING | **yes** |
| Fig. 2 risk–coverage | R2 | 42/42 recomputations; per-topology axis no longer crops (regression test) | descriptive, attainable range only | Ahmed | **APPROVED_FOR_PUBLICATION** | no |
| Fig. 3 incremental value | R2 | all registered comparisons NOT_ESTIMABLE; nothing drawn | accurate, but carries no information beyond T5/T7 | Ahmed | SCIENTIFIC_REVIEW_PENDING (not recommended) | **yes** |
| Fig. 4 three-outcome | R2 derived tables | derived tables reproduce registered `rq2.csv` (9/9 cross-checks); panel tests | corrected (Section 4) | Ahmed | **APPROVED_FOR_PUBLICATION** | no |
| Fig. 5 error structure | R2 | confusion counts = R2 `confusion_matrix.csv` | corrected wording (families not independent; coinciding calibration curves stated) | Ahmed | **APPROVED_FOR_PUBLICATION** | no |
| Fig. 6 robustness | 7 VALID runs + 1 RUN_INCOMPLETE | from the sensitivity summary | accurate, all not estimable; redundant with T8 | Ahmed | SCIENTIFIC_REVIEW_PENDING (not recommended) | **yes** |
| T4, T5, T6, T6b, T6c, T7, T8, T9 | R2 / derived / summary | verbatim from validated sources; T6 cross-checked | scoped captions | Ahmed | **APPROVED_FOR_PUBLICATION** | no |

**Approvals recorded:** 11 artifacts (Fig. 2, Fig. 4, Fig. 5, T4–T9).

- Ahmed Zayed (science owner) approved them on 2026-11-12, DESCRIPTIVE scope.
- The decision was given explicitly in-session and is recorded verbatim in each approval file.

**Published files:** `03_results/PUBLICATION_MANIFEST.csv` lists every published file with its hash. Unsigned templates and the package for the remaining owners are in `06_audit_preparation/publication_signoff/`.

## 4. Fig. 4 correction evidence

| Panel | Defect | Correction | Evidence |
| --- | --- | --- | --- |
| (a) | pooled shares without population; Center silently absent at 0.60 | topologies included and excluded (with reason: Center maximum attainable 0.258) printed; windows, runs and independence groups per class; SPECIFIC / AMBIGUITY / UNRESOLVED counts | `03_results/derived/PRIMARY/rq2_scoped.csv` (POOLED_ESTIMABLE and per-topology rows); bar widths equal shares (test) |
| (b) | empty markers for undefined proportions | k/n labels; "no SPECIFIC issued: undefined" text instead of a marker; axis says "not classifier accuracy" | test: markers = 2 × classes − undefined |
| (c) | first token of a compound reason ("single candidate rejected") shown as the cause | exclusive primary reason by documented precedence (support flag before matched-coverage cut before set construction); non-exclusive reasons in T6c | FAULT 2,656 and DELAY 62 blocked by support flags; LEAK: 2,308 flags vs 1,605 matched-coverage cut; NORMAL: 32 vs 801 |
| (d) | flag rates over all topologies while (a) covered two | same evaluated topologies as (a); per-class n; overlap stated; "flag-free ≠ correct" | `support_flags_scoped.csv` (non-exclusive and exclusive combinations) |

**Values (0.60, Downstream + Upstream):**

| Class | Windows | SPECIFIC (correct) | Ambiguity sets (true class included) | Unresolved |
| --- | --- | --- | --- | --- |
| LEAK | 14,614 | 10,701 (10,701) | 0 | 3,913 |
| NORMAL | 1,330 | 497 (497), all from Upstream | 0 | 833 |
| FAULT | 2,656 | 0 | 0 | 2,656 |
| DELAY | 62 | 0 | 31 (31) | 31 |

## 5. How to approve or reject an artifact

1. Run `python tools/reporting/build_signoff_package.py`.
2. Copy `06_audit_preparation/publication_signoff/templates/<artifact>.yaml` to `06_audit_preparation/publication_approvals/<artifact>/<reviewer>.yaml`.
3. Fill in `decision`, `reviewer.name`, `reviewer.role`, `date` and `statement`. Never edit `binding`.
4. Run `python tools/reporting/build_results.py`.

The artifact moves to `final/` only if the policy's required roles are all satisfied.
