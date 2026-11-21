# H2-PRISM Frozen Outer-Fold Experiment Report

**Status:** Empirical results generated from the frozen configuration; interpret only under the limitations below.
**Config:** `1.0.2` (`configs/frozen_evaluation_config.yaml`)
**Git commit:** `13c55125a2588cfb2708d7c0e58bc9454996b933`
**Independent uncertainty unit:** `Scenario_Family_ID` for family-level summaries and resampling.

## Evaluation estimand and family-overlap limitation

The configured outer folds hold out one network topology at a time. This tests
**cross-topology transfer**. The audited fold assignments reuse some
`Scenario_Family_ID` values across train and test because those families have
members at multiple topologies. The results therefore **must not** be described
as unseen-family generalization or as independent held-family validation. The
exact overlap is recorded in `FOLD_VALIDATION_REPORT.csv`. The D(x) reference
set excludes the entire query family, even when that family is represented in
outer training data. The evaluation population is conditional on the audited
normal/event intervals used to define eligible windows; this experiment is not
an end-to-end prospective event-onset detector. The data are simulated
hydrogen-blend results, not evidence of field performance or pure-hydrogen
operation. The supplied folds also retain a scenario whose topology is recorded as `Unknown` in each training split; it is not assigned to an outer test topology. Inner validation uses two GroupKFold partitions over the three training topology values, so it does not leave each topology group out independently.
 Strict family-disjoint four-class evaluation is not feasible with the current dataset because only one family is available for: COMPRESSOR_DELAY, COMPRESSOR_FAULT, NORMAL.

## Frozen pipeline

- Non-overlapping 60-sample windows at 1 Hz; only
  windows wholly inside annotated event intervals are used for abnormal runs.
- Normal baseline files provide baseline windows. Pre-event, post-event,
  boundary-crossing, and excluded compound windows remain accounted for in
  `WINDOW_MANIFEST.csv` and are excluded from model fitting.
- Inputs are pressure/flow window summaries only; phase, topology, time,
  labels, and identifiers are not model features.
- One canonical Parquet per `Scenario_ID`; model fitting weights windows so
  each family has equal total weight.
- A fixed random forest baseline, inner topology-grouped OOF calibration
  selection, family-excluded nearest-neighbor support (`k=25`),
  and a development-only specific-diagnosis threshold.
- All performance rows report the held-out topology transfer estimand.

## Baseline and matched-coverage comparison

```
   method  folds  mean_matched_coverage  mean_matched_risk  mean_deployed_coverage  mean_deployed_risk
        B      3               0.800196           0.680964                0.803383            0.673289
       B2      3               0.800196           0.680964                0.802648            0.673289
       B3      3               0.800196           0.680964                0.815069            0.672164
        C      3               0.800196           0.681883                0.799869            0.671409
C_minus_D      3               0.800196           0.680964                0.803710            0.673289
   D_only      3               0.800196           0.577512                0.866552            0.593726
```

`SELECTIVE_EVALUATION_RESULTS.csv` includes each fold, the test-score-ranked
matched-coverage risk, and the separately reported risk/coverage obtained by
applying the threshold selected from development OOF data. Matched-coverage
ranking uses only model scores to choose accepted test rows; labels are used
only to calculate test risk.

## Calibration and three-outcome policy

Calibration methods are fitted and selected using inner grouped OOF data only;
outer-test calibration metrics are in `CALIBRATION_RESULTS.csv`. Calibration
selection on the same development OOF predictions used to fit each
classwise calibrator is a development selection procedure, not an independent
calibration validation set.

Outcome counts and fractions are in `POLICY_OUTCOMES.csv`. Ambiguity sets are
truncated to at most 3 classes according to
the frozen policy; `candidate_count`, truncation flags, and reason codes are
saved per outer prediction.

## Family-level uncertainty and ablation

```
       comparison  independent_units  mean_family_risk_difference  bootstrap_ci_95_low  bootstrap_ci_95_high  two_sided_sign_flip_p     permutation_method  bootstrap_replicates           interpretation
C_minus_C_minus_D                  9                    -0.011795            -0.039132              0.003376                 0.8125 exact_family_sign_flip                  1000 negative favors method C
        C_minus_B                  9                    -0.011926            -0.039403              0.003340                 0.7500 exact_family_sign_flip                  1000 negative favors method C
```

The intervals resample independent family-level risk differences, not windows.
The paired sign-flip p-values use family-level risk differences and should be
treated as limited-sample exploratory inference; the number of independent
families is reported in `STATISTICAL_VALIDATION.csv`. Negative risk differences
favor C. Retain null, negative, and inconclusive findings.

## Reproducibility artifacts

The run generated `65` SHA-256 provenance entries in
`RESULTS_PROVENANCE.csv`, including the frozen config, manifest, fold table,
input Parquet files, and source modules. `FEATURE_TABLE.csv`,
`OUTER_PREDICTIONS.csv`, per-fold results, per-family results, and generated
Stage 2 figures contain the auditable intermediate and final outputs.

This empirical `D(x)` is a data-dependent class-support statistic. It is not a
claim of physical identifiability, physical localization, field validation,
or hydrogen-purity outside the audited H2-SimNet benchmark.
