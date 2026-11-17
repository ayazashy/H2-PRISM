# Model Interface Compatibility (F3–F9, A12–A16) with the Candidate Dataset

No model was trained on real data, no hyperparameter was tuned, and no research metric was computed.

| Component | Interface with the candidate package | Change made | Evidence | Status |
| --- | --- | --- | --- | --- |
| Raw loading (`io.read_table`, `io.build_time_axis`) | Parquet time is a stored **index** named `Timestamp` | **Fixed:** `build_time_axis(time_col="Timestamp")` now accepts an index of that name (`TIME_SOURCE_INDEX`) | `test_real_data_interfaces.py` (4 real runs) | TESTED on real files |
| Validation (`io.validate_scenario_frame`) | 16 sensor channels; no NaN | none | same | TESTED |
| Windowing (`windows.generate_windows`) | Scenario dict built from manifest columns (`canonical_clean_file`, `Scenario_ID`, `family_primary`, `candidate_primary_class`, `eligible_primary_candidate`) | none needed | Delay run: only COMPRESSOR_DELAY windows eligible, post-event windows excluded; excluded run: 0 eligible windows; normal run: all eligible | TESTED on real files (interface values 60 s / 30 s are **not** an approved choice) |
| Features (`features.extract_features`, register) | 16 channels × statistics; names match the register | none | 64 columns for 4 statistics; metadata guard | TESTED on real files |
| Grouped evaluation (`splits`, `baseline.outer_folds_from_table`) | `CANDIDATE_OUTER_FOLDS.csv` has `outer_fold_id`, `split_role`, `Scenario_ID`; family columns can be renamed to `Scenario_Family_ID` | none | `test_candidate_package.py` (validator + `assert_group_disjoint` under 3 views; runner consumes folds) | TESTED |
| RF runner, calibration (F5/F6) | Takes a window feature table with `Scenario_Family_ID` plus the folds above | none | Synthetic tests (`test_baseline.py`, integration) | TESTED (synthetic only; real-data execution NOT authorised) |
| D(x) (F7) | Reference = outer-train windows; query family exclusion via `family_primary` | none | Synthetic tests | TESTED (synthetic only) |
| Policy (F9), comparators / ablations (A16) | Operate on prediction tables, independent of the dataset | none | Synthetic tests | TESTED (synthetic only) |
| LR reference (A14), feature sensitivity (A15) | Same runner and fold interface | none | Synthetic tests | TESTED (synthetic only) |
| Artifact validation (A12) | New spec `configs/candidate_artifact_validation.yaml` | added spec | 33/33 PASS (`artifact_validation/`) | EXECUTED |
| Provenance | `OUTPUT_HASHES.json`, file SHA-256 in the inventory, `BUILD_SUMMARY.json` | added | hash test | TESTED |
| Legacy loader (`h2prism.data.load_fold`) | Still reads Yazan's `folds.csv` (two files per scenario; leaky) | **not changed** (owner: Yazan) | — | Must not be used for experiments. Use the candidate manifest after approval |

## Open integration item

There is no one-command builder yet that turns the approved manifest into the full window and feature table. It depends on Faisal's decisions (realization, window/stride, pre-event policy). It is easy to add once those are fixed; it was not written to avoid presupposing them.
