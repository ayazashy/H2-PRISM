# Candidate Dataset Manifest v0.2 (PROVISIONALLY_SELECTED, PENDING YAZAN SIGNOFF)

| Item | Value |
| --- | --- |
| File | `06_audit_preparation/phase6_resolution/CANDIDATE_MANIFEST_V02.csv` |
| SHA-256 | `36bcbaf97bb17659995f393884d1dcde3bbca9236c3dcdcc6e7651e61538fb59` (identical on two builds; LF enforced by `.gitattributes`) |
| Rows | 57 runs; 51 `eligible_primary` |
| Build | `python tools/dataset/build_manifest_v02.py` (reads only the pinned Phase-3 package; no raw data) |
| Source package | `06_audit_preparation/pre_experiment_review/OUTPUT_HASHES.json` (17/17 pinned hashes reproduced on a fresh Windows checkout) |
| Raw source | Zenodo 10.5281/zenodo.17871393 V2, archive MD5 `15bc64a3afc9e2990c9db66eb37617de`; per-file SHA-256 of both realizations in the manifest columns |

## Columns

| Group | Columns |
| --- | --- |
| Identity | `Scenario_ID`, `run_stem`, `topology` |
| Families | `Scenario_Family_ID` (= primary map), `family_extended_sensitivity`, `family_conservative_sensitivity` |
| Labels | `raw_label_columns` (raw, unmodified), `label_mapped` |
| Eligibility | `eligible_primary`, `exclusion_reason` |
| Timing | `timing_status`, `onset_s`, `delay_last_active_s`, `window_label_rule`, `phase_used=False` |
| Restrictions | `location_analysis_allowed` (False for the 3 `leakG5G6_overlapped` runs) |
| Realizations | `file_noise_added`, `sha256_noise_added`, `file_clean`, `sha256_clean`, `candidate_primary_realization` |
| Versioning | `evidence`, `manifest_version=v0.2-candidate`, `status` |

## Verification

`tests/test_candidate_config.py::test_manifest_v02_consistent_with_config`:
- 51 eligible runs, 39 families;
- the 4 classes as listed;
- every exclusion has a reason;
- families nest in topology;
- the eligible set equals the fold set.

The selection rules are listed in the builder docstring and in `YAZAN_RESOLUTION.md`. The v0.1 provisional package and `01_dataset_audit/` are unchanged.
