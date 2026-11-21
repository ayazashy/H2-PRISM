# Implementation and Test Report (Phase 6)

## Code changes (preparation stage only; no real-data training)

| File | Change | Decision |
| --- | --- | --- |
| `src/h2prism/distinguishability.py` | new flag `TOP_CLASS_FEW_INDEPENDENT_RUNS` (`DConfig.min_top_class_families`, default 2) and output column `top_class_n_families` | F-D08 |
| `src/h2prism/calibration.py` | `calibration_feasibility()`: pre-registered fallback to "none" when any class has fewer than 2 independent development groups; isotonic excluded unless explicitly allowed | F-D09 |
| `src/h2prism/combined_score.py` (new) | cross-fitted s_C / s_{C−D} correctness meta-model; development-only fit; NaN for undefined D | F-D10 |
| `src/h2prism/uncertainty.py` (new) | paired, topology-stratified family bootstrap; per-stratum descriptive estimates | F-D13 |
| `src/h2prism/feature_table.py` (new) | manifest → window manifest + feature table; realization, family column, window config and statistics are required arguments; one realization per run | F-D01, F-D04–F-D06 |
| `tools/dataset/build_manifest_v02.py` (new) | deterministic candidate manifest v0.2 | Y-D07 |
| `06_audit_preparation/phase6_resolution/build_updated_matrix.py` (new) | updated decision matrix generator | — |
| `tests/test_phase6_components.py` (new, 9 tests) and `tests/test_candidate_config.py` (new, 4 tests) | see below | F-D15 |

## Tests executed

| Command | Result |
| --- | --- |
| `pytest tests/test_phase6_components.py tests/test_distinguishability.py tests/test_baseline.py` | 34 passed |
| `pytest tests/test_candidate_config.py` | 4 passed |
| `python -m compileall -q src tools tests` | OK |
| `pytest` (full, once) | **171 passed, 2 skipped** (skips apply only when raw data is absent); 0 failed |
| `validate_artifacts.py --spec configs/candidate_artifact_validation.yaml` | 33/33 PASS |
| `build_manifest_v02.py` run twice | identical SHA-256 |

What the new tests verify:
- the single-run top class is flagged even when the neighbourhood looks diverse;
- calibration falls back to "none" when support is insufficient;
- meta-model out-of-fold scores do not depend on the own group's labels;
- the no-D score ignores D;
- NaN D yields a NaN score;
- the bootstrap is deterministic, independent of row order, keeps strata and warns on 1-unit strata;
- identical methods give exactly 0;
- duplicate units are rejected;
- the feature builder is deterministic and order-independent, uses one realization, excludes ineligible runs, keeps metadata out of features, and requires decision arguments;
- the config is never frozen, its hashes match, its objects can be built, and it is consistent with v0.2.

No defect in existing code was found in this phase.

## Not executed (by design)

- `feature_table.build_feature_table` on the full real dataset (that would build the primary table before sign-off);
- any model fit, calibration, D, policy or bootstrap on real data;
- a macOS or Linux run.
