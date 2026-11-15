# Grouped Evaluation Protocol (Faisal F4)

## Chosen estimand

By decision, the primary evaluation uses the existing three topology-heldout
folds: each outer test split contains one known topology and training contains
the other known topologies. The supplied folds also retain a scenario whose
topology is recorded as `Unknown` in every training split; it is not assigned
to an outer test topology. This estimates **cross-topology transfer** with
that audited training exception. It does not estimate unseen-family
generalization.

The same `Scenario_Family_ID` is present on both sides of some topology
splits. The folds therefore do not satisfy strict global family-disjoint
evaluation, notwithstanding the scenario/topology separation. The experiment
reports exact overlap for each fold and makes no unseen-family claim. This
limitation is retained rather than rewriting the teammate-owned folds or
pretending the two split definitions are equivalent.

The canonical fold records contain only one family for `NORMAL`,
`COMPRESSOR_FAULT`, and `COMPRESSOR_DELAY` (and six for `LEAK`). Therefore a
strict family-disjoint four-class train/test split cannot include all four
classes on both sides with this dataset. Additional independent families for
the three single-family classes are required before that claim can be tested.
Per-fold counts are recorded in `FOLD_VALIDATION_REPORT.csv`.

## Outer-fold assertions

`src/h2prism/evaluation.py::load_outer_fold`:

- checks that every scenario has one split role, topology, family, and class;
- deduplicates mirror records to one canonical Parquet per `Scenario_ID`;
- asserts non-empty train/test sides, disjoint scenario IDs, disjoint topology
  values, and all four classes in both sides;
- measures and records (but does not hide) base-family overlap.

## Development-only operations

Within each outer training set, inner OOF predictions use a two-fold
`GroupKFold` grouped by topology. Because the supplied training splits contain
two known topologies plus the `Unknown`-topology scenario, the two inner folds
partition three topology groups; they do not leave each of the three groups
out independently. These OOF predictions are the only inputs for selecting a
calibration method and the 80% target-specific threshold. The inner split also
has base-family overlap; it is not described as family-independent. For D(x),
both the scaler fit and neighbor references exclude the entire query family.

Classifier feature summaries are computed independently per scenario and
contain no cross-scenario windows. No scaler, calibration method, model
parameter, reference neighbor, or policy threshold is selected from outer-test
labels. The accepted configuration version `1.0.2` in
`configs/frozen_evaluation_config.yaml` is frozen before generation of the
accepted outer results; any earlier technical shakeout outputs are discarded
and regenerated from this version.

## Reporting

Report raw and calibrated baseline metrics, per-fold results, per-family
results, matched-coverage risk, development-threshold coverage/risk, ambiguity
and unresolved outcomes, and family-clustered uncertainty. Test-score ranking
may select the requested coverage subset for a risk-coverage point; labels are
used only to calculate risk after that score-only selection.
