# H₂-PRISM Research Findings Report (technical report and executive summary)

- **Status:** results of authorized real-data execution, 2026-11-11.
- **Evidence status:** PENDING. Figures and tables carry a preliminary watermark until the named owners complete PRIMARY_RESULTS_VALIDATION.
- **Scope:** the H₂-SimNet V2 simulation only (three topologies). Nothing here is a field, industrial or deployment result.

## 1. Executive summary

1. **Primary experiment.** R2 (run_key `a10530f1fcf2`) completed and passed lifecycle validation (33/33 checks). In addition, 42 of its reported summaries were recomputed independently from window-level outputs, and all 42 match.
2. **RQ1 (does D(x) add decision value beyond confidence?).** The registered test is **NOT_ESTIMABLE** at every registered target (0.60, 0.80, 0.90), in both modes and both policy variants, in R2 and in every completed sensitivity run.
   - The binding constraint is the registered support safeguards, not a comparator or an implementation error.
   - An exploratory post-hoc comparison over the coverage range attainable in all three topologies (0.05–0.25) gives s_C the lowest point risk. Its paired interval against s_C−D includes 0 at every point.
   - **No incremental value of D(x) is established.**
3. **Center transfer failure (accuracy 0.213).** Confirmed root cause: a **source-dataset inconsistency**. *Corrected by the forensic audit (`FORENSIC_FINDINGS_REPORT.md`):* the released **event folders** `anom_gestcent` and `anom_gestdown` carry each other's simulation model. The first version of this report said the two NORMAL files were swapped; the grouping of runs, and therefore every number below, is the same under both readings.
   - This explains 99.5% of all misclassified windows in R2.
   - It is not a pipeline defect. R2 and the manifest are unchanged, and the issue is referred to the dataset owner (R-18).
4. **RQ2 (three-outcome policy).** Wherever SPECIFIC was issued at the registered 0.60 operating point, it was correct (10,701 LEAK and 497 NORMAL windows). However:
   - that operating point exists only for Downstream and Upstream;
   - FAULT is never SPECIFIC there;
   - DELAY outcomes differ completely between the two topologies.

   At the exploratory shared coverage of 0.25, which includes Center, SPECIFIC decisions on Center are **wrong for LEAK** (989 of 989). The safeguards do not detect a systematic, confidently supported error.
5. **Sensitivity.** All 8 runnable registered analyses were authorized and executed. Seven completed. `offset_invariant_features` stopped in fold 3 because the registered combined-score meta-model is not estimable there; it is recorded, not patched. No analysis changes the RQ1 conclusion (Section 6).

## 2. Methodology as executed (A8)

- **Data:**
  - Manifest v0.2 (`36bcbaf9…`), 51 eligible runs, noise-added realization.
  - 27,993 windows of 300 s with 50% overlap.
  - 128 features (16 channels × 8 statistics), feature table `4d1310a6…`.
- **Evaluation:**
  - Leave-one-topology-out over 3 folds (`3b21d823…`).
  - Development-only inner selection with topology groups (`ebff65da…`).
  - Random Forest grid; calibration none/sigmoid selected on development, restricted to monotone maps.
- **Distinguishability:**
  - D(x) = top-two class-share gap among the k=25 nearest reference windows.
  - The query's family is excluded from its reference.
  - Support flags: TOP_CLASS_FEW_INDEPENDENT_RUNS (fewer than 2 families), LOW_SCENARIO_DIVERSITY (fewer than 2 runs) and OUT_OF_SUPPORT (above the 0.99 quantile).
- **Scores:**
  - s_C = logistic meta-model of development correctness on (logit C, M, −H, D).
  - s_C−D is the same model without D.
  - Comparators: confidence, margin, −entropy and D only.
- **Policy:**
  - SPECIFIC is blocked by the first two flags and UNRESOLVED is forced by OUT_OF_SUPPORT.
  - Otherwise SPECIFIC, an AMBIGUITY_SET (mass 0.9, at most 2 classes) or UNRESOLVED.
- **RQ1 estimand:**
  - Pooled selective risk s_C minus s_C−D at matched coverage 0.80 (secondary 0.60 and 0.90).
  - Rank matched by exact count with a salted SHA-256 tie key (PA-1); threshold transfer is secondary.
  - Pooled only if estimable in every fold.
  - Family bootstrap stratified by topology (2,000 resamples), with effect sizes only.
