# Final Code and Method Audit (Phase 9, independent technical review for F-D15)

- **Scope:** `baseline.py`, `calibration.py`, `distinguishability.py`, `combined_score.py`, `comparators.py`, `policy.py`, `metrics.py`, `uncertainty.py`, `features.py`, `feature_table.py`, `windows.py`, `experiments/primary_protocol.py`, `tools/experiments/run_primary_protocol.py`, `scripts/visualize.py` (test side effects).
- **Reviewed against:** the original plans (`assets/*Plan*.pdf`) and `FINAL_EXPERIMENT_CONFIG.yaml`.
- This is not Faisal's sign-off.

## 1. Verified defects fixed in Phase 9 (each with a test)

| # | Defect | Consequence if unfixed | Fix | Test |
| --- | --- | --- | --- | --- |
| D1 | Rank matching accepted every window tied with the m-th score | s_C and s_C−D were compared at different coverages (synthetic: 0.45 vs 0.55 at target 0.30). That confounds the primary RQ1 estimand and departs from plan F10 step 86 ("select target fraction") | Protocol amendment PA-1: `exact_count_selection`, with ties broken by a salted SHA-256 window_id key. The runner asserts identical SPECIFIC counts per fold | `tests/test_tie_policy.py` (17); `test_rank_matched_coverage_is_exactly_matched` |
| D2 | RQ1 computed only s_C vs s_C−D | Plan F10 requires C vs B (confidence) and the secondary indicators; config `secondary_comparisons` had no output (protocol/implementation mismatch) | `COMPARISONS` covers s_C vs s_C−D (PRIMARY), confidence (C vs B), margin, −H and D-only | `test_rq1_reports_every_registered_comparison_without_omission` |
| D3 | A variant/target/mode that was non-estimable in every fold produced **no RQ1 row** | Silent omission of NOT_ESTIMABLE results | RQ1 now enumerates every registered combination; numeric fields stay empty, never 0 | same |
| D4 | Resume key lacked code identity | After a code change, stale fold outputs could be reused | `run_key` includes `code_sha256` (CRLF-normalised hash of the package) | `test_deterministic_and_resumable` |
| D5 | An output directory holding another run was reused | Partial or old aggregate CSVs could sit beside a new run manifest | Refused with PreflightError ("different run") | `test_output_dir_of_a_different_run_is_refused` |
| D6 | Non-finite features and duplicate window_id were not checked before modelling | A late crash inside the D(x) fit, or non-deterministic tie keys | Preflight fails closed on both (real data: 0 non-finite values, ids unique) | real preflight 26/26; tie tests |
| D7 | RQ2 per-class reporting labels were hard-coded | Divergence from `evaluation.per_class_reporting` | Read from config | `test_rq2_reporting_labels_come_from_config` |
| D8 | `test_visualize_cli_runner` wrote illustrative figures into the tracked `03_results/` (ISS-18) | Synthetic/illustrative files in the genuine results directory on every test run | `H2PRISM_VISUALIZE_OUT` redirect; the test writes to `tmp_path` | full suite leaves `03_results/` clean |

Phase 8 fixes (still verified): manifest v0.2 aliasing; provenance columns excluded from features; flag-only availability mask.

## 2. Component review (no further defect found)

| Component | Checked | Result |
| --- | --- | --- |
| Baseline selection | Inner grouped split by topology; macro-F1, then log-loss tie-break; grid from config | OK |
| Calibration | Feasibility fallback; selection on development OOF; cross-fitted calibrated development probabilities; final calibrator applied to the outer test only | OK |
| D(x) | Standardisation fitted on the reference only; own-family exclusion; OOS quantile fitted on the reference; flags enforced | OK. **Limitation:** the development reference is one topology, while the test-time reference is both development topologies (larger support at test time) |
| Combined score | Cross-fitted by topology on development; final model applied without refit | OK |
| Thresholds | Development OOF only; NOT_ESTIMABLE when unattainable; realized development coverage now recorded | OK |
| Policy and decisions | SPECIFIC only if selected or ≥ τ and not flagged; ambiguity size 2..K−1; no specific label on other outcomes (asserted) | OK |
| Metrics | Coverage over all eligible windows; risk undefined when n_specific = 0 (not 0) | OK |
| Family bootstrap | Unit = Scenario_Family_ID, strata = topology, paired; strata with one unit held fixed with a warning | OK |
| Provenance and serialization | config/code/feature hashes, git commit, seed; LF CSV/JSON with fixed float format; artifact_class on every table | OK |
| Execution gate | Authorization YAML bound to the config SHA-256 and scope; exit code 2 on refusal; dry run is the default | OK |

