<<<<<<< HEAD
# Diagnostic Problem Formulation (Faisal F2)

## Scope

The primary task is four-class event attribution on eligible H2-SimNet
simulation windows: `NORMAL`, `LEAK`, `COMPRESSOR_FAULT`, and
`COMPRESSOR_DELAY`. The frozen class mapping and compound-event exclusions are
defined in `01_dataset_audit/class_mapping.yaml` and the provisional manifest.
This is simulated hydrogen-blend data, not evidence of field performance or
pure-hydrogen operation.

For a sensor-derived feature vector \(x\), the classifier returns
\(p_k(x)\), the probability assigned to class \(k\). The confidence, margin,
and normalized entropy are

\[
C(x)=p_{(1)}(x),\quad
M(x)=p_{(1)}(x)-p_{(2)}(x),\quad
H(x)=-\frac{\sum_k p_k(x)\log p_k(x)}{\log 4}.
\]

Separately, a fold-specific reference set yields empirical class-support
proportions \(q_k(x)\) from nearest feature windows after excluding every
reference row sharing the query's `Scenario_Family_ID`. The empirical
distinguishability statistic is

\[
D(x)=q_{(1)}(x)-q_{(2)}(x).
\]

`D(x)` is a support statistic derived from this dataset, feature definition,
reference set, distance, and neighbor count. It is not a physical
identifiability result, a localization estimate, or a calibrated probability.
The query family is excluded even when it occurs in the outer training data
under another topology.

## Decision outcomes

The operational decision has three outcomes:

1. `SPECIFIC`: report one class when the development-selected combined score
   clears its threshold and the candidate set is a singleton.
2. `AMBIGUITY_SET`: return a bounded set of plausible classes when multiple
   candidates remain and the policy's evidence floor is met.
3. `UNRESOLVED`: abstain when evidence is insufficient to provide either a
   specific result or a useful ambiguity set.

Coverage always means the fraction receiving a `SPECIFIC` decision; selective
risk is the error rate among those specific decisions. Ambiguity-set and
unresolved frequencies are reported separately.

## Evaluation boundary

Outer evaluation holds out one topology at a time. This is a
cross-topology-transfer estimand, not unseen-family generalization: the frozen
folds contain base-family overlap across topologies. Results must retain that
qualification. The supplied fold file also retains a scenario with unknown
topology metadata in training, not test. The evaluated population is
conditional on the audited
normal/event intervals used to label eligible windows; this is not an
end-to-end event-onset detector. The canonical folds have only one family for
`NORMAL`, `COMPRESSOR_FAULT`, and `COMPRESSOR_DELAY`, so strict family-disjoint
evaluation cannot include all four classes with the current data. No phase,
topology, timestamp, labels, or identifiers are classifier features.
=======
# Diagnostic Problem Formulation and Symbol Register: DRAFT

**Task:** F2 (owner: Faisal). The symbol register also supports A4 (owner: Ahmed).
**Status:** SPECIFIED (draft prepared on branch `audit/preparation-integration`). **Faisal has not approved it and Ahmed has not reviewed it.**
**Dependency not met:** Y4 frozen mapping. `class_mapping.yaml` is marked `FROZEN_FOR_FAISAL`, but the plan requires Faisal technical review and Ahmed scientific review before the freeze, and no record of either review exists (see `06_audit_preparation/YAZAN_DATASET_VERIFICATION.md`).

## 1. Objects