- **Config:** `06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml` (`f788b6d8…`), unchanged throughout.

## 3. Execution history and provenance

| Run | Class | Status | Use |
| --- | --- | --- | --- |
| `db9acd23ef58` (R1) | PRIMARY | **INVALID**, archived | fold 3 selected an order-reversing sigmoid calibration (100% → 0% correct). Defect found by inspecting outer-test output (disclosed); fix is a monotonicity rule plus regression test (commit `0a0a9e2`) |
| `a10530f1fcf2` (R2) | PRIMARY | COMPLETED, VALID | the primary reference. Code hash `4c3edfe4` = tree of `0a0a9e2` |
| 8 registered analyses | SENSITIVITY / ROBUSTNESS | Section 6 | secondary only; never pooled with R2 |

**Calibration disclosure:** the monotonicity rule was introduced after seeing R1's outer-test outputs. The rule does not depend on any outcome; it excludes maps that invert rankings. In R2 it selected "none" in every fold. Readers should still weigh R2 as a second, informed execution.

## 4. Center topology failure: root cause

> **Correction (forensic audit, 2026-11-11).** The table below reads the evidence as "two NORMAL runs carry the other topology's configuration". The source simulation models (`simulation_model_sensors.csv`) and export scripts show instead that the 36 event runs in `anom_gestcent`/`anom_gestdown` are exchanged; the NORMAL files match their models. The mechanism, the error counts and the consequences are unchanged. See `FORENSIC_FINDINGS_REPORT.md` section 2.

The hypotheses were tested in this order:

| Hypothesis | Verdict | Evidence |
| --- | --- | --- |
| E/F: label or topology alignment / sensor configuration | **CONFIRMED (source dataset)** | `run_fingerprint.csv`: 49 of 51 runs show their topology's configuration (Center: MFS4 active and PS4 = PS9; Downstream: MFS4 inactive and PS4 = PS8; Upstream: MFS4 inactive and PS4 = PS9). The two exceptions are the NORMAL runs: `CS_CENTER_NORMAL_RUN_NORMALITY` has the Downstream signature and `CS_DOWNSTREAM_NORMAL_RUN_NORMALITY` has the Center signature. `source_normal_files.csv`: identical in the MATLAB simulation output, the clean release and the noise-added release; the MATLAB "center" NORMAL file has no MFS4 column |
| Mechanism | **CONFIRMED** | In fold 1 training, the only Center-configured windows are NORMAL (the Downstream NORMAL run), so held-out Center LEAK windows → NORMAL: 7,307 of 7,307, median confidence 0.85. In fold 2, Downstream NORMAL (Center-configured) → LEAK: 662 of 665, median confidence 1.00. These two groups are 99.5% of all 8,012 errors (`error_attribution.csv`). Upstream is unaffected (100% correct) |
| H: implementation defect | Not found | 42/42 recomputations match; class order, folds and the feature hash are verified; the feature table rebuilds to the run's hash |
| C: absolute-level fingerprints | Not the main cause | With offset-invariant features, Center accuracy falls to 0.035 and Downstream to 0.783 (all LEAK) |
| A/B/G: shift, sparse support, training coverage | Contributing, secondary | NORMAL and DELAY have 1 run per topology and FAULT 2; Center DELAY → FAULT (31 windows) is a sparse-support error |
| D: timing confounding | Not tested further | DELAY / start-up confounding (L6) stands |

**Consequence.** Center (and partly Downstream) results measure the effect of this inconsistency, not genuine cross-topology generalisation.

- The manifest is not altered. Correcting it is the dataset owner's decision (R-18): either keep the source assignment and report it as a limitation, or make a versioned correction plus a newly authorized run.
- The swap also degrades development: inner-selection macro-F1 is 0.74, 0.30 and 0.10 in folds 1–3. Folds 2 and 3 pair Center with another topology in development.

## 5. RQ1: why it is not estimable, and what can be said

`rq1_pooled_reasons.csv` gives a reason code for every one of the 60 registered comparisons.

