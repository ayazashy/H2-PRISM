# Faisal: Experiment Design Dossier (decisions F-D01 … F-D18)

**Status:** every decision is `PENDING_HUMAN_APPROVAL`. Recommendations are protocol choices made **without** any outer-test outcome. No model has been trained on project data.

## F-D01: Realization

| Option | Alignment | Realism | Independence / leakage | Interpretation |
| --- | --- | --- | --- | --- |
| A clean only | weak (noise-free signals overstate separability) | low | fine | optimistic |
| B noise-added only | good | intended by the data publisher (ReadME) | fine | primary |
| **C noise-added primary + clean secondary (recommended)** | good | as B | fine **if never pooled** | adds a pre-registered noise-sensitivity check |
| D both pooled as training data | — | — | **invalid**: duplicates every run | — |

Fix the choice before any run. Both realizations of a run always sit on the same side (enforced).

## F-D02: Outer design (`pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv`)

- Leave-one-topology-out: 3 folds, each with 17 test runs and 34 training runs.
- **Verified:** 0 issues under primary, extended and conservative families; no byte-identical file across a split; all 4 classes in every training and test fold; topology carries no class information (identical class profile per topology).
- **Generalisation target:** a withdrawal topology of the same simulated network that was not seen in training. It is **not** an unseen industrial network and not field data.
- Alternative: family K-fold mixing topologies. It leaves test folds without NORMAL or DELAY, so it is not recommended as primary.

## F-D03: Inner scheme (`evidence/INNER_FOLD_SUFFICIENCY.csv`)

| Requirement | LOTO_within_train (recommended) | grouped_by_family_primary_k3 |
| --- | --- | --- |
| Train/validation independence | ✔ (topology-disjoint; tested) | ✔ (family-disjoint; tested) |
| Every class in inner train | ✔ 6/6 | ✔ 9/9 |
| Every class in inner validation (needed for calibration and thresholds) | ✔ | ✘ (some splits lack NORMAL / FAULT / DELAY) |
| D(x) inner reference per class | NORMAL 1 run (665 windows), DELAY 1 run (**31 windows**), FAULT 2 runs, LEAK 13 runs | 1–2 runs for the thin classes |
| Determinism | ✔ | ✔ |

**Consequence:** development-stage selection for NORMAL and DELAY rests on single runs. For DELAY, a k = 25 neighbourhood is essentially the whole class reference of one run, so expect `LOW_SCENARIO_DIVERSITY`.

## F-D04: Windows (`evidence/WINDOW_OPTION_COMPARISON.csv`; 51 eligible runs, `pre_event_policy = exclude`)

| Window / stride | Eligible windows | NORMAL | LEAK | FAULT | DELAY | Boundary losses | Overlap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 / 15 | 56,118 | 3,996 | 43,953 | 7,980 | 189 | 102 | 50% |
| **60 / 30** | 27,993 | 1,995 | 21,921 | 3,984 | 93 | 93 | 50% |
| 60 / 60 | 14,013 | 999 | 10,977 | 1,992 | 45 | 51 | 0% |
| 120 / 60 | 13,962 | 996 | 10,938 | 1,986 | 42 | 93 | 50% |
| 300 / 150 | 5,529 | 396 | 4,335 | 786 | 12 | 90 | 50% |

Recommendation: **60 / 30 primary, 60 / 60 as a dependence sensitivity check.**
- Sampling is a verified 1 s, so a window holds 60 samples.
- The shortest event (DELAY, 976 s) still yields 31 windows per run.
- Boundary losses are below 0.3%.
- Shorter windows only add correlated windows, never new runs.

**F-D05 (joint):** `label_normal` raises NORMAL-contributing runs from 3 to 45, but those NORMAL windows come only from early run time, which is phase-confounded. Recommendation: `exclude` for the primary analysis, `label_normal` as a pre-registered secondary.

## F-D06: Feature contract

