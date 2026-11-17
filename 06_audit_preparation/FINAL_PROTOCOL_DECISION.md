# Final Protocol Decision (Phase 7) - PROTOCOL_SELECTED_PENDING_EXECUTION

Basis: the project lead's explicit delegation of protocol selection (Phase 7 instruction). **No individual owner signature (Yazan, Faisal, Ahmed) is recorded or implied.** Source-data uncertainties remain open and are handled by the restrictions below. Configuration: `FINAL_EXPERIMENT_CONFIG.yaml` (sha256 `b9f44ad7afc0dd1ce75dbfcafcf457c6c0ef8e395b678703f9ea12e90e2162b9`).

Counts: NOT_APPLICABLE 1, REQUIRES_NAMED_OWNER_SIGNOFF 7, RESTRICTED_DUE_TO_SOURCE_EVIDENCE 4, SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION 32.

Owner-signoff items are governance actions (code review, contract amendment, checksum regeneration, documentation, gate records, assets). They do not change any protocol value, but they must be completed or explicitly waived by the project lead before execution starts.

## Critical estimability finding (F-D11/F-D12)

LEAK is 78.3% of the eligible 60 s/30 s windows in every topology (`phase4_approvals/evidence/WINDOW_OPTION_PER_RUN.csv`). In development, NORMAL/FAULT/DELAY have one reference family, so `TOP_CLASS_FEW_INDEPENDENT_RUNS` blocks SPECIFIC for them. The 0.80 and 0.90 targets are therefore **expected NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL** in development; 0.60 is expected estimable. The safeguard is kept, the 0.80 primary target is not changed, and a warning-only policy is registered **only** as a secondary sensitivity analysis fixed before any outer-test evaluation.

| ID | Owner | Priority | Phase-7 status | Selected protocol value / restriction |
| --- | --- | --- | --- | --- |
| A-D04 | Ahmed+Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | effect sizes only (config) |
| A-D05 | Ahmed | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | candidate class definitions consistent across v0.2, label mapping and config |
| A-D10 | Ahmed | P0 | REQUIRES_NAMED_OWNER_SIGNOFF | gate re-record after Y/F signoff |
| F-D01 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | noise_added primary, clean secondary, pooling forbidden (config + feature_table.py) |
| F-D02 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | LOTO folds pinned in config |
| F-D03 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | LOTO_within_train pinned in config |
| F-D04 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | 60/30, min_samples 60; 60/60 sensitivity |
| F-D05 | Faisal+Yazan+Ahmed | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | exclude primary; label_normal secondary |
| F-D06 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | 128 features; 80 offset-invariant sensitivity |
| F-D07 | Faisal+Ahmed | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | pooled primary; NORMAL/FAULT/DELAY descriptive only |
| F-D08 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | k=25 uniform; new TOP_CLASS_FEW_INDEPENDENT_RUNS flag implemented and tested |
| F-D10 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | src/h2prism/combined_score.py cross-fitted meta-model implemented and tested |
| F-D11 | Faisal+Ahmed | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | p-only, singleton->UNRESOLVED, max 2; blocking flags incl. TOP_CLASS_FEW_INDEPENDENT_RUNS (consequence documented) |
| F-D12 | Faisal | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | 0.80 primary target from plan F10; unattainable coverage reported, never forced |
| F-D15 | Faisal | P0 | REQUIRES_NAMED_OWNER_SIGNOFF | all modules tested; human code review pending |
| F-D17 | Faisal+Ahmed | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | CANDIDATE_EVALUATION_CONFIG.yaml complete; no open value, every block PENDING_HUMAN_SIGNOFF |
| Y-D01 | Yazan | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | 57 runs / 51 eligible encoded in CANDIDATE_MANIFEST_V02.csv |
| Y-D05b | Yazan | P0 | RESTRICTED_DUE_TO_SOURCE_EVIDENCE | brokenC1G5_weak excluded |
| Y-D05d | Yazan+Ahmed | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | 15 multi-location leak runs mapped to LEAK in v0.2 |
| Y-D06a | Yazan+Faisal+Ahmed | P0 | RESTRICTED_DUE_TO_SOURCE_EVIDENCE | post-delay rows excluded, not relabelled |
| Y-D07 | Yazan | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | CANDIDATE_MANIFEST_V02.csv built deterministically (sha256 36bcbaf9...) |
| Y-D08 | Yazan | P0 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | READY_WITH_EXCLUSIONS (restricted) - see YAZAN_RESOLUTION.md A6 |
| A-D01 | Ahmed | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | RQ1 testable with restrictions; inference protocol in AHMED_RESOLUTION.md |
| A-D02 | Ahmed | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | RQ2 operational criteria defined before experiments |
| A-D03 | Ahmed | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | scope: unseen withdrawal topology of the simulated network |
| A-D07 | Ahmed | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | code/method consistency re-verified incl. combined score |
| F-D09 | Faisal | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | candidates none/sigmoid; calibration_feasibility fallback implemented and tested |
| F-D13 | Faisal+Ahmed | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | src/h2prism/uncertainty.py stratified paired family bootstrap implemented and tested |
| F-D14 | Faisal | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | plan RF grid, seed 20261104 |
| F-D16 | Faisal | P1 | REQUIRES_NAMED_OWNER_SIGNOFF | contract amendments listed in MODEL_AND_EXPERIMENT_READINESS.md |
| F-D18 | Faisal | P1 | REQUIRES_NAMED_OWNER_SIGNOFF | A12-A16 tested; acceptance pending |
| Y-D02 | Yazan | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | 60/60 clean-vs-noise relations; one realization per run enforced in feature_table.py |
| Y-D03 | Yazan | P1 | RESTRICTED_DUE_TO_SOURCE_EVIDENCE | interim map: primary separate / extended merged; ancestry unknown |
| Y-D04 | Yazan | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | Scenario_Family_ID = family_primary in v0.2; extended/conservative columns for sensitivity |
| Y-D05c | Yazan | P1 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | Compound runs excluded in v0.2 |
| A-D06 | Ahmed | P2 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | dataset description text prepared |
| A-D08 | Ahmed | P2 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | SCIENTIFIC_LIMITATIONS_AND_CLAIMS.md |
| Y-D06b | Yazan | P2 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | phase_used=False; onset_s recorded |
| Y-D09 | Yazan | P2 | SELECTED_BY_PROJECT_LEAD_PROTOCOL_DELEGATION | src/h2prism/dataset_manifest.py is the reference builder |
| Y-D10 | Yazan | P2 | REQUIRES_NAMED_OWNER_SIGNOFF | CRLF->LF cause verified; regeneration is Yazan's action |
| A-D09 | Ahmed | P3 | REQUIRES_NAMED_OWNER_SIGNOFF | replacement text for README 2/6/7 and FIGURE_SPECIFICATION prepared, not applied |
| A-D11 | Ahmed | P3 | REQUIRES_NAMED_OWNER_SIGNOFF | Plan 2 PDFs exist outside repo; adding them is Ahmed's action |
| G-D01 | User | P3 | NOT_APPLICABLE | User explicitly approved the 4-commit plan (executed) and the LF fix commit |
| Y-D05a | Yazan | P3 | RESTRICTED_DUE_TO_SOURCE_EVIDENCE | no location analysis for leakG5G6 |

