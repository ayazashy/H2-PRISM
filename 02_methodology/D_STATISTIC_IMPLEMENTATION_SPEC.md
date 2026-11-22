# D(x) Implementation Specification: DRAFT

**Task:** F7 (owner: Faisal; math review by Ahmed under A4; leakage review by Yazan).
**Status:** IMPLEMENTED and TESTED on synthetic and hand-calculated fixtures (`tests/test_distinguishability.py`, 17 tests). NOT EXECUTED on project data. NOT ACCEPTED.
**Claim boundary:** D(x) is an empirical neighbourhood statistic. It is not physical identifiability, and no value of D has been demonstrated.

## Definition (`src/h2prism/distinguishability.py`)

```
z(x)   = (x - mu_R) / sigma_R            mu_R, sigma_R computed on the reference set R only
                                          (a constant feature gets sigma = 1, and this is recorded)
R(x)   = { r in R : family(r) != family(x) }  when exclude_query_family = True
d_k    = k-th smallest Euclidean distance from z(x) to R(x),  with k_av = min(k, |R(x)|)
N(x)   = { r in R(x) : ||z(x) - z(r)|| <= d_k + tie_tol }     tie-inclusive, so the result is
                                                              independent of reference row order
w_r    = 1  (uniform)   or   1 / max(d_r, distance_floor)  (inverse_distance)
s_c    = sum of w_r over r in N(x) with y_r = c;  optional prior correction s_c / pi_c,
         where pi_c is the class share in R(x)
q_c    = s_c / sum_c' s_c'                q(x) in the simplex; an absent class gets q_c = 0, never NaN
D(x)   = q_(1) - q_(2),  where the ordering breaks ties by lower class index;  D = q_(1) if K = 1
```

Reference construction rules, enforced by the caller and tested in the integration test:

- **Outer-test queries:** R = outer-training windows only. Families are disjoint by assertion.
- **Development queries:** `development_support()` computes q and D for each reference window with its own family excluded.
- The query's label is never an argument. Labels from the outer test never enter R.

## Saved outputs (per query)

`q_<class>`, `D`, `top_class`, `second_class`, `k_requested`, `k_effective`, `n_available_reference`, `n_distinct_scenarios`, `n_distinct_families`, `max_scenario_share` (a scenario-dominance diagnostic), `mean_/min_/max_neighbor_distance`, `support_flags`.

## Edge cases and their behaviour

| Case | Behaviour | Test |
| --- | --- | --- |
| Fewer than k references | k_eff = \|R(x)\|; flag SPARSE_REFERENCE | `test_fewer_than_k_references` |
| Distance ties | All tied references are included | `test_ties_are_included_and_order_invariant` |
| Only one class in the neighbourhood | D = 1; this is **not** treated as strong evidence; check the flags | `test_scenario_dominance_and_low_diversity` |
| Class missing from the reference | q_c = 0; flag INSUFFICIENT_CLASS_REFERENCE | `test_missing_class_gives_zero_not_nan` |
| Duplicate or zero-distance references | Flag ZERO_DISTANCE_NEIGHBOR | `test_zero_distance_and_duplicates_flagged` |
| Neighbourhood drawn from a single scenario | Flag LOW_SCENARIO_DIVERSITY; `max_scenario_share` = 1 | same test as above |
| Non-finite query features | D = NaN; flag INVALID_FEATURES; the policy returns UNRESOLVED | `test_invalid_query_features` |
| Non-finite reference features | `fit` raises | `test_reference_rejects_non_finite` |
| Far from all references | OUT_OF_SUPPORT, only if a threshold was fitted with `fit_out_of_support_threshold` on the reference | `test_out_of_support_threshold_from_reference_only` |
| Class imbalance | Optional prior correction | `test_prior_correction` |

## Open decisions (Faisal, before the primary run)

1. Whether k = 25 is defensible given the realised reference size per fold and class. Under the current folds, each held-out fold has 1–2 scenarios per non-LEAK class.
2. Uniform vs inverse-distance weighting, and prior correction on or off. Choose one primary definition; the others stay exploratory.
3. Flag thresholds (`min_class_reference`, `min_distinct_scenarios`, `low_support_min_top_count`, the OUT_OF_SUPPORT quantile). The defaults in `DConfig` are PROVISIONAL placeholders.
4. Window-level vs scenario-balanced support. Scenario dominance is measurable (`max_scenario_share`) but no balancing is implemented.
5. Whether Euclidean distance on standardised features is suitable. Absolute-pressure fingerprinting can dominate distances; this is checked through the A15 offset-invariant arm.
