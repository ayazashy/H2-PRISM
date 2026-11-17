<<<<<<< HEAD
# Empirical Distinguishability Design Decision (Faisal F7)

## Definition and implementation

For each query family, first remove every reference window whose
`Scenario_Family_ID` equals that query's ID. Fit a `StandardScaler` on the
remaining reference windows only, transform those references and the query,
then rank the same leave-family-out references by Euclidean distance. Use up
to \(k=25\) neighbors. Neighbor contributions are inversely weighted by the
number of selected neighbors from that family; normalize the weighted class
totals to obtain \(q_k(x)\). Then:

\[
D(x)=q_{(1)}(x)-q_{(2)}(x).
\]

All four support proportions, effective neighbor/family counts, missing
classes, and a query-family-excluded assertion are saved with predictions.
The statistic is deterministic given the frozen feature table, reference
subset, class order, and configuration. It is empirical support—not physical
identifiability or a calibrated probability.

## Edge cases and interpretation

- Fewer than 25 eligible reference windows: use the available neighbors and
  record the actual number.
- No references after family exclusion: fail explicitly.
- A class with zero neighbor support remains at \(q=0\) and is listed as
  missing; no pseudo-count is added.
- Distance ties are resolved by unique `window_id`, making neighbor selection
  independent of input row ordering.
- A family may span multiple topologies. It is excluded completely, including
  other-topology rows.
- The excluded family's feature values do not affect either the scaler or
  neighbor ranking; a regression test perturbs query-family reference outliers
  and verifies unchanged support.

This last rule can remove all same-class support for a query class with only
one global family, such as normal operation. Such predictions are explicitly
flagged and can be unresolved; they are not silently repaired by including the
query family. Focused tests cover query-family exclusion, missing classes,
finite support, edge cases, and invariance to query/reference row-order
permutations. The `k=25` value is a frozen analysis choice, not a proven
optimal neighbor count. Sensitivity across neighbor counts remains an
exploratory follow-up, and any superiority claim requires the actual outer
results and family-level uncertainty.

The family-specific scaler correction is frozen in configuration `1.0.2`.
This correction protects D(x); it does not remove family overlap from the
classifier's supplied outer folds. The benchmark has only one family for
`NORMAL`, `COMPRESSOR_FAULT`, and `COMPRESSOR_DELAY`, making a strict
family-disjoint four-class split impossible without additional data.

Implementation: `compute_empirical_support` in
`src/h2prism/evaluation.py`. See `03_results/OUTER_PREDICTIONS.csv` and
`03_results/STATISTICAL_VALIDATION.csv`.
=======
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
>>>>>>> 6fee8a0a58a0773ad0ac6f0d5eb1f71ae4d984ed
