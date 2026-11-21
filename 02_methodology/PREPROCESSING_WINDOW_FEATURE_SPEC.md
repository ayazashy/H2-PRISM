# Preprocessing, Windowing, and Feature Specification (Faisal F3)

## Inputs and provenance

Use the versioned provisional manifest and `01_dataset_audit/folds.csv`.
Training inputs are canonical Parquet files only, one file per `Scenario_ID`;
mirror/format duplicates are not independent observations. Keep
`Scenario_ID`, `Scenario_Family_ID`, topology, target label, window boundaries,
eligibility, and exclusion reason in the window metadata. The pipeline does
not modify raw data or Yazan's audit artifacts.

## Frozen window rules

`configs/frozen_evaluation_config.yaml` freezes 60 samples per window, a
60-sample stride, and the audited 1 Hz rate. Windows are non-overlapping and
must be complete. An abnormal scenario contributes windows wholly contained in
its annotated `[event_onset_s, event_offset_s]` interval. Pre-event,
post-event, and boundary-crossing windows are recorded but excluded. A normal
baseline scenario contributes complete windows under its normal scenario
label. In that case `DURING_EVENT` in the inherited status vocabulary means
the whole window is valid for the normal baseline label; it does not assert a
fault event. Trailing samples that cannot form a full window are counted in
`tail_samples_omitted` and are not padded.

Compound or otherwise ineligible records are retained in the manifest with
their frozen exclusion reason and never enter the primary feature table.
Unknown labels, missing timing for an abnormal scenario, non-monotone
timestamps, missing sensors, and non-finite sensor readings fail explicitly
or are marked ineligible; no labels are inferred from phase or filename.
Consequently, the evaluation estimates attribution conditional on these
audited intervals, not prospective event detection before onset.

## Features

For each of 12 pressure channels and 4 mass-flow channels, compute mean,
standard deviation, 5th-to-95th percentile range, first-difference mean, and
first-difference standard deviation. This yields 80 sensor features per
window. Timestamp, phase, topology, raw labels, scenario IDs, family IDs, and
event-boundary metadata are not model inputs. The implementation uses
`src/h2prism/windows.py`.

The estimator receives unscaled sensor summaries. The only scaling in the
pipeline is the `StandardScaler` used by `D(x)`; it is fit independently on
each reference/training subset and never on the outer test set. Window fitting
weights are inverse to the number of windows in each family, so a family with
more eligible windows does not acquire proportionally greater total weight.

## Reproduction

From the repository root, install project requirements and run:

```bash
python scripts/run_experiments.py
```

The run writes `03_results/WINDOW_MANIFEST.csv` and
`03_results/FEATURE_TABLE.csv` along with the fold results and hashes. The
feature table is fold-tagged because a scenario can be training data in one
outer fold and test data in another.
