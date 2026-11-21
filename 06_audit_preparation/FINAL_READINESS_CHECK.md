# Final Readiness Check (Phase 7)

**Status:** PROTOCOL_SELECTED_PENDING_EXECUTION (project-lead delegation; no owner signatures recorded).

## Integration check (Phase 7; existing artifacts, no real-data model run)

| Link | Check | Result |
| --- | --- | --- |
| Manifest v0.2 ↔ config | hash `36bcbaf9…`; 51 eligible = config `eligible_runs` | ✔ `test_final_config.py` |
| Manifest ↔ folds | eligible set = fold set; families nest in topology; 0 leakage issues under 3 views | ✔ `test_candidate_package.py`, `test_candidate_config.py` |
| Labels and timing ↔ window builder | row-level labels; pre/post-event rows excluded; builder takes the config values | ✔ (Phase 3 real-file interface tests; Phase 6 builder tests) |
| Feature builder ↔ register | statistics ⊆ implemented features; register hash pinned | ✔ |
| D(x) safeguards ↔ policy | all flags exist; `TOP_CLASS_FEW_INDEPENDENT_RUNS` blocks SPECIFIC in the primary policy; warning-only variant is secondary | ✔ |
| Calibration fallback ↔ config | `calibration_feasibility`, min 2 groups, fallback "none" | ✔ |
| Combined score ↔ plan | features [logit C, M, −H, (D)], cross-fitted on development only | ✔ (Phase 6 tests) |
| Statistics ↔ claims | effect sizes only; topology-stratified family bootstrap, pooled, conditional | ✔ |
| Placeholders | no `PENDING_*` value in the final config | ✔ (test) |
| Stale references | final config pins the candidate-config hash `e4be96df…` | ✔ (test) |
| Contradictions found | none. Previously open tension (F-D11) resolved by keeping the safeguard primary and registering warning-only as secondary; 0.80/0.90 targets expected NOT_ESTIMABLE (`FINAL_PROTOCOL_DECISION.md`) | — |

## Validation executed (Phase 7)

- `pytest tests/test_final_config.py tests/test_candidate_config.py tests/test_candidate_package.py`: **23 passed**.
- `pytest tests/test_final_config.py` after the hash and cleanup edits: **4 passed**.
- Full suite not rerun: no library code changed in Phase 7 (only a new test file and configuration/documentation). Last full run: 171 passed, 2 skipped (commit `3cec445`).
- No real-data training, D evaluation, risk–coverage or benchmark was run.

## Pinned artifacts

| Artifact | SHA-256 |
| --- | --- |
| FINAL_EXPERIMENT_CONFIG.yaml | `b9f44ad7afc0dd1ce75dbfcafcf457c6c0ef8e395b678703f9ea12e90e2162b9` |
| CANDIDATE_EVALUATION_CONFIG.yaml (source) | `e4be96df29bf99c7e37a32695d83e763e5ee41765f673f79f0265f574023e208` |
| CANDIDATE_MANIFEST_V02.csv | `36bcbaf97bb17659995f393884d1dcde3bbca9236c3dcdcc6e7651e61538fb59` |
| Outer / inner folds | `3b21d823…` / `ebff65da…` |
| Label mapping / feature register | `61a3182b…` / `3dd5e927…` |

## Remaining before primary execution

1. **Explicit user authorisation** for the execution phase.
2. **The 7 owner governance items** (Y-D10, F-D15, F-D16, F-D18, A-D09, A-D10, A-D11) completed or explicitly waived by the project lead.
3. **First execution task (not done):** write the orchestration runner that chains the existing tested modules per `phase6_resolution/CANDIDATE_EXPERIMENTAL_PROTOCOL.md`. Suggested entry point: `tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml`.
   - Its first step: verify the pinned hashes, then call `h2prism.feature_table.build_feature_table(manifest_v02, data/raw, "noise_added", "Scenario_Family_ID", WindowConfig(60, 30, 60, "row_level", "exclude"), <8 statistics>)`.
   - Then run the development stage before any outer-test evaluation.