- **Rank matched at 0.60:** `POOLED_REQUIRES_ALL_FOLDS_TARGET_UNATTAINABLE_IN_CENTER`. Center allows at most 0.258 coverage; Downstream (0.722) and Upstream (0.736) are estimable.
- **Rank matched at 0.80 and 0.90:** `TARGET_UNATTAINABLE_IN_ALL_FOLDS`.
- **Threshold transfer:** `DEV_THRESHOLD_UNATTAINABLE_IN_ALL_FOLDS`. Development attainable coverage is 0.569, 0.000 and 0.070 by fold, because a single-topology reference cannot supply two independent families or is out of support.
- **Not the cause:**
  - comparator matching: attainable coverage is identical across all six methods;
  - ties;
  - an implementation error.
- **Binding constraint:** neighbours of a window are dominated by overlapping windows of one run. Two families appear only when another topology replicates the same scenario.
  - Center is out of step with the other topologies (L12), so only 25.8% of its windows are flag-free.
  - At test time, "independent" support therefore partly reflects cross-topology replicas of the same simulated scenario (families are defined per topology).

**Exploratory post-hoc comparison** (`exploratory_shared_coverage.csv`): coverages 0.05–0.25 are attainable in all three topologies, using the same PA-1 selection and the same family bootstrap.

| Coverage | s_C risk | s_C−D risk | Δ (95% interval) | confidence risk | Δ vs confidence (95% interval) |
| --- | --- | --- | --- | --- | --- |
| 0.10 | 0.000 | 0.100 | −0.100 [−0.365, 0.000] | 0.247 | −0.247 [−0.580, −0.003] |
| 0.15 | 0.035 | 0.169 | −0.134 [−0.317, 0.000] | 0.175 | −0.140 [−0.411, 0.067] |
| 0.20 | 0.101 | 0.190 | −0.088 [−0.213, 0.001] | 0.215 | −0.114 [−0.357, 0.143] |
| 0.25 | 0.146 | 0.152 | −0.006 [−0.049, 0.034] | 0.238 | −0.093 [−0.259, 0.029] |

How to read this table:

- The point estimates favour s_C.
- Every interval against s_C−D includes 0.
- The topology pattern is inconsistent: the s_C vs s_C−D difference comes from Center and the s_C vs confidence difference from Downstream.
- Upstream risk is 0 for every method.
- With 39 families in 3 strata, and Center affected by L12, this is **descriptive and inconclusive**. It is not a test of the registered hypothesis.

## 6. Registered sensitivity and robustness analyses

The full table is `03_results/diagnostics/CROSS_RUN_SUMMARY.csv`, and the validated runs are summarised in `03_results/primary_protocol/SENSITIVITY_SUMMARY/`.

| Analysis (run key) | Status | Windows | Accuracy C / D / U | Max attainable coverage C / D / U | Registered pooled RQ1 | Pooled risk at 0.25: s_C / s_C−D / confidence |
| --- | --- | --- | --- | --- | --- | --- |
| primary (`a10530f1fcf2`) | COMPLETED | 27,993 | 0.213 / 0.929 / 1.000 | 0.258 / 0.722 / 0.736 | NOT_ESTIMABLE (all 6) | 0.146 / 0.152 / 0.238 |
| clean_realization (`220f49ad35f9`) | COMPLETED | 27,993 | 0.378 / 0.929 / 1.000 | 0.105 / 0.328 / 0.128 | NOT_ESTIMABLE (all 6) | n.e. / n.e. / n.e. |
| windows_60_60 (`72075f284d50`) | COMPLETED | 14,013 | 0.213 / 0.929 / 1.000 | 0.260 / 0.745 / 0.760 | NOT_ESTIMABLE (all 6) | 0.146 / 0.155 / 0.239 |
| pre_event_label_normal (`105fde53d265`) | COMPLETED | 31,929 | 0.249 / 0.897 / 0.950 | 0.227 / 0.756 / 0.769 | NOT_ESTIMABLE (all 6) | n.e. / n.e. / n.e. |
| offset_invariant_features (`ff9cc78ab2ca`) | INCOMPLETE (2/3 folds) | 27,993 | 0.035 / 0.783 / — | 0.070 / 0.990 / — | — (fold 3 stopped) | — |
| k_10 (`821642d2201e`) | COMPLETED | 27,993 | 0.213 / 0.929 / 1.000 | 0.217 / 0.675 / 0.681 | NOT_ESTIMABLE (all 6) | n.e. / n.e. / n.e. |
| k_50 (`7565497cc7dd`) | COMPLETED | 27,993 | 0.213 / 0.929 / 1.000 | 0.261 / 0.759 / 0.770 | NOT_ESTIMABLE (all 6) | 0.146 / 0.157 / 0.239 |
| prior_correction (`faf07c82b108`) | COMPLETED | 27,993 | 0.213 / 0.929 / 1.000 | 0.208 / 0.718 / 0.450 | NOT_ESTIMABLE (all 6) | n.e. / n.e. / n.e. |
| extended_family_map (`4d13822c5521`) | COMPLETED | 27,993 | 0.213 / 0.929 / 1.000 | 0.258 / 0.722 / 0.737 | NOT_ESTIMABLE (all 6) | 0.146 / 0.152 / 0.238 |

