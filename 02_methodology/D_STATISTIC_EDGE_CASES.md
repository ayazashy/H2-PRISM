# D(x) Edge Cases and Support Flags (F7)

- **Status:** SPECIFIED from `EmpiricalSupport._one`; every case is tested in `tests/test_distinguishability.py` or `test_phase6_components.py`.
- **Flags:** joined by `|` in `support_flags`; an empty string means none.

| Case | Behaviour | Flag | Effect in the primary policy |
| --- | --- | --- | --- |
| Non-finite query features | D = NaN, q not computed | INVALID_FEATURES | UNRESOLVED |
| No reference after own-family exclusion | D = NaN | NO_REFERENCE | UNRESOLVED |
| \|R(x)\| < k | k_eff = \|R(x)\| | SPARSE_REFERENCE | reported only |
| Some class has fewer than 25 reference windows | computed | INSUFFICIENT_CLASS_REFERENCE | reported only |
| Distance ties at d_(k) | all tied windows included | — | — |
| Top class has fewer than 5 neighbours | computed | LOW_SUPPORT | reported only |
| Top-class neighbours come from fewer than 2 families | computed | TOP_CLASS_FEW_INDEPENDENT_RUNS | **blocks SPECIFIC** |
| Neighbourhood from fewer than 2 scenarios | computed | LOW_SCENARIO_DIVERSITY | **blocks SPECIFIC** |
| Nearest neighbour distance ≤ 1e-9 (duplicate) | computed | ZERO_DISTANCE_NEIGHBOR | reported only |
| Mean neighbour distance above the OOS threshold | computed | OUT_OF_SUPPORT | UNRESOLVED |
| One class in the neighbourhood | D = 1 | (usually one of the support flags) | qualified by the flags |
| q tie between classes | D = 0; order by class index | — | — |
| Constant reference feature | σ = 1 (recorded in `constant_features_`) | — | — |
| Non-finite reference features | `fit` raises ValueError | — | run fails closed |

**Expected on real data (structural, before any fitting):** NORMAL, FAULT and DELAY have one family per development topology. TOP_CLASS_FEW_INDEPENDENT_RUNS will therefore fire whenever they are the top class. This drives the expected NOT_ESTIMABLE status of the 0.80 and 0.90 targets.
