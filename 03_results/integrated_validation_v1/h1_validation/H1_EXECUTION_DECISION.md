# H1 execution decision record

- **Prepared:** 2026-11-18, branch `research/integrated-validation`, base `6eddd4a`.
- **Scope:** decide which H1 analyses are eligible now, which need owner approval, and which need new independent evidence. Written before any figure or report in `h1_validation/`.
- **Numbers:** every figure below is reproduced by `scripts/h1_analysis.py`. Its 161 verification checks against the frozen R2 outputs all match (`analysis/h1_verification.csv`).

## 1. Exact hypothesis (unchanged)

> **H1.** At matched specific-diagnosis coverage, incorporating the proposed event-distinguishability assessment into the diagnostic decision policy will reduce empirical selective diagnostic risk compared with a calibrated classifier using conventional confidence-based abstention on held-out pipeline scenarios.

**Registered operationalisation** (`02_methodology/STATISTICAL_ANALYSIS_PLAN.md`):

- Δ = R_sel(s_C) − R_sel(s_C−D) at rank-matched coverage (PA-1), primary policy.
  - Target 0.80; 0.60 and 0.90 are secondary.
  - s_C = logistic P(correct | logit confidence, margin, −entropy, D(x)); s_C−D is identical without D(x).
  - Both share folds, probabilities, eligibility flags and decision rules.
- **Independence unit:** Scenario_Family_ID.
- **Pooling rule:** a pooled result exists only if both methods are estimable in every outer fold.

## 2. Registered experiment status (not changed here)

**R2** (run key `a10530f1fcf2…`, config `f788b6d8…`) is **NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL** for all 12 primary-comparison rows of `R2/rq1.csv` (6 per policy variant):

- 3 targets × 2 modes × 2 policy variants;
- `implementation_error_found = False` in every row of `rq1_pooled_reasons.csv`.

**H1 is therefore NOT_ESTIMABLE under the registered protocol.** No later analysis replaces this verdict.

## 3. Root causes of non-estimability (observed vs hypothesised)

| Code | Candidate cause | Status | Evidence (all verified) |
|---|---|---|---|
| A | Target above attainable coverage | **Observed, binding** | Rank-matched mode. Test maximum attainable coverage is 0.258 (Center), 0.722 (Downstream) and 0.736 (Upstream), so 0.60 is unattainable in Center and 0.80/0.90 in every fold. |
| E | Development thresholds unattainable | **Observed, binding** (threshold-transfer mode) | Development maximum attainable coverage is 0.569, 0.000054 and 0.035 by fold. |
| C | Too few independent families in the neighbourhood | **Observed, mechanism of A/E** | The specific-blocking flags TOP_CLASS_FEW_INDEPENDENT_RUNS (fewer than 2 families of the top class among the k = 25 neighbours) and LOW_SCENARIO_DIVERSITY (fewer than 2 scenarios) block 74.2 % of Center windows. The 39 per-topology families derive from **17 scenario ancestors** shared by all three topologies. |
| F | Label or attribution errors | **Observed, dominant upstream cause** | 36/57 runs carry the other topology's source model (D1 pending). 7,347 of 8,012 classifier errors (91.7 %) lie in disputed runs. The remaining 665 (one undisputed Downstream NORMAL run) are a by-product of the swapped training composition (Experiment F: 99.5 % jointly). |
| H | Errors concentrated by topology | **Observed** | Center LEAK → NORMAL (7,307 windows, 13 runs) plus Downstream NORMAL → LEAK (662). Upstream has 0 errors. |
| B | Class distribution | **Observed, contributing** | LEAK is 78.3 % of windows. DELAY and NORMAL have 1 run per topology and 1 ancestor each. |
| G | Over-conservative decision rule | **By design, not a defect** | The flag-blocking rule is registered. Relaxing flags to reach a target is prohibited. |
| D | Calibration | **Not a cause** | Calibration was feasible in all folds (2 groups per class). The identity map ("none") was selected in all three folds. |
| I | D(x) duplicates confidence | **Observed at development level** | Protocol 2.0 arm G1: s_C = s_C−D = confidence = 0.091 group-balanced risk. On R2 rankings, Spearman(D, confidence) is 0.02–0.69, so D is not identical, but it showed no development risk gain. |
| J | Formal D(Y) restricted classifications | **Not applicable to R2** | D(Y) is not part of the R2 policy. |
| K | Dataset cannot support the comparison even with correct code | **Observed for the registered target** | 13 families per stratum, 17 ancestors in total, and thin classes. Reaching 0.80 requires ≥ 80 % of each held-out topology's windows to have ≥ 2 independent top-class families among their neighbours. |