Notes:

- "All 6" means rank matched and threshold transfer at 0.60, 0.80 and 0.90 (s_C vs s_C−D, primary policy).
- `policy_warning_only` is embedded in every run and is NOT_ESTIMABLE throughout.
- "n.e." means the 0.25 point is not attainable in every topology.
- The analyses with a different population (`windows_60_60`, `pre_event_label_normal`) and different units (`extended_family_map`) are not pooled with R2.

**Findings:**

- **No registered analysis makes RQ1 estimable.** The support-flag constraint binds in every variant.
- **The Center failure is stable.** Accuracy is 0.213 under every D(x) and family variant, 0.249 with pre-event NORMAL windows, and 0.378 in the clean realization.
  - Offset-invariant features make it worse (0.035; run stopped in fold 3 because the meta-model is not estimable, see `SENSITIVITY_offset_invariant_features/RUN_INCOMPLETE_NOTE.md`).
  - This matches the configuration-swap explanation (L12) rather than a feature-scaling or windowing artifact.
- **Neighbourhood size changes attainability, not the conclusion.** k=10 lowers Center attainable coverage to 0.217, so even 0.25 is not estimable; k=50 raises it slightly (0.261) and reproduces R2's exploratory pattern.
- **Windowing (60/60) reproduces R2** on half the windows.
- **The clean realization lowers attainability sharply** (0.105 / 0.328 / 0.128). This is consistent with near-duplicate noise-free windows concentrating neighbourhoods on single runs.
- **Prior correction lowers Upstream attainability** (0.450) and Center attainability (0.208); the classifier is unchanged.
- **Calibration stability:** "none" was selected in all 3 folds of every completed run (8 runs, 24 folds). Per-run records are in `calibration_records.json`.


## 7. Role of D(x) (`dx_association.csv`, `dx_selection_overlap.csv`, `exploratory_guard_effect.csv`)

- **Changes which windows are selected:** yes, strongly at low coverage. At 0.05 the s_C and s_C−D selections overlap with Jaccard 0.05; at 0.25 the overlap is 0.64. At 0.10, the 2,005 windows chosen only by s_C−D contain 281 errors; the windows chosen only by s_C contain 0.
- **Duplicates confidence:** partly. Spearman correlation between D and confidence on guard-available windows is 0.69 for Downstream and below 0.2 elsewhere.
- **Detects systematic error:** no. On Center, mean D is 0.97 on wrong windows versus 0.93 on correct ones. A reference that carries the same inconsistency produces confident, "well-supported" errors.
- **Mainly signals insufficient evidence:** the support flags, which come from the same neighbourhood machinery, matter more than D's ranking.
  - Guarded s_C risk at 0.25 is 0.146 versus 0.335 without the guard.
  - Confidence risk is 0.238 with the guard versus 0.422 without.
  - These are exploratory, not registered.
- **Answer:** D(x) reshapes selection and its support flags withhold many errors. **An incremental diagnostic value beyond confidence-based policies is not demonstrated**, under the registered test or the exploratory one.

## 8. RQ2: three-outcome accounting (`rq2_accounting.csv`)

**Registered 0.60, rank matched, primary policy** (Center absent: not estimable there):

