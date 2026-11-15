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
