# Evaluation Feasibility Report: CANDIDATE_NOT_APPROVED

## 1. Family views (`CANDIDATE_FAMILY_MAP.csv`, evidence in `FAMILY_RELATIONSHIP_EVIDENCE.csv`)

| View | Rule | Families (57 runs) | Notes |
| --- | --- | ---: | --- |
| **Primary** | Union of WEAK_STRONG_SAME_INJECTION (dataset ReadME plus identical pre-event rows) and SHARED_IDENTICAL_TRAJECTORY (≥ 400 identical leading rows); 12 edges | 45 | All 12 dependence edges are weak/strong pairs (G3G4, G4, G5, C1 fault × 3 topologies) |
| Extended (dependence-cautious) | Primary plus SHARED_SHORT_INITIAL_SEGMENT (1–399 identical leading rows); 19 more edges | 35 (it merges e.g. C1 fault with C1 delay, and transient leakG4 with leakG4 weak/strong) | The short shared segments look like a common initial state (25 rows) or almost-identical early transients (387–397 of 400 rows). Recorded as **unresolved** (plan Y2 step 23: no merging on initial state alone) |
| Conservative | One family per topology | 3 | Upper bound on dependence |

Facts that hold across all views: no family spans topologies, and 0 of 1,083 cross-topology run pairs share any identical row. The **unresolved-relationships register** is the 19 `SHARED_SHORT_INITIAL_SEGMENT` rows in `FAMILY_RELATIONSHIP_EVIDENCE.csv`.

**Implication:** under leave-one-topology-out, all three views nest inside topology, so the outer folds are family-disjoint under **every** view. The view matters only for inner splits and for any resampling-based uncertainty.

## 2. Candidate outer folds (`CANDIDATE_OUTER_FOLDS.csv`)

Leave-one-topology-out (3 folds), 51 eligible runs, one row per run carrying both canonical realization paths.

Validation (`h2prism.splits.validate_outer_folds` over all files of every realization, byte-identity equivalence):
- **0 issues under primary, extended and conservative views** (`CANDIDATE_FOLD_VALIDATION_ISSUES.csv` is empty).
- Re-checked by `tests/test_candidate_package.py`: no family overlap, no byte-identical file across a split, every eligible run exactly once per fold, every topology tested exactly once, and all 4 classes in every training and every test fold.

| Class | Independent runs | Primary families | Runs per test fold | In every training fold | Class-level inference |
| --- | ---: | ---: | --- | --- | --- |
| LEAK | 39 | 30 | 13 | yes (26) | **RESTRICTED**: 10 families per test fold; family-level resampling is possible but tests one topology at a time |
| COMPRESSOR_FAULT | 6 | 3 | 2 (one weak/strong family) | yes (4) | **DESCRIPTIVE_ONLY** |
| COMPRESSOR_DELAY | 3 | 3 | 1 | yes (2) | **DESCRIPTIVE_ONLY** |
| NORMAL | 3 | 3 | 1 | yes (2) | **DESCRIPTIVE_ONLY** (could change if pre-event rows are labelled NORMAL) |

`CLASS_BY_TOPOLOGY.csv`: every topology holds the same class profile (1 / 2 / 13 / 1). So **topology carries no label information**, and the test topology cannot leak class through topology.

## 3. Inner development splits (`CANDIDATE_INNER_FOLDS.csv`)

- `LOTO_within_train`: 2 per outer fold, 6/6 feasible, all classes in every inner train.
- `grouped_by_family_primary_k3`: 9/9 feasible.
- Both use outer-training runs only.

## 4. Estimand and limitations

- **Estimand:** performance on a **withdrawal topology not seen in training**, i.e. generalisation across network operating configuration. This is stricter than a random-scenario holdout and is not the same quantity.
- Fold-to-fold variation mixes model variance with topology shift. With 3 topologies, no inference *across topologies* is possible.
- Windows are repeated observations. Effective sample size is runs or families, never windows.
- Phase and event type are confounded by design (compressor events at 25 s, leaks at 100–7000 s). Time-in-run must not be a feature.

## 5. Claim classification (pending approval)

| Claim type | Status |
| --- | --- |
| Pooled LEAK vs non-LEAK selective-risk/coverage comparison across held-out topologies | RESTRICTED |
| C vs C−D comparison (RQ1) at the pooled level with family-level paired resampling | RESTRICTED (feasible only for the pooled population, dominated by LEAK) |
| Per-class results for NORMAL / COMPRESSOR_FAULT / COMPRESSOR_DELAY | DESCRIPTIVE_ONLY |
| Three-outcome policy behaviour (RQ2) | EXPLORATORY until thresholds are frozen on development data |
| Generalisation to new networks, field data, or pure hydrogen | NOT_SUPPORTED |
| Leak localisation (G3–G6) | NOT_SUPPORTED (L1 annotation conflict; not a primary target) |
