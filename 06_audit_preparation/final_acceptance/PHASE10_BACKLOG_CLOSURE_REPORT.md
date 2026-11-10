# Phase 10: Pre-Experiment Backlog Closure (consolidated final report)

**Verdict: `PRE_EXPERIMENT_TECHNICALLY_COMPLETE`**
**`PRIMARY_EXECUTION_AUTHORIZED: NO`**: no authorization file exists, and four required governance clearances are unrecorded. The runner refuses execution (tested).

No primary experiment was run. No research result exists. Raw data are unchanged.

## 1. Task inventory and denominator reconciliation

- **Original plans** (`assets/Yazan new plan.pdf`, `assets/Faisal New Plan 2.pdf`, `assets/Ahmed New Plan 2.pdf`): **37 tasks**, namely Yazan Y1–Y8 (8), Faisal F1–F13 (13) and Ahmed A1–A16 (16).
- **Phase 9 denominators (9 + 15 + 14 = 38) counted matrix rows, not tasks:**
  - 37 tasks, plus 3 split rows (F3 code/specs, F5 code/results, F10 runner/results), plus 3 added plan requirements that are not numbered tasks (Yazan §4 Gates 1–3, Yazan §5 risk register, the registered sensitivity analyses) = 43 rows;
  - minus 5 NOT_APPLICABLE rows (Y6, F5-results, F10-results, A8, A11) = 38.
- **Phase 10 matrix (`TEAM_PLAN_COMPLETION_MATRIX.csv`, rebuilt):** 58 requirement rows covering all 37 tasks. Each task is split into pre-experiment deliverables, owner attestations and post-experiment outputs, so that results that cannot yet exist are not counted as failures.

| Owner | Rows | VERIFIED_PRE_EXPERIMENT_COMPLETE | PRE_EXPERIMENT_INCOMPLETE | POST_EXPERIMENT_DEPENDENCY | HUMAN_ATTESTATION_REQUIRED | NOT_APPLICABLE_WITH_EVIDENCE |
| --- | --- | --- | --- | --- | --- | --- |
| Yazan (8 tasks) | 13 | 8 | 0 | 0 | 4 | 1 (Y6 → A10) |
| Faisal (13 tasks) | 22 | 13 | 0 | 5 | 4 | 0 |
| Ahmed (16 tasks) | 23 | 14 | 0 | 7 | 2 | 0 |
| **Total (37 tasks)** | **58** | **35** | **0** | **12** | **10** | **1** |

Pre-experiment technical deliverables: Yazan 8/8, Faisal 13/13, Ahmed 14/14. These are counts of matrix rows, each with evidence checked by `tests/test_plan_deliverables.py`. They are not percentages of the projects.

## 2. Preparation work closed in Phase 10

- **Yazan:**
  - `01_dataset_audit/DATASET_AUDIT_AMENDMENT_2026-11.md` supersedes the refuted Y1–Y7 statements; 13 originals keep their text behind a pointer banner.
  - `00_governance/RISK_REGISTER.csv`: 17 plan risks with the plan fields.
  - Checksum and provenance reconciliation (264/264; 256 + 8 CRLF + 1 `.gitkeep`).
  - `YAZAN_TECHNICAL_ACCEPTANCE_PACKAGE.md`: READY_WITH_EXCLUSIONS (restricted) recommendation, with the ambiguities preserved.
- **Faisal:**
  - 16 named specifications in `02_methodology/`, written from the code: preprocessing, windowing, features, baseline, calibration, D(x) math / edge cases / design decision, comparators, ambiguity sets, pseudocode, thresholds, SAP, grouped evaluation, fold validation, sensitivity.
  - `configs/frozen_evaluation_config.yaml` (hash-checked pointer).
  - `00_governance/TECHNICAL_INTEGRATION_ARCHITECTURE_FREEZE.md`.
  - `04_validation/` (3 reports).
  - Contract updated to v2.0.0 schemas.
- **Ahmed:**
  - A1, A2, A3 (3 documents), A4, A5 (template, table spec, figure spec v2, provenance register), A6, A7, A10 (3 documents), A12 report, A13 spec and build manifest, A14–A16 split specs.
  - README reconciled: 3 local absolute links removed; stale test count, folds, blend and confounding statements corrected; experiment status added.
  - Task register moved to the plan vocabulary.

## 3. Software changes (all tested)

