# Three-Outcome Selective Diagnostic Policy: DRAFT (combined pseudocode and threshold rules)

**Task:** F9 (owner: Faisal; validity and interpretation reviewed by Ahmed). This draft also covers the content required for DECISION_POLICY_PSEUDOCODE.md and POLICY_THRESHOLD_SELECTION.md.
**Status:** IMPLEMENTED and TESTED (`src/h2prism/policy.py`, `tests/test_policy.py`, 11 tests). Thresholds have NOT been chosen. NOT ACCEPTED.

## Pseudocode (exactly as implemented)

```
input : p(x) in simplex over K classes, s(x), optional D(x), flags F(x), PolicyConfig
1  if p(x) invalid (non-finite, outside [0,1], row sum != 1)  -> UNRESOLVED, INVALID_INPUT
2  if s(x) non-finite                                         -> UNRESOLVED, INVALID_SCORE
3  if F(x) ∩ unresolved_flags != {}                            -> UNRESOLVED, FLAG:<names>
      (default unresolved_flags: OUT_OF_SUPPORT, INVALID_FEATURES, NO_REFERENCE)
4  why = []
   if s(x) < tau_accept                         why += SCORE_BELOW_THRESHOLD
   if tau_D set and not (D(x) >= tau_D)         why += D_BELOW_THRESHOLD_OR_UNDEFINED
   if F(x) ∩ specific_blocking_flags != {}      why += FLAG_BLOCKS_SPECIFIC
   if why == []                                  -> SPECIFIC, y_hat = argmax p (ties: lower class index)
5  order classes by p desc (ties: lower index); m = smallest prefix with cumulative p >= ambiguity_mass
6  if m == 1: singleton_handling == "unresolved" -> UNRESOLVED; else m = 2
7  if m >= K                                     -> UNRESOLVED, ALL_CLASS_SET_PREVENTED
8  if m > max_set_size                           -> UNRESOLVED, SET_TOO_BROAD
9  otherwise                                     -> AMBIGUITY_SET, S = first m classes, reason = why
```

Invariants (all tested): 2 ≤ |S| ≤ min(max_set_size, K−1); an all-class set is never emitted; an out-of-support window is never forced to SPECIFIC; y_true is never an input; output is deterministic.

## Threshold-selection rules (binding for every caller)

- `PolicyConfig.threshold_source` must be `"development"`; any other value raises an error.
- τ_accept, τ_D, ambiguity_mass and max_set_size are chosen only on inner (development) out-of-fold predictions, with the query family excluded, and are then frozen in `configs/frozen_evaluation_config.yaml`. That file does not exist yet (F4).
- A development fit is not independent validation. The outer test is used once, after freezing.

## Open decisions (Faisal; Ahmed approves interpretation)

The choice of candidate source (p only, as now, or p combined with q); `singleton_handling`; `max_set_size` (for K = 4 the only admissible values are 2 or 3); which flags block SPECIFIC; and whether τ_D applies alongside the combined score s_C or only in the D-only arm.
