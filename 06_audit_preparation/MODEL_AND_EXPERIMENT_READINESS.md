# Model and Experiment Readiness

Legend: SPECIFIED, IMPLEMENTED, TESTED (synthetic), EXECUTED, VALIDATED, FROZEN, BLOCKED. **No component is VALIDATED or FROZEN.**

## Component readiness and traceability (supports A6; RQ → method → code → config → test → execution → result)

| RQ | Component | Definition | Code | Config | Tests | Executed on project data | Result | Status | Blocking dependency |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RQ1, RQ2 | Loading and validation | `io.py` docstring | `src/h2prism/io.py`, `data/loader.py` | — | test_io (6), loader (7) | Samples only | — | TESTED | Canonical tree (ISS-04); sampling source (ISS-06) |
| RQ1, RQ2 | Windowing and eligibility | `windows.py`, problem formulation §3 | `src/h2prism/windows.py` | `WindowConfig` (required arguments) | test_windows (11) | No | — | TESTED | Window/stride justification; `label_mode`; `pre_event_policy` (Y4) |
| RQ1, RQ2 | Features | `FEATURE_DEFINITION_REGISTER.csv` (128 candidates) | `src/h2prism/features.py` | — | test_features (5) | No | — | TESTED | Faisal feature-set decision; a one-command builder over the manifest is not written |
| RQ1, RQ2 | Grouped evaluation | Plan F4 | `src/h2prism/splits.py` | `frozen_evaluation_config.yaml` **missing** | test_splits (7) | Validator on `folds.csv` → **FAIL** | — | BLOCKED | Y2/Y5 correction, then the F4 decision |
| RQ1 | RF baseline | Plan F5 grid | `src/h2prism/baseline.py` | `rf_param_grid()` | test_baseline (6) | No | — | TESTED | F3 table, F4 folds |
| RQ1 | Calibration | Plan F6 | `src/h2prism/calibration.py` | criterion argument | test_baseline (2) | No | — | TESTED | F5 inner OOF |
| RQ1 | q(x), D(x) | `D_STATISTIC_IMPLEMENTATION_SPEC.md` | `src/h2prism/distinguishability.py` | `DConfig` (flag defaults PROVISIONAL) | test_distinguishability (17) | No | — | TESTED | k / weighting / flag decisions; real-data dominance check |
| RQ1 | C, M, H | Symbol register | `src/h2prism/comparators.py` | — | test_comparators (6) | No | — | TESTED | Faisal sign-off |
| RQ1 | s_C, s_{C−D} meta-model | Plan F10 | **not implemented** | — | — | No | — | NOT_STARTED | F5–F8 outputs; cross-fitting design |
| RQ2 | Three-outcome policy | `SELECTIVE_DIAGNOSTIC_POLICY.md` | `src/h2prism/policy.py` | `PolicyConfig` | test_policy (11) | No | — | TESTED | Development threshold procedure |
| RQ1 | Coverage, risk, matched coverage | Plan F10 step 89 | `src/h2prism/metrics.py` | — | test_metrics (8) | No | — | TESTED | — |
| RQ1 | Family bootstrap, paired differences | Plan F11 | **not implemented** | — | — | No | — | NOT_STARTED | F10 |
| support | LR reference (A14) | Spec A14 | `secondary_baseline.py` | `secondary_baseline.yaml` | 5 | No | — | TESTED | F3/F4; Faisal acceptance |
| support | Feature sensitivity (A15) | Spec A15 | `experiments/feature_sensitivity.py` | `feature_sensitivity.yaml` | 3 | No | — | TESTED | Arm approval; F3/F4 |
| support | Supporting ablations (A16) | Spec A16 | `experiments/supporting_ablations.py` | dev `PolicyConfig` | 5 | No | — | TESTED | F9 thresholds, F10 freeze |
| support | Artifact validation (A12) | Tool docstring | `tools/research_audit/*` | `artifact_validation.yaml` | 6 | **Yes** (repository artifacts) | 28 PASS / 2 MISSING / 1 status FAIL | EXECUTED | Faisal schema acceptance |
| support | Reporting (A13) | Tool docstring | `tools/reporting/*` | `reporting_figures.yaml` | 6 | Dry run (inputs absent) | NOT_BUILT | TESTED | F6/F10 outputs |

## Leakage controls now enforced in code

1. `baseline.run_grouped_evaluation` refuses any outer fold whose independence groups (default `Scenario_Family_ID`) intersect. The current `folds.csv` is therefore **rejected**, which is the intended behaviour.
2. Inner model selection uses only outer-training rows. A test perturbs the outer-test features and checks that selection and inner OOF are byte-identical.
3. Scaling for LR and D is fitted on training/reference rows only (tested).
4. D excludes the query family; the query label is not an argument; reference rows come from outer-train only.
5. The policy refuses thresholds unless `threshold_source == "development"`, and never receives `y_true`.
6. Metadata columns cannot be model features (`assert_no_metadata_features`).
7. Window manifests that would double-count exports are flagged (`check_window_manifest`).

## Proposed F12 contract amendments (for Faisal's decision; not applied)

- `manifest_schema`: add `label_raw`, `label_mapped`, `n_rows`, `event_timing_status`, `canonical_tree` (per the plan's F12 core contract).
- `window_manifest_schema`: add `file_id`, `n_samples`, `label_mode`, `time_source`, and the boundary values `NO_EVENT` and `UNKNOWN_TIMING` (file-level labels cannot support boundary claims).
- `prediction_table_schema`: add `p_raw_<k>`, `p_calibrated_<k>`, `q_<k>`, `support_flags`, `run_status`, `missing_train_classes`, `params`, `seed`.

## Can primary experiments begin?

**No.** The blocking chain is: Y2 correction (Scenario_IDs from content, evidence-based families, canonical tree) → Y5 regeneration → F4 design decision and frozen config (with Ahmed's approval) → F3 feature table from the frozen manifest → F5/F6/F7 development runs → F9 thresholds on development data → F10 freeze → outer test.
Development work on the provisional package is possible now, but only with corrected, family-disjoint development folds and outputs labelled DEVELOPMENT_ONLY.