| Change | Why |
| --- | --- |
| Execution paths for the 9 registered sensitivity analyses (`SENSITIVITY_OVERRIDES`; `--sensitivity`, `--execute-sensitivity`; scope `SENSITIVITY_EXPERIMENT:<name>`) | registered in the protocol but not runnable |
| `pre_event_label_normal` keeps post-event windows excluded | `windows.py` `label_normal` also relabelled post-event rows, which would have changed two choices at once |
| Preflight: family-column check; pinned inner folds must equal the runner's derived splits (28 checks) | the pinned inner-fold file was never verified against what the runner actually uses |
| Outputs: `n_families`; `calibration_reliability.csv`; per-fold `calibration_selection.csv` | F6 results and the T_RQ1 family count had no output path |
| Reporting: config bound to runner outputs with row filters; synthetic runner outputs → illustrative; effects and outcome-share figure kinds | A13 referenced files the runner never writes |
| A12 spec checks manifest v0.2 against contract v2 | it validated the superseded v0.1 manifest against the new contract |

The pinned config `f788b6d8…` is unchanged. Folds, features, labels, safeguards, PA-1 and all registered comparisons are preserved.

## 4. Nine sensitivity analyses

| Analysis | Path | Synthetic E2E | Real structural dry run (no fitting) |
| --- | --- | --- | --- |
| clean_realization | `--execute-robustness` / `--execute-sensitivity` | pass | 27/27 checks; 27,993 windows |
| windows_60_60 | `--execute-sensitivity` | pass | 27/27; 14,013 |
| pre_event_label_normal | same | pass, plus a relabelling test | 27/27; 31,929 (1,893 post-event dropped) |
| offset_invariant_features | same | pass (80 features) | 27/27; 80 features |
| k_10 / k_50 | same | pass | 27/27 each |
| prior_correction | same | pass | 27/27 |
| extended_family_map | same | pass | 27/27 (32 families, nested) |
| policy_warning_only | embedded in every run | pass | n/a |

The dry runs predate the 28th check (`inner_folds_match_runner`); the primary dry run passes 28/28.

## 5. Scientific limitations (recorded; no protocol change)

- **L1:** only three topologies; results are conditional.
- **L5 run fingerprint:** absolute-level features nearly identify the run (median η² 0.99). Interpret with `offset_invariant_features`.
- **L6:** COMPRESSOR_DELAY is confounded with the start-up phase; descriptive only.
- **L3/L4:** thin classes; LEAK 78.3%.
- **L7:** unknown ancestry of 19 pairs.
- **L2:** simulation only.

Full list: `05_documentation/DATASET_LIMITATIONS.md` and `SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md`.

## 6. Validation (final run after all code changes)

| Check | Result |
| --- | --- |
| Compile | COMPILE_OK |
| Full test suite | **289 passed, 2 skipped, 0 failed** (291 collected). Skips: sample-data fallback, which is exercised only when raw data are absent |
| A12 candidate spec / plan spec | 33/33 PASS / 36 PASS + 1 MISSING_ARTIFACT (`03_results/BASELINE_PREDICTIONS.parquet`, post-experiment) |
| Real-data preflight (read-only) | PREFLIGHT_PASSED 28/28; feature table `4d1310a6…`; config `f788b6d8…` |
| `03_results/` after the suite | unchanged; no `03_results/primary_protocol/` |
| Deterministic regeneration | feature table `4d1310a6…` reproduced; byte-identical resume and reorder tests |

## 7. Outstanding

- **Technical defects:** none known.
- **Execution-blocking human items** (runner-enforced via `governance_clearance`):
  - F-D15: Faisal code acceptance.
  - F-D16: Faisal contract v2 acceptance.
  - A-D10: Ahmed/Yazan Gate 1–3 attestation.
  - PA-1: Faisal or project-lead acceptance.
- **Non-blocking human items:**
  - Y4 mapping reviews.
  - Y7 readiness decision.
  - Yazan adoption of the amendment, checksums and risk register.
  - F-D18 (A12–A16 acceptance, plus the A14 inner-scheme freeze).
  - Ahmed's approval of the A1–A7/A10 drafts.
- **Project-lead delegation:** covers protocol selection only, as recorded in Phase 7. No named-owner sign-off or waiver was created.
- **Post-experiment** (12 rows): F5/F6/F10/F11/F13 results; A5 final figures; A8; A9 freeze report; A11; A14–A16 results.

**Next action:** owners attest, or the project lead waives in writing. The project lead then writes `EXECUTION_AUTHORIZATION_PRIMARY.yaml` (see `NEXT_PHASE_EXECUTION_HANDOFF.md`).