**Causal chain (observed):**

1. Source-folder swap (F).
2. Confidently wrong Center predictions and anomalous neighbourhoods (H).
3. Neighbours drawn from a single family or scenario (C).
4. SPECIFIC blocked for 74 % of Center windows.
5. Attainable coverage 0.258 < 0.60 (A).
6. Pooled RQ1 not estimable.

The registered target structure (A, E) and thin, replicated scenarios (B, K) make the 0.80 target unattainable even in Downstream and Upstream, which are not limited by the swap. Correcting labels alone would therefore not make the registered 0.80 contrast estimable (Protocol 2.0 arm B lost the registrable target: flag-free share 0.136).

## 4. Available diagnostic data and eligible labels

- **R2 window predictions.** 27,993 windows; frozen `predictions.parquet` SHA-256 `4338c8c9…`, `decisions.parquet` `1f457927…`. Pinned in `03_results/diagnostics/PRIMARY_a10530f1fcf2/DIAGNOSTICS_MANIFEST.json`; kept outside Git.
  - **Labels:** NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY, as in the registered manifest v0.2. Topology attribution is disputed for 36 runs.
- **Independent units.**
  - Per topology: 17 runs, 13 families, 17 ancestors.
  - Pooled: 51 runs, 39 families, **17 ancestors**.
  - All outer-test windows were inspected in R2. **No untouched partition exists.**
- **Center (controlled simulation).** 6 queries; 672 conditional D(Y) cells (6 queries × 7 bound scenarios × 4 sensor groups × 2 clock bounds × 2 universes).
  - The 7 scenarios, 4 groups and 2 clocks are **repeated views of the same captures**, not independent trials.
- **MHC and HY2RES.** No fault, leak or location labels, so neither can enter an H1 comparison.

## 5. Matched-coverage feasibility

- **Registered targets:** unattainable (Section 3).
- **Shared attainable region (primary variant):** [0, 0.258], identical for all six methods (asserted in R2).
- **Exploratory grid:** {0.05, 0.10, 0.15, 0.20, 0.25}, fixed by `tools/experiments/diagnose_primary_run.py` before this analysis. It is reused unchanged, and no point was chosen by outcome.
- **At each grid point:** 1,401–6,999 SPECIFIC calls and 0–1,019 errors for s_C.
- **Discordant errors** between s_C and s_C−D arise from **1–3 families (1–3 ancestors)**.

## 6. Baseline comparators

All comparators share predictions, eligibility and the tie key.

| Comparator | Role | Information |
|---|---|---|
| s_C−D | Registered primary | Same as s_C minus D(x) |
| confidence, margin, −entropy | Registered secondary | Classifier probabilities only, with the evidence guard |
| D_only | Registered secondary | Neighbourhood statistic only |
| confidence without evidence guard | **New exploratory baseline**: the "conventional confidence-based abstention" named in H1 | Classifier probabilities only. No support flags. Same eligible windows and coverage |

## 7. Status of D(x) and D(Y)

- **D(x):** the empirical kNN class-proportion margin (k = 25, own-family excluded). It is implemented and tested.
  - Development ablation: no incremental value.
  - R2: no gain outside disputed runs (Section 9).
- **D(Y):** the formal set-membership triple (H_consistent, H_excluded, H_indeterminate) under **conditional hypothetical bounds** on Center only.
  - Full universe: 336/336 UNRESOLVED.
  - Restricted universe: 59 SPECIFIC, of which 48 correct and 11 wrong. All 11 wrong decisions have an unsupported true hypothesis.
  - It cannot be compared with a classifier on independent scenarios, because no qualified bounds and no classifier on the same queries exist.

