# Data Processing History (A10)

- **Status:** PRE-EXPERIMENT. Chronological record of every transformation between the archive and the model input.
- Experiment runs (git commit, config hash, seed, status) will be appended from each `run_manifest.json` after authorized execution. **None exists yet.**

| Date | Step | Input → output | Version / hash | Change ref |
| --- | --- | --- | --- | --- |
| 2026-10-30 | Yazan audit v0.1: inventory, path-derived scenario/family map, provisional freeze | local raw copy → `01_dataset_audit/*` | v0.1-provisional | Y8 |
| 2026-11 (Phase 2) | Official archive download and untouched extraction; MD5 verified; cross-tree and label analysis | Zenodo zip → `data/raw/` | MD5 `15bc64a3…` | raw_verification/ |
| 2026-11-10 (Phases 3–6) | Run identity rebuilt (57 runs × 2 realizations); evidence-based families; label mapping; LOTO folds | raw → manifest v0.2, folds | `36bcbaf9…`, `3b21d823…`, `ebff65da…` | CC-001 |
| 2026-11-10 (Phase 7) | Protocol selected (windows 60/30, 128 features, RF, calibration, D(x), policy, thresholds) | → FINAL_EXPERIMENT_CONFIG 1.0 | `b9f44ad7…` | CC-002 |
| 2026-11-11 (Phase 8) | Runner integration; manifest-schema and provenance-leak fixes | → feature tables (not stored) | noise `4d1310a6…`, clean `3bc7e712…` | CC-003 |
| 2026-11-11 (Phase 9) | PA-1 matched-coverage tie rule; contract v2 | → FINAL_EXPERIMENT_CONFIG 1.1 | `f788b6d8…` | CC-004, CC-005 |
| 2026-11-11 (Phase 10) | Sensitivity execution paths (overrides in code; config unchanged); real structural dry runs; reporting adapters | no data change | config unchanged | CC-007 |

**Model-input transformation chain:**
1. Parquet (1.0 s index), one realization per run.
2. Row-level label mapping.
3. 60 s / 30 s windows, keeping only eligible DURING_EVENT / NO_EVENT windows.
4. 8 statistics × 16 channels.
5. No scaling or imputation for the RF; D(x) standardisation is fitted on the development reference only.

**Raw data were never modified.**
