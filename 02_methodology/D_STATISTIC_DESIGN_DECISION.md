# D(x) Design Decision Record (F7)

- **Status:** DECIDED_UNDER_PROJECT_LEAD_PROTOCOL_DELEGATION (Phase 7) and recorded in the config. Faisal attestation NOT_RECORDED.
- No value below was chosen from outer-test data. None exists.

| Decision | Choice | Rationale | Alternatives (registered as sensitivity, if any) |
| --- | --- | --- | --- |
| Neighbourhood size | k = 25 | plan F7 prespecified starting value; ≥ 25 windows exist per class per development topology | `k_10`, `k_50` |
| Metric | Euclidean on reference-standardised features | simple and transparent; the scale is fitted on the reference only | none (limitation: Euclidean suitability is untested) |
| Weighting | uniform | no tuning parameter | inverse distance implemented, not registered |
| Prior correction | off | q reflects raw neighbourhood composition; LEAK dominance is reported, not reweighted | `prior_correction` |
| Own-family exclusion | on | prevents self- and sibling-evidence | none |
| Tie handling | tie-inclusive | row-order invariance | none |
| Blocking flags | TOP_CLASS_FEW_INDEPENDENT_RUNS, LOW_SCENARIO_DIVERSITY | a high D driven by one run is not independent evidence (F-D08) | `policy_warning_only` (secondary variant: only LOW_SCENARIO_DIVERSITY blocks) |
| Unresolved flags | OUT_OF_SUPPORT, INVALID_FEATURES, NO_REFERENCE | no reliable neighbourhood | none |
| OOS threshold | 0.99 quantile of leave-one-family-out reference distances | fitted on the reference only | none |
| Development reference | other development topology | cross-fitting without self-reference | none. Limitation: test-time reference has 2 topologies |

**Dominance investigation:** `n_distinct_scenarios`, `max_scenario_share`, `n_distinct_families` and `top_class_n_families` are stored for every window, and the flag rates are reported per fold.

**Not claimed:** physical identifiability, novelty, or superiority of D. RQ1 tests D's incremental value only through s_C vs s_C−D at matched coverage.