| Topology | Class | n | SPECIFIC (correct) | AMBIGUITY_SET (true class included) | UNRESOLVED |
| --- | --- | --- | --- | --- | --- |
| Downstream | LEAK | 7,307 | 5,599 (5,599) | 0 | 1,708 |
| Downstream | NORMAL | 665 | 0 | 0 | 665 |
| Downstream | FAULT | 1,328 | 0 | 0 | 1,328 |
| Downstream | DELAY | 31 | 0 | 31 (31) | 0 |
| Upstream | LEAK | 7,307 | 5,102 (5,102) | 0 | 2,205 |
| Upstream | NORMAL | 665 | 497 (497) | 0 | 168 |
| Upstream | FAULT | 1,328 | 0 | 0 | 1,328 |
| Upstream | DELAY | 31 | 0 | 0 | 31 |

**Exploratory 0.25** (all topologies, Center included):

- Center LEAK: 989 SPECIFIC, **all wrong (NORMAL)**; 3,820 ambiguity sets, all including LEAK; 2,498 unresolved.
- Center FAULT: 658 SPECIFIC, all correct.
- Center NORMAL: 656 SPECIFIC, all correct.
- Center DELAY: 30 SPECIFIC, all wrong (FAULT).

Reading:

- A 100%-correct SPECIFIC subset is not a 100%-correct classifier. The registered RQ2 point excludes the topology on which the classifier fails.
- Conservative outcomes for FAULT, DELAY and NORMAL are driven by class-support limits: the FEW_INDEPENDENT_RUNS and LOW_DIVERSITY reason codes dominate.
- The system communicates insufficient evidence for thin classes. It does **not** communicate the systematic Center error.

## 9. Supported and unsupported conclusions

| Conclusion | Status |
| --- | --- |
| The registered RQ1 hypothesis is not testable on this dataset under the registered safeguards | SUPPORTED |
| D(x) improves selective diagnosis beyond confidence (C3) | NOT SUPPORTED (not estimable; exploratory intervals include 0) |
| SPECIFIC decisions are reliable where issued | SUPPORTED ONLY for Downstream/Upstream at 0.60; contradicted for Center at 0.25 |
| Center failure = genuine cross-topology shift | NOT SUPPORTED (source-dataset inconsistency, L12) |
| Classifier evidence reflects physical event signatures (C10) | NOT SUPPORTED (offset-invariant arm degrades; configuration differences dominate) |
| Generalisation, field validity, industrial readiness, statistical significance | UNSUPPORTED (unchanged) |

## 10. Threats to validity

- **L12 swap:** dominates the Center and Downstream results.
- **Three topologies only.**
- **Thin classes:** 1–2 runs per topology.
- **Overlapping windows:** inference is by family; families are per topology, so cross-topology replicas count as independent.
- **Disclosure:** R1 was invalidated, and the calibration rule was added after seeing outer-test output.
- **Exploratory analyses are post hoc.**
- **Simulation only.**
- **Unknown ancestry of 19 run pairs** (L7).
- **Clean versus noise-added realizations:** not interchangeable.

## 11. Methodology freeze (A9-c)

Frozen hashes:

| Artifact | Hash prefix |
| --- | --- |
| config | `f788b6d8` |
| manifest | `36bcbaf9` |
| outer folds | `3b21d823` |
| inner folds | `ebff65da` |
| label mapping | `61a3182b` |
| feature register | `3dd5e927` |
| feature table | `4d1310a6` |
| R2 code | `4c3edfe4` (commit `0a0a9e2`) |

Run keys and authorizations are in `03_results/RESULTS_INDEX.csv` and `03_results/RESULTS_PROVENANCE.csv`. Owner sign-off is not recorded.

## 12. Remaining dependencies

| Dependency | Owner |
| --- | --- |
| R-18 dataset decision | Yazan |
| PRIMARY_RESULTS_VALIDATION and evidence status | named owners |
| F-D18 and A14 secondary baseline | Faisal; separate authorization |
| Y4-b, Y7-b, Y-APPROVE, A-APPROVE approvals | named owners |
| Manuscript, poster, publication manifest (A11) | after the above |

## 13. Reproduction

```
python tools/experiments/diagnose_primary_run.py --run 03_results/primary_protocol/PRIMARY --raw-parent data/raw
python tools/experiments/summarize_runs.py
python tools/reporting/build_results.py
```
