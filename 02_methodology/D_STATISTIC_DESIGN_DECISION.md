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