## 3. Leakage audit (16 boundaries)

| # | Boundary | Finding |
| --- | --- | --- |
| 1 | Duplicate raw files across folds | 0 duplicate hashes among 57 runs × 2 realizations. The ISS-02 byte duplicate is resolved by one Scenario_ID per run |
| 2 | Clean/noisy realizations | One realization per run; both realizations of a run share its fold, so no cross-fold pairing is possible |
| 3 | Shared simulation ancestry | Unknown (Y-D03). Families nest in topology and LOTO holds out whole topologies, so any within-topology ancestry stays on one side |
| 4 | Window overlap | 60/30 windows overlap only within a run; windows never span runs; runs never span folds |
| 5 | Topology identity | Held out entirely (LOTO). 4 absolute-level features have topology η² > 0.5 → transfer risk, not leakage |
| 6 | Family identity | Asserted disjoint between development and test (runner + preflight) |
| 7 | Normalisation / imputation | None fitted globally; D(x) scaling is fitted on the reference; RF needs none; non-finite values fail closed |
| 8 | Feature selection | None (fixed 128 registered features) |
| 9 | Calibration | Development OOF only |
| 10 | Threshold tuning | Development only; label-free rank matching on test |
| 11 | D(x) reference | Development windows only; own family excluded |
| 12 | Cross-fitting | Topology-grouped in development |
| 13 | Combined-score fitting | Development OOF only |
| 14 | Model comparisons | Same windows, same folds, same eligibility; exact matched counts |
| 15 | Bootstrap units | Families, paired, stratified by topology |
| 16 | Aggregation | Pooled only when every fold is estimable; outer labels used only for scoring. Shuffled outer labels give identical decisions (test) |

**Validity risks (not leakage; the protocol is unchanged, so they are reported):**
- **Run fingerprint:** absolute-level features almost identify the run within a topology (median η² 0.99 for `__mean` features). The model can learn run-specific operating levels. The registered `offset_invariant_features` sensitivity analysis addresses this.
- **DELAY confounding:** COMPRESSOR_DELAY windows all come from the start-up segment (median window start 480 s, against about 10,000 s for the other classes), so the DELAY class is confounded with run phase. It is already descriptive-only.

## 4. Scientific consistency

- **RQ1 (C vs C−D at matched coverage)** is now implemented as the plan states. C vs B and the other indicators are secondary. Inference is effect sizes with family-bootstrap CIs, with no significance claims (config `inference: effect_sizes_only`).
- **RQ2:** per-class SPECIFIC / AMBIGUITY / UNRESOLVED rates; LEAK is "restricted"; other classes descriptive only.
- **Estimability:** 0.80 and 0.90 under the primary policy are expected NOT_ESTIMABLE (LEAK 78.3%; flags block thin-class tops). This is reported, never forced.
- **Unsupported claims** (embedded in every run manifest): industrial readiness, field validation, generalisation beyond the 3 simulated topologies, physical identifiability, metric leak localisation, pure-hydrogen performance, a verified blend %, and D(x) superiority beyond the reported effects.
- **Remaining gaps:**
  - 7 of the 9 registered sensitivity analyses have no runner path yet. Not needed for the primary run.
  - The ancestry, location and annotation evidence gaps are permanent restrictions.
