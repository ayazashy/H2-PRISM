# Mathematical and Conceptual Consistency Review (A4)

- **Status:** PRE-EXPERIMENT REVIEW performed 2026-11-11 by the technical review against code and specs. Ahmed's approval NOT_RECORDED.
- **Scope:** `02_methodology/` specs (F2, F3, F7, F8, F9, F10, F11), `configs/`, `src/h2prism/`.

## Symbol table

| Symbol | Domain / range | Defined in | Implemented in |
| --- | --- | --- | --- |
| x | ℝ^128 (ℝ^80 in the offset-invariant sensitivity), one eligible 60 s window | FEATURE_EXTRACTION_SPEC | features.py, feature_table.py |
| y, Y, K | Y = {NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY}, K = 4 | DIAGNOSTIC_PROBLEM_FORMULATION | config `dataset.classes` |
| p(x) | Δ^{K−1}; `p_raw` (RF), `p_cal` (after the selected calibrator, or identical if "none") | BASELINE_MODEL_SPEC, PROBABILITY_CALIBRATION_SPEC | baseline.py, calibration.py |
| ŷ(x) | argmax_k p_k(x), ties to the lower index | F2 | policy.py, runner `y_hat` |
| q(x) | Δ^{K−1}, reference-neighbourhood class support (own family excluded) | DISTINGUISHABILITY_MATHEMATICAL_SPEC | distinguishability.py |
| D(x) | [0, 1], q_(1) − q_(2) | same | same |
| C(x), M(x), H(x) | [1/K, 1], [0, 1], [0, log K] nats | UNCERTAINTY_AND_DISTINGUISHABILITY_COMPARATORS | comparators.py |
| −H(x) | [−log K, 0] (used so that higher = accept) | same | comparators.py (`neg_entropy`) |
| s_C(x), s_{C−D}(x) | (0, 1): logistic P(correct \| inputs) | same | combined_score.py |
| F(x) | subset of the 9 support flags | D_STATISTIC_EDGE_CASES | distinguishability.py |
| g(x) | {SPECIFIC, AMBIGUITY_SET, UNRESOLVED} | DECISION_POLICY_PSEUDOCODE | policy.py |
| S(x) | ambiguity set, 2 ≤ \|S\| ≤ 2 (max_set_size) < K | AMBIGUITY_SET_CONSTRUCTION | policy.py |
| τ, m, n | development threshold; requested count ceil(target·n); n = eligible windows | POLICY_THRESHOLD_SELECTION | runner |
| Coverage | n_SPECIFIC / n_eligible | STATISTICAL_ANALYSIS_PLAN | metrics.py |
| Selective risk | errors among SPECIFIC / n_SPECIFIC (undefined if 0) | same | metrics.py |
| Δ | risk(s_C) − risk(comparator), pooled over families | same | runner aggregate, uncertainty.py |

## Checks (plan A4 step 33 onwards)

| Check | Result |
| --- | --- |
| p vs q distinct (classifier vs reference neighbourhood) | consistent |
| D range, direction and tie rule | consistent ([0, 1]; higher = more one-sided) |
| Entropy direction (−H used as an acceptance score) | consistent |
| Confidence vs margin | consistent |
| Coverage denominator = all eligible windows (including UNRESOLVED) | consistent across metrics.py, the PA-1 selection and the SAP |
| Loss 1[ŷ ≠ y] only for SPECIFIC | consistent |
| Prediction ŷ vs decision g separated (y_pred_specific only on SPECIFIC; asserted) | consistent |
| Every equation implemented or marked conceptual | yes; no conceptual-only equation remains in the primary protocol |
| No unavailable measurements (temperature, metric location, blend %) | none used |

## Issues found and resolved

| # | Location | Severity | Issue | Resolution | Status |
| --- | --- | --- | --- | --- | --- |
| M1 | runner rank matching (v1.0) | major | tie-inclusive matching gave unequal coverage, so "matched coverage" was undefined under ties | PA-1 exact count | resolved |
| M2 | runner RQ1 (pre-Phase 9) | major | C vs B absent, although the formulation required it | all comparators reported | resolved |
| M3 | README §7, old figure spec | minor | "3-fold topology CV / zero leakage" contradicted the formulation | README and FIGURE_SPECIFICATION rewritten | resolved |
| M4 | DIAGNOSTIC_PROBLEM_FORMULATION | minor | written before PA-1; the matched-coverage rule is not restated there | cross-reference added to DIAGNOSTIC_PROBLEM_FORMULATION; POLICY_THRESHOLD_SELECTION authoritative | resolved |
| M5 | D(x) reference size: development (1 topology) vs test (2 topologies) | design note | combined-score weights are fitted on D with smaller support than at test time | recorded in D_STATISTIC_DESIGN_DECISION | accepted limitation |

**Conclusion:** no undefined symbol, contradictory formula or inconsistent metric definition remains in the primary protocol. All five items are resolved or accepted.
