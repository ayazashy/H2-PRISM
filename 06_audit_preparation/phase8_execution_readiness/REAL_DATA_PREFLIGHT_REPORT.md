# 03 Real-Data Preflight (read-only; PREFLIGHT_ONLY; no model fitting)

**Command:**
```
python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out <scratch> --dry-run
```
Result: **PREFLIGHT_PASSED** in about 92 s. Evidence: `REAL_DATA_PREFLIGHT_MANIFEST.json` (config sha256 `b9f44ad7…`, git commit `d9b4c3f`).

## Checks (25 of 25 passed, noise-added primary realization)

- **Config:** status `PROTOCOL_SELECTED_PENDING_EXECUTION`; required sections present.
- **Pinned hashes:** manifest v0.2, outer folds, inner folds, label mapping and feature register all match.
- **Manifest:** required columns present; 51 eligible runs (= config); unique IDs; 4 classes; every exclusion has a reason; families nest in topology.
- **Folds:** cover the eligible runs exactly; family isolation (validator: no issues); topology isolation (one test topology per fold, disjoint from training).
- **Raw files:** all 51 noise-added files present and **byte-identical to the manifest SHA-256** (raw data unmodified).
- **Policy and thresholds:** policy flags are known; thresholds are development-only.

## Feature compatibility (feature extraction only)

| Realization | Windows | Per class (NORMAL / LEAK / FAULT / DELAY) | Feature-table SHA-256 | Checks |
| --- | ---: | --- | --- | --- |
| noise_added (primary) | 27,993 | 1,995 / 21,921 / 3,984 / 93 | `4d1310a6…` | 25/25 |
| clean (robustness) | 27,993 | identical | `3bc7e712…` | 25/25 (`REAL_DATA_PREFLIGHT_CLEAN_REALIZATION.json`) |

- 128 features; only registered sensor statistics are used.
- Every eligible window carries its run's class: no pre-event or post-delay relabelling, and no boundary windows.
- The counts reproduce Phase-4 evidence (`WINDOW_OPTION_COMPARISON.csv`) exactly.

## Structural estimability bound (from class shares, not from model outputs)

LEAK is 78.3% of eligible windows in every topology (NORMAL 7.1%, FAULT 14.2%, DELAY 0.3%). With thin-class top classes flagged in development, the 0.80 / 0.90 primary targets are expected not estimable. Actual estimability is determined by the runner in the development stage.

**Not performed (prohibited in this phase):** model fitting, D(x) on real data, predictions, outer-test scoring, risk–coverage, statistics.
