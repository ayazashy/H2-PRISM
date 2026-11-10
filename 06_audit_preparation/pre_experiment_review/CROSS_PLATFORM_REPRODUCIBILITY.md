# Cross-Platform Reproducibility of Canonicalisation

## Defect (Yazan's audit scripts)

`audit/02…py` and `audit/03_04…py` write paths with the OS separator and choose the "canonical" Parquet by iteration order. The result: 58/58 clean-tree files on macOS, but 3/58 on Windows (`../raw_verification/AUDIT_RERUN_KEYED_COMPARISON.csv`). Yazan's scripts are **not modified**. The correction is a separate, versioned candidate module.

## Correction (`src/h2prism/dataset_manifest.py`)

| Mechanism | Implementation |
| --- | --- |
| Path normalisation | `norm_path`: backslash → `/`, collapse `//`, strip `./` |
| Order-independent discovery | `discover_files` returns sorted, de-duplicated normalised paths; `build_file_inventory` re-sorts any input list |
| Stable Scenario_ID | `CS_<TOPOLOGY>_<SEGMENT_DIR>_<RUN_STEM>` from the normalised path; `_noisy` stripped |
| Unlocated files | Resolved only by SHA-256 equality to a located file |
| Content fingerprints | SHA-256 of bytes; sensor fingerprint over the canonical sensor order (column-order invariant); numerical equivalence by `allclose(atol=1e-9)` |
| Format precedence | Parquet before CSV (stored `Timestamp` index and labels), then path |
| Stable families | Deterministic union-find (minimum ID is the representative) |
| Deterministic output | Fixed float format `%.10g`, `\n` line endings, sorted rows, `OUTPUT_HASHES.json` |

## Verification

| Check | Command or test | Result |
| --- | --- | --- |
| Real data: reversed order + Windows separators | `build_pre_experiment_package.py --order reversed --out <scratch>`, then compare `OUTPUT_HASHES.json` | **13/13 output files byte-identical** |
| Windows vs POSIX paths, `./`, `//` | `test_dataset_manifest.py::test_norm_path_windows_and_posix`, `test_parse_location_both_separators` | PASS |
| Different file orders | `test_inventory_independent_of_order_and_separator` | PASS |
| Equivalent CSV/Parquet, shuffled column order | `test_csv_parquet_equivalence_and_column_order`, `test_fingerprint_column_order_invariant` | PASS |
| Duplicate / misfiled file | `test_realization_typing_and_misfiled_copy` | PASS |
| Missing metadata, `Timestamp` column vs index | `test_missing_metadata_and_timestamp_column`; `test_io.py`; `test_real_data_interfaces.py` | PASS |
| Saved hashes still match the files | `test_candidate_package.py::test_output_hashes_match_files` | PASS |

**Not verified:** an actual macOS or Linux run. Determinism was established on Windows with simulated POSIX/Windows inputs only.
