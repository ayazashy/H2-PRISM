# Feature Extraction Specification (F3)

- **Status:** SPECIFIED from `src/h2prism/features.py`; IMPLEMENTED and TESTED.
- **Register:** `02_methodology/FEATURE_DEFINITION_REGISTER.csv` (pinned `3dd5e927…`).

## Features (per channel × statistic, 16 × 8 = 128, named `<channel>__<stat>`)

| Statistic | Definition (samples v over window times t, seconds) | Offset-invariant |
| --- | --- | --- |
| mean | arithmetic mean | no |
| std | population standard deviation (ddof = 0) | yes |
| min | minimum | no |
| max | maximum | no |
| range | max − min | yes |
| last_minus_first | v[last] − v[first] | yes |
| slope | OLS slope of v on t (unit/s); NaN if all t are equal | yes |
| mean_abs_diff | mean \|v[i+1] − v[i]\| (per sample) | yes |

- **Channels:** PS1–PS12, MFS1–MFS4. No cross-channel or mass-balance features (inlet/outlet roles are not verified).
- **Metadata (never features):** `features.METADATA_COLUMNS`, which includes `window_id`, `Scenario_ID`, `Scenario_Family_ID`, labels, `phase`, `topology`, `boundary_status`, fold, time fields, `realization` and `feature_version`.
- **Enforcement:**
  - `features.assert_no_metadata_features()` raises on any metadata column.
  - The runner requires the exact registered set.
  - The contract test checks the name pattern.
- **Determinism:** `table_sha256` over a fixed float format. The real noise_added table (`4d1310a6…`) reproduced identically across runs.

## Known validity risk (limitation 10; no change to primary features)

- Absolute-level statistics (mean, min, max) nearly identify the run within a topology (median η² 0.99 for `__mean`).
- The registered sensitivity analysis `offset_invariant_features` restricts features to the 5 offset-invariant statistics (80 features).
- Interpretation of any primary result must take that sensitivity into account.
