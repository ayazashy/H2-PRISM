# Faisal Pipeline Leakage Validation

## Checks enforced by the implementation

- One canonical Parquet input is loaded per `Scenario_ID`; mirror file rows are
  not multiplied into model samples.
- Train/test scenario IDs and topology values are checked for disjointness for
  every configured outer fold. Both sides must contain all four primary
  classes.
- Fold family overlap is measured and emitted; it is **not** asserted to be
  zero. This is a topology-transfer experiment, not unseen-family evaluation.
- Windows are built within one scenario only. Incomplete event-boundary,
  pre-event, post-event, compound, or unsupported-label windows do not enter
  the primary feature table.
- Classifier inputs are sensor summaries only. IDs, labels, timestamp, phase,
  and topology are excluded by feature-column selection.
- Model and calibration decisions use outer-training data. Calibration and
  specific-coverage thresholds are selected from inner grouped OOF
  predictions; outer-test labels do not select them.
- `D(x)` standardization is fit separately on references after removing the
  complete query family; that family is excluded from scaling and ranking.
- Family sample weights and family-level bootstrap/sign-flip summaries avoid
  treating repeated windows as independent uncertainty units.

## Explicit limitation

The supplied folds intentionally hold out topology, while base families span
topologies. Consequently, family overlap across outer train/test is expected
and reported in `03_results/FOLD_VALIDATION_REPORT.csv`. The experiment cannot
support an unseen-family generalization claim. Strict family-disjoint
four-class evaluation is not claimed to be feasible under the existing class
family distribution.
The supplied folds also keep one scenario with topology recorded as `Unknown`
in each training split; it is not assigned to a test split. This retained
exception is disclosed in the fold diagnostics and experiment report.

Only one family is available for each of `NORMAL`, `COMPRESSOR_FAULT`, and
`COMPRESSOR_DELAY` in the canonical fold records. A fully family-disjoint
four-class evaluation cannot be formed from these data: holding out the sole
family of any of those classes would leave that class absent from training.
Additional independent families are needed to measure unseen-family
generalization without dropping classes.

The evaluated windows are selected using audited normal/event intervals. This
defines a conditional event-attribution population and is not an end-to-end
prospective event-onset detector. Results also remain limited to simulated
hydrogen-blend data.

The automated checks are implemented in `src/h2prism/evaluation.py` and
`tests/test_faisal_pipeline.py`. Runtime fold diagnostics and input hashes are
in the generated result tables.