- 16 verified channels (PS1–12 in MPa, MFS1–4 in kg/s; units REPORTED).
- 8 statistics per channel, 128 features in total (`02_methodology/FEATURE_DEFINITION_REGISTER.csv`, SHA-256 `3dd5e927…`).
- No cross-channel or mass-balance features (inlet/outlet roles unverified).
- Absolute and level features are kept in the primary set; the offset-invariant 80-feature subset is the A15 sensitivity arm (fingerprint risk).
- Missing values: none observed. Windows with non-finite values are excluded.
- Scaling inside training folds only. IDs, topology, phase and time are never features (enforced).

## F-D07: Thin classes

| Class | Runs | Families (primary) | Per test fold | Supported use |
| --- | ---: | ---: | --- | --- |
| LEAK | 39 | 30 | 13 runs / 10 families | pooled and per-family; family bootstrap |
| COMPRESSOR_FAULT | 6 | 3 | 2 runs / 1 family | DESCRIPTIVE_ONLY |
| COMPRESSOR_DELAY | 3 | 3 | 1 run | DESCRIPTIVE_ONLY |
| NORMAL | 3 | 3 | 1 run | DESCRIPTIVE_ONLY (unless F-D05 secondary) |

## F-D08: D(x)

**Implementation (mathematically verified by 17 tests):**
- training-only standardisation;
- tie-inclusive Euclidean k-NN;
- query-family exclusion;
- q_c is 0, never NaN, for absent classes;
- flags for sparse reference, missing class, low diversity, zero distance, out of support and invalid input;
- optional inverse-distance weighting and prior correction.

Outer-train reference support (60 / 30): NORMAL 2 runs (1,330 windows), DELAY 2 runs (62 windows), FAULT 4 runs (2,656), LEAK 26 runs (14,614).

**Recommended pre-registration:**
- Primary: k = 25, uniform weighting, no prior correction, `min_distinct_scenarios = 2`, `low_support_min_top_count = 5`, OUT_OF_SUPPORT at the 0.99 leave-one-family-out quantile of the development reference.
- Sensitivity: k = 10 and k = 50; prior correction on.
- Scenario-balanced support is **not implemented**. Implement it only if Faisal wants it as a sensitivity arm.
- The empirical usefulness of D is **untested** (RQ1).

## F-D09 / F-D10: Calibration and comparators

- Calibration: none / sigmoid / isotonic compared on inner OOF with log loss; "none" is kept unless strictly better.
- Isotonic is fragile with one run per thin class.
- Comparators C, M and −H use the same probabilities. s_C and s_{C−D} are fitted as logistic models on cross-fitted development predictions; **this meta-model is not implemented yet** (it implements a plan definition, so it can proceed).
- A conformal alternative is not prepared. It would need an exchangeability argument across topologies, which three groups do not support.

## F-D11 / F-D12: Policy and thresholds

Recommended settings:
- candidates from p only;
- a singleton candidate becomes UNRESOLVED;
- `max_set_size = 2` (at K = 4, a size-3 set is close to uninformative);
- OUT_OF_SUPPORT, INVALID and NO_REFERENCE give UNRESOLVED;
- LOW_SCENARIO_DIVERSITY blocks SPECIFIC.

Thresholds come from inner OOF at target coverage 0.80 (0.60 and 0.90 secondary). `PolicyConfig` refuses any source other than development.

## F-D13 … F-D18

- Family-paired bootstrap on the primary map, with the extended map as sensitivity. No topology-level inference.
- Accept the plan's Random Forest grid with seed `20261104`.
- Technical acceptance of the new code (`VALIDATION_AND_REGRESSION_REPORT.md`).
- Interface-contract amendments.
- Freeze `configs/frozen_evaluation_config.yaml` from `CANDIDATE_EVALUATION_FREEZE_SPEC.md`.
- A12–A16 integration gate.

## Remaining technical blockers

1. Correctness meta-model (s_C, s_{C−D}) with cross-fitting: not implemented.
2. One-command window and feature builder over the approved manifest: not implemented (needs F-D01, F-D04, F-D05).
3. Scenario-balanced D support: not implemented (optional).
4. F11 family bootstrap: not implemented.