| Symbol | Domain / range | Meaning | Implementation |
| --- | --- | --- | --- |
| x | ℝ^d | An eligible measurement window, represented by its feature vector. Eligibility is decided by `windows.generate_windows` | `src/h2prism/windows.py`, `src/h2prism/features.py` |
| d | ℕ | Number of model features (`FEATURE_DEFINITION_REGISTER.csv`; the final subset is decided by Faisal) | `features.model_feature_columns` |
| y | Y | Frozen target label of the window | `windows.map_rows_to_primary` (row-level) or the scenario label (file-level) |
| Y, K | Y = {NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY}, K = \|Y\| = 4 | Provisional primary target from `class_mapping.yaml` (pending review) | config `classes` |
| f, p(x) | p(x) ∈ Δ^(K−1) | Classifier probability vector. `p_raw` is uncalibrated; `p_calibrated` is used only when F6 selects a calibrator on development data | `baseline.py`, `calibration.py` |
| ŷ(x) | Y | argmax_k p_k(x), ties broken by lower class index. This is a **classifier output, not a decision** | `baseline.py`, `policy.py` |
| q(x) | Δ^(K−1) | Empirical class support in the tie-inclusive k-neighbourhood of x within the reference set, which excludes x's own family | `distinguishability.py` |
| D(x) | [0, 1] | q_(1)(x) − q_(2)(x). An empirical statistic, **not** physical identifiability | `distinguishability.py` |
| C(x) | [1/K, 1] | max_k p_k(x) | `comparators.confidence` |
| M(x) | [0, 1] | p_(1)(x) − p_(2)(x) | `comparators.margin` |
| H(x) | [0, log K] (nats) | −Σ_k p_k log p_k, with 0 log 0 := 0. In acceptance scores it is used as −H (higher means more willing to accept) | `comparators.entropy` |
| s(x) | ℝ | Acceptance score. Higher means more willing to issue SPECIFIC. F10 defines s_C = LR[logit C, M, −H, D] and s_{C−D} = LR[logit C, M, −H], both fitted on development data only | `comparators.logit`; F10 meta-model: NOT_STARTED |
| g(x) | {SPECIFIC, AMBIGUITY_SET, UNRESOLVED} | Diagnostic decision, defined separately from ŷ | `policy.apply_policy` |
| S(x) | subset of Y, 2 ≤ \|S\| ≤ min(max_set_size, K−1) | Ambiguity set: the shortest prefix of the p-ordered classes whose cumulative mass reaches m_amb | `policy.py` |
| τ_accept, τ_D, m_amb | ℝ, [0,1], (0,1] | Policy thresholds. They must have `threshold_source = development` | `PolicyConfig` |
| F(x) | set of flags | Support flags: SPARSE_REFERENCE, INSUFFICIENT_CLASS_REFERENCE, LOW_SCENARIO_DIVERSITY, LOW_SUPPORT, OUT_OF_SUPPORT, ZERO_DISTANCE_NEIGHBOR, INVALID_FEATURES, NO_REFERENCE | `distinguishability.py` |

## 2. Evaluation quantities (Faisal F10 step 89)

- Loss for an accepted SPECIFIC: ℓ(ŷ, y) = 1[ŷ ≠ y].
- Coverage = N_SPECIFIC / N_eligible.
- Selective risk = N_incorrect SPECIFIC / N_SPECIFIC. It is undefined when N_SPECIFIC = 0, and that case is reported, never imputed.
- AMBIGUITY_SET and UNRESOLVED outcomes are never counted as correct specific diagnoses. Ambiguity sets are reported by inclusion rate **together with** set size.
- Statistical independence unit: `Scenario_Family_ID`. Windows are repeated, correlated observations.

## 3. Decisions this draft does NOT make (owners must decide)

1. **Label granularity.** Labels can be row-level (Parquet binary columns, with onsets in `EVENT_TIMING_AUDIT.csv`) or file-level. `WindowConfig.label_mode` must be set explicitly.
2. **Pre-event rows of fault scenarios.** Under the row-level reading of `class_mapping.yaml`, these rows are NORMAL. `pre_event_policy ∈ {exclude, label_normal}` is a required argument. The choice changes how many families count as NORMAL (from 1 up to roughly all of them), so it directly affects the Y5 feasibility argument.
3. **Ambiguity in the NORMAL rule.** The YAML rule "label_anomaly == 0 **or** all fault columns == 0" overlaps the fault rules. The implementation applies fault-precedence and marks label_anomaly=1 rows with no fault as `ANOMALY_WITHOUT_TYPE`. Yazan must confirm this reading.
4. Window length and stride (60 s / 30 s is only a candidate), k, flag thresholds, `singleton_handling`, `max_set_size`, and the calibration criterion.

> **Cross-reference (2026-11-11, A4 item M4):** matched coverage is defined by protocol amendment PA-1 (exact-count selection with a salted SHA-256 window_id tie key, denominator = all eligible windows of the outer-test fold). The authoritative definition is `02_methodology/POLICY_THRESHOLD_SELECTION.md`.
>>>>>>> 6fee8a0a58a0773ad0ac6f0d5eb1f71ae4d984ed
