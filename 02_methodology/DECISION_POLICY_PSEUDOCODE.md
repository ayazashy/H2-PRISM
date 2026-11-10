# Three-Outcome Decision Policy: Pseudocode (F9)

- **Status:** transcribed from `policy.apply_policy` (IMPLEMENTED, TESTED in `tests/test_policy.py`).
- **Primary config:** `candidate_source: p_only`, `singleton_handling: unresolved`, `max_set_size: 2`, `ambiguity_mass: 0.9`.
  - `unresolved_flags`: OUT_OF_SUPPORT, INVALID_FEATURES, NO_REFERENCE.
  - `specific_blocking_flags`: LOW_SCENARIO_DIVERSITY, TOP_CLASS_FEW_INDEPENDENT_RUNS.

```
input: p(x) (calibrated, K=4), score s(x), flags F(x), tau_accept (development threshold or PA-1 selection), classes
if p(x) is not a valid probability vector:            return UNRESOLVED, reason INVALID_INPUT
if s(x) is not finite:                                return UNRESOLVED, reason INVALID_SCORE
if F(x) ∩ unresolved_flags ≠ ∅:                       return UNRESOLVED, reason FLAG:<flags>
order ← classes sorted by (−p_c, class index)
why ← []
if s(x) < tau_accept:                                 why += SCORE_BELOW_THRESHOLD
if F(x) ∩ specific_blocking_flags ≠ ∅:                why += FLAG_BLOCKS_SPECIFIC:<flags>
if why is empty:                                      return SPECIFIC, prediction order[0]
m ← smallest m with Σ_{j≤m} p_order[j] ≥ 0.9           (ambiguity construction, see AMBIGUITY_SET_CONSTRUCTION.md)
if m == 1:                                            return UNRESOLVED, SPECIFIC_REJECTED_SINGLE_CANDIDATE
if m ≥ K:                                             return UNRESOLVED, ALL_CLASS_SET_PREVENTED
if m > max_set_size (2):                              return UNRESOLVED, SET_TOO_BROAD
return AMBIGUITY_SET, set = order[1..m]  (no specific prediction)
```

## Rank-matched mode (PA-1)

- The runner first selects exactly m* = ceil(target · n) eligible windows by (score desc, SHA-256 tie key asc).
- It then calls the same policy with s = +1 for selected windows, −1 for unselected finite scores, NaN otherwise, and τ = 0.
- The SPECIFIC count must equal m*; this is asserted.

## Invariants (asserted in aggregation)

- y_pred_specific is set only on SPECIFIC rows.
- Ambiguity sets have 2 ≤ |S| ≤ K−1.
- n_specific + n_ambiguity + n_unresolved = n_eligible.