## 8. Eligibility decisions

| Analysis | Decision | Reason |
|---|---|---|
| H1-01 re-read registered RQ1 | **Eligible, run** | Read-only |
| H1-02 attainable coverage per fold | **Eligible, run** | Recomputed from frozen predictions |
| H1-03 D(x) redundancy (development ablation + R2 score AUROC) | **Eligible, run** | Existing artifacts |
| H1-04 exploratory shared-coverage comparison | **Eligible, run, EXPLORATORY_POST_HOC** | Fixed grid; inspected windows |
| H1-05 error attribution by run attribution, family and ancestor | **Eligible, run** | Uses the forensic table only as a stratifier, never as a label change |
| H1-06 D(Y) library completeness | **Eligible, run** | Existing conditional results |
| RQ3 three-outcome validity | **Eligible, run** | Registered decisions, folds 2–3 |
| Corrected-attribution replication (Experiment F) | **Blocked: needs D1 = B by Yazan plus written authorization** | D1 `NOT_RECORDED` (`P2_0_RC1.yaml`) |
| Protocol 2.0 confirmatory run | **Blocked: needs D1, D2, owner sign-offs and independent data** | Status `RELEASE_CANDIDATE_P2_0_RC1_NOT_APPROVED` |
| Any H1 confirmation | **Needs new independent evidence** | All windows inspected; 17 ancestors |

**Minimum approval to unblock the replication:** Yazan records D1 = B (adopt manifest v0.3). The project lead then writes an `EXPLORATORY_REPLICATION` authorization naming `run_primary_protocol.py`, manifest v0.3 and config `f788b6d8…` with only the topology column changed. Outputs are as in `03_results/validation/center_evidence_enhancement/EXPERIMENT_F_PROPOSAL.md`, plus `analysis/h1_05_paired_comparisons.csv` recomputed on the replication.

**What the replication can show:** whether a shared nontrivial coverage region and nonzero errors exist once attribution is corrected. **What it cannot show:** a confirmation of H1.

## 9. Recommended minimal analysis (executed) and expected outputs

- **Run:** `scripts/h1_analysis.py --r2-run <frozen R2 dir>`. It first verifies the R2 hashes.
- **Outputs** (`analysis/`):
  - `h1_01` registered RQ1;
  - `h1_02` feasibility and independence units;
  - `h1_03` redundancy;
  - `h1_04` selections;
  - `h1_05` paired comparisons with family- and ancestor-level bootstrap intervals and attribution decomposition;
  - `h1_06` three-outcome validity;
  - `h1_07` D(Y) completeness;
  - `h1_verification.csv`.

## 10. Success and stop criteria (fixed before writing results)

**Exploratory support** for the registered contrast (s_C vs s_C−D) would require **all** of the following:

1. Δ_R < 0 at every shared grid point.
2. Family- and ancestor-level 95 % intervals excluding 0.
3. Discordant errors spread over ≥ 3 ancestors.
4. A nonzero risk difference among windows from undisputed runs.

**Outcome rules:**

- If (4) cannot be met because neither policy errs outside disputed runs, the contrast carries no information beyond the attribution defect. It is reported as **INCONCLUSIVE / EXPLORATORY EVIDENCE ONLY**.
- The registered verdict stays NOT_ESTIMABLE in every case.
- **Stop criteria:** no new classifier, threshold, target, salt or label is introduced. If any reproduced count differs from the frozen output, analysis stops (assertions in the script).

## 11. Contribution even if H1 remains unproven

- An exact causal account of non-estimability.
- A quantified demonstration that the evidence-support guard withheld 78 % of classifier errors that conventional confidence abstention would have issued. This is exploratory and confounded by the attribution defect.
- Proof on Center that an incomplete hypothesis library turns set-membership decisions into wrong SPECIFIC decisions, and that the full declared universe prevents it.
- A minimum-requirements specification for a confirmatory study (`H1_CONFIRMATION_REQUIREMENTS.md`).
