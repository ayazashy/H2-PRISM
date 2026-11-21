# Dataset Reconciliation Report: CANDIDATE_NOT_APPROVED

**Source:** official H₂-SimNet V2 (Zenodo 10.5281/zenodo.17871393; archive MD5 verified; see `../RAW_DATASET_VERIFICATION_REPORT.md` §1–2).
**Generator:** `python tools/dataset/build_pre_experiment_package.py --raw-parent data/raw --out 06_audit_preparation/pre_experiment_review`. Module: `src/h2prism/dataset_manifest.py`.
Output hashes are in `OUTPUT_HASHES.json`. The run summary is in `BUILD_SUMMARY.json`.

## 1. What is a run, what is a realization

242 tabular files reduce to **57 simulated runs (candidate Scenario_IDs)**. Each run has up to four realizations:

| Realization | Files | Evidence | Handling |
| --- | ---: | --- | --- |
| CLEAN_SIMULATION | 114 (57 CSV + 57 Parquet; one per run and format) | `H2-SimNet-clean/` tree (which also holds the 6 `_noisy` files and 1 misfiled copy, counted below) | One canonical file per run (Parquet precedence) |
| NOISE_ADDED_RELEASE | 114 (57 + 57) | 57 of the 60 `CLEAN_VS_NOISE_ADDED_SAME_RUN` edges: labels identical, residual mean < 0.01, lag-1 autocorrelation ≈ 0 (white noise, as the ReadME states) | Same run. **Never** independent evidence |
| NOISE_ADDED_VARIANT (`*_noisy`) | 6 (3 + 3) | The remaining 3 `CLEAN_VS_NOISE_ADDED_SAME_RUN` edges: same test against the clean file | Same run |
| RAW_SOLVER_EXPORT (MATLAB CSV) | 6 | 3 `RAW_SOLVER_EXPORT_OF_SAME_RUN` edges. After interpolation to 1 s, the median per-channel error is 0.08–0.6% of range | Same run; not modelling input (dt 0.8/0.9 s, PS11/PS12/MFS4 missing, no labels) |
| MISFILED_COPY | 2 | SHA-256 identical to `anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet` (the noisy Upstream run) | Assigned to `CS_UPSTREAM_ASSESTMENT_TRANSIENT_LEAKG4`; excluded as a file |

Inside a realization, CSV and Parquet are **format twins**: 121 `SAME_REALIZATION_FORMAT_TWIN` edges, all numerically equal at atol 1e-9. Exact per-file facts (SHA-256, rows, time source, dt, label onsets) are in `CANDIDATE_FILE_INVENTORY.csv`.

## 2. Differences: formatting vs noise vs content

- **Formatting only:** CSV vs Parquet inside a tree, and CRLF vs LF in Yazan's copy (`../raw_verification/CHECKSUM_RECONCILIATION.csv`).
- **Numerical noise only:** clean vs release, and clean vs `_noisy`.
- **Different simulation content:** different scenarios. Within a topology, some pairs share identical leading pre-event rows (`FAMILY_RELATIONSHIP_EVIDENCE.csv`). No cross-topology pair shares any row (0 of 1,083).

## 3. Canonicalization procedure (deterministic, cross-platform)

1. Discover files and normalise paths to POSIX form; sort.
2. Parse topology, segment directory and run stem from the path. Strip `_noisy`.
3. Files at unlocated paths are resolved **only** by byte identity to a located file. Otherwise they are UNRESOLVED (no such case remains).
4. Canonical file per (run, realization): Parquet before CSV, then lexicographic path. Parquet is preferred because it carries the `Timestamp` index and the labels, and the CSV is numerically identical.
5. **The modelling realization (clean or noise-added) is not chosen here.** That is Faisal's decision, and the manifest lists both canonical files.

Verified: feeding the files in reverse order with Windows separators gives **byte-identical outputs** (13/13 files). See `CROSS_PLATFORM_REPRODUCIBILITY.md`.

## 4. Unresolved provenance

- The H₂ fraction is unverified (not in the ReadME, `.m` scripts or `.slx` XML).
- Why a noisy file sits at the clean-tree root is unknown (publisher-side). It is handled as a copy.
- The ReadME anomaly table does not cover leakG5 (5000 s), leakG6 (7000 s), start-transient leakG3 (100 s) or transient leakG4 (400 s). See `LABEL_AND_TIMING_CORRECTIONS.md`.