## Amendment PA-1: matched-coverage tie rule (Phase 9, before any outer-test evaluation)

- **Config:** `FINAL_EXPERIMENT_CONFIG.yaml` is now `final-protocol-1.1`, sha256 `f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae`. The only change from 1.0 (`b9f44ad7…`) is the new `thresholds.matched_coverage` block.
- **Problem:** Random Forest probabilities often saturate (many outer-test windows share one score). The 1.0 implementation accepted ties together, so in rank-matched mode s_C and s_C−D could be compared at different realized coverages. In the synthetic run they were 0.45 and 0.55 at target 0.30. That breaks the matched-coverage estimand of RQ1.
- **Alternatives evaluated (on design grounds and synthetic evidence only; no real outer-test data exists):**
  - A. Exact-count selection with a deterministic, label-free tie key: coverage is identical by construction, which matches plan F10 step 86 ("select target fraction without labels").
  - B. Tie-group inclusion with realized-coverage reporting and NOT_ESTIMABLE when coverages differ: with saturated scores, B would make RQ1 non-estimable or unmatched in most folds, and it does not realize the stated estimand.
- **Selected: A for rank-matched mode** (primary RQ1).
  - Unit: window.
  - Denominator n: all eligible windows of the outer-test fold.
  - Requested count: m = ceil(target·n).
  - Eligible for selection: finite score, valid probabilities, and no unresolved or specific-blocking flag under the evaluated policy variant.
  - Order: score descending, then SHA-256(`h2prism-pa1-v1|window_id`) ascending. A salted hash is used because raw identifiers encode run, class and topology order (a lexicographic key would be biased; see `tests/test_tie_policy.py::test_hash_key_avoids_identifier_order_bias`).
  - The same key is used for every method.
  - If m exceeds the eligible count, the result is NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL. Coverage is never forced.
- **Threshold-transfer mode is unchanged.** A deployable threshold cannot split ties; realized coverage is reported.
- **Tie-order sensitivity (secondary, reported, never used for selection):** 20 alternative salts. The pooled risk difference is reported per salt in `tie_sensitivity.csv`.
- **Status:** RECORDED_PENDING_OWNER_ACCEPTANCE (Faisal, F10). This does not change the research questions, data, folds, models, safeguards or targets.
