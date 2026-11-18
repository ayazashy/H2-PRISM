# H1 research report — Methods

## M1. Data and frozen inputs

| Input | Identity | Role |
|---|---|---|
| R2 window predictions | `predictions.parquet`, SHA-256 `4338c8c9ececc477212043ba890812b3163e0f7ef16d10c567fb4161c0103098` | probabilities, D(x), support flags, the six registered scores, fold, family |
| R2 decisions | `decisions.parquet`, SHA-256 `1f4579271b8fa5ec11d4950cf1e19c4f5eb73c552e7f831cbb1d418b70862c86` | registered three-outcome decisions (0.60, folds 2–3) |
| Configuration | `06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml`, SHA-256 `f788b6d8…` | policy variants, tie key, bootstrap settings |
| Forensic attribution | `03_results/diagnostics/forensics/source_model_attribution.csv` | per run: is the source model consistent with the manifest topology? |
| Development ablation | `03_results/ablation/ARM_SUMMARY.csv` | Protocol 2.0 arms A–G2 |
| Center D(Y) | `03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json` | 672 conditional decisions |

**Data handling.** The two parquet files are kept outside Git. The analysis refuses to run unless their hashes equal those pinned in `03_results/diagnostics/PRIMARY_a10530f1fcf2/DIAGNOSTICS_MANIFEST.json`, and the run manifest is COMPLETED from the pinned configuration.

## M2. Definitions

- **Notation.** For window i in outer fold f:
  - ŷ_i = argmax_c p_cal,c(x_i) (calibration selected the identity map in every fold);
  - correctness 1[ŷ_i = y_i].
- **Eligibility.** E_f = windows with a finite score and no unresolving or specific-blocking flag under the policy variant (`pp._available`).
  - Primary variant: OUT_OF_SUPPORT, INVALID_FEATURES and NO_REFERENCE unresolve; LOW_SCENARIO_DIVERSITY and TOP_CLASS_FEW_INDEPENDENT_RUNS block SPECIFIC.
- **Coverage.** C = Σ a_i / N_f, with N_f = all windows of the fold. The attainable maximum is |E_f| / N_f.
- **Selective risk.** R_sel = Σ a_i 1[ŷ_i ≠ y_i] / Σ a_i. It is undefined (never 0) when Σ a_i = 0.
- **Rank-matched exact-count selection (PA-1).**
  - Requested count: m = ⌈c · N_f⌉.
  - Order: score descending, then SHA-256(`h2prism-pa1-v1|window_id`) ascending.
  - Not estimable if m > |E_f|.
  - Identical counts for every method.
- **Paired difference.** Δ_R(c) = R_sel(s_C) − R_sel(comparator). Negative favours s_C.
- **D(x)** (`02_methodology/DISTINGUISHABILITY_MATHEMATICAL_SPEC.md`):
  - D(x) = q₍₁₎(x) − q₍₂₎(x), where q(x) is the class-proportion vector of the k = 25 nearest development windows (z-scored features), excluding the query's own family.
  - s_C = logistic P(correct | logit confidence, margin, −entropy, D). s_C−D drops D.
- **Conventional baseline (exploratory).**
  - Confidence = max p_cal, selected with the same exact count from all windows with a finite score.
  - No support flags. This is the "conventional confidence-based abstention" named in H1.
- **Scenario ancestor.** Scenario_ID with the topology token removed. The same template is simulated in all three topologies.
  - Reproduces the forensic independence table exactly: LEAK 13, COMPRESSOR_FAULT 2, COMPRESSOR_DELAY 1, NORMAL 1.
- **Attribution status.** A window is "disputed" if its run's inferred source model differs from the manifest topology.
  - This is a stratifier only. No label is changed.

## M3. Procedures

1. **H1-01:** re-read `rq1.csv` and `rq1_pooled_reasons.csv`; assert every primary row is NOT_ESTIMABLE.
2. **H1-02:** recompute |E_f|/N_f per fold and variant. Verify against `estimability.csv` (tolerance 1e-9, CSV precision). Count runs, families and ancestors.
3. **H1-04:** for c ∈ {0.05, 0.10, 0.15, 0.20, 0.25}, select per fold for the six registered scores and the conventional baseline.
   - This grid is fixed in `tools/experiments/diagnose_primary_run.py`. It is the largest regular grid inside the shared attainable region [0, 0.258] and was not chosen from outcomes.
   - Every count is verified against `risk_coverage_curve.csv` and `exploratory_guard_effect.csv`.
4. **H1-05 paired comparisons and uncertainty:**
   - **(a)** The registered paired topology-stratified family bootstrap (`h2prism.uncertainty.paired_stratified_bootstrap`, 2,000 replicates, seed 20261104, 95 % percentile). Reproduces `exploratory_shared_coverage.csv` exactly.
   - **(b)** The same with scenario ancestors (17 units, single stratum).
   - **(c)** The standard deviation of the ancestor bootstrap (planning input only).
   - **(d)** Selection overlap and discordant errors.
   - **(e)** Errors among windows from undisputed runs, with selections held fixed.
5. **Error capture:** classifier errors split into blocked by flags, eligible but not accepted, and accepted.
6. **H1-03:**
   - Spearman correlations, verified against `dx_association.csv`.
   - Correctness AUROC of each score (Mann–Whitney with average ranks) on all windows and on eligible windows.
   - Re-read of the development ablation.
7. **RQ3:** registered s_C decisions at 0.60 (folds 2–3), per topology × class.
   - Specific errors, ambiguity inclusion and size, unresolved reason tokens, classifier error rate per outcome.
   - Totals verified against `rq2.csv`.
8. **H1-06:** D(Y) decision counts by universe × sensor group × clock bound.
   - Assertion: no wrong SPECIFIC has a supported true hypothesis.

## M4. Inference policy

- No p-values and no significance claims (as in the registered SAP).
- Intervals are percentile bootstrap intervals conditional on the observed strata. They are **post hoc** and cannot confirm H1, because every window was inspected in R2.
- The ancestor-level interval is reported beside the registered family-level interval because the families are not independent across topologies.

## M5. What was not done

- **Not re-run or changed:**
  - no model was trained, refit or recalibrated;
  - no threshold, flag rule, target, salt or label was changed;
  - no frozen file was written.
- **Not run because it is blocked:**
  - the corrected-attribution replication (D1 not recorded);
  - Protocol 2.0 (not approved).
