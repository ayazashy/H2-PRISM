# Preprocessing Specification (F3)

- **Status:** SPECIFIED from the implemented code; IMPLEMENTED and TESTED. Faisal acceptance NOT_RECORDED.
- **Sources:** `src/h2prism/io.py`, `feature_table.py`, `experiments/primary_protocol.py`.
- **Config:** `06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml` (final-protocol-1.1, `f788b6d8…`).

## Pipeline (one command: `tools/experiments/run_primary_protocol.py`)

1. **Manifest:**
   - Read manifest v0.2 (`36bcbaf9…`). The pinned hash is checked.
   - `feature_table.normalize_manifest_columns` maps the v0.2 names to internal names. A mix of both naming schemes raises an error.
2. **Eligibility:** only `eligible_primary == True` runs (51). Excluded runs keep their `exclusion_reason`.
3. **Raw file selection:**
   - Exactly one realization per run: `file_noise_added` (primary) or `file_clean` (robustness / `clean_realization` sensitivity). Realizations are never pooled.
   - Each file's SHA-256 must equal the manifest value. A missing or modified file is a PreflightError.
4. **Time axis (`io.build_time_axis`):**
   - The parquet `Timestamp` index (1.0 s) is used as is.
   - A file without a time column needs an explicit `assumed_dt_s` and a documented source; no silent assumption is made.
   - Non-increasing time raises (no repair).
5. **Channels:** PS1–PS12 (MPa) and MFS1–MFS4 (kg/s) (`io.SENSOR_CHANNELS`). Units are documentary (ReadME); no conversion is applied.
6. **Missing values:** no imputation anywhere. Non-finite feature values fail the run closed (PreflightError). Real data: 0 non-finite values.
7. **Scaling:** none is applied to model inputs (Random Forest). The only standardisation is inside D(x), fitted on the reference (development) windows (see `DISTINGUISHABILITY_MATHEMATICAL_SPEC.md`).
8. **Feature selection:** none. The fixed registered set is used (`FEATURE_EXTRACTION_SPEC.md`).
9. **Phase:** recorded as metadata and **not** used as a model input (`phase_used=False`).

## Leakage controls

- Identifiers, labels, timing, topology, phase, fold and provenance columns are in `features.METADATA_COLUMNS` and can never become features.
- The runner accepts only `<channel>__<stat>` names, which must equal the registered set exactly.
- Nothing is fitted on outer-test windows (`FINAL_CODE_AND_METHOD_AUDIT.md` §3).

## Tests

`tests/test_io.py`, `test_windows.py`, `test_features.py`, `test_phase6_components.py`, `test_primary_protocol.py` (missing or modified raw file, wrong schema), `test_interface_contract.py`.
