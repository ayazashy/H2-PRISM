# 01 Integration Validation Report (Phase 8)

## Integration inventory (after Phase 8)

| Component | Module | Status |
| --- | --- | --- |
| Raw loading, time axis | `io.py` | IMPLEMENTED_AND_TESTED (integrated) |
| Manifest v0.2 | `tools/dataset/build_manifest_v02.py`, `feature_table.normalize_manifest_columns` | IMPLEMENTED_AND_TESTED (integrated; schema defect fixed) |
| Labels, timing, eligibility, windows | `windows.py`, `feature_table.py` | IMPLEMENTED_AND_TESTED (integrated) |
| Features (128) | `features.py` | IMPLEMENTED_AND_TESTED (integrated; leakage defect fixed) |
| Outer folds (LOTO) / inner LOTO | `splits.py`, runner | IMPLEMENTED_AND_TESTED (integrated) |
| Model selection on development | `baseline.select_on_development` (extracted, shared) | IMPLEMENTED_AND_TESTED (integrated) |
| Calibration + fallback | `calibration.py` | IMPLEMENTED_AND_TESTED (integrated) |
| D(x) + safeguards | `distinguishability.py` | IMPLEMENTED_AND_TESTED (integrated) |
| Combined scores s_C / s_C−D | `combined_score.py` | IMPLEMENTED_AND_TESTED (integrated) |
| Baselines C, M, −H, D-only | `comparators.py` via runner | IMPLEMENTED_AND_TESTED (integrated) |
| Three-outcome policy (primary and warning-only) | `policy.py` via runner | IMPLEMENTED_AND_TESTED (integrated) |
| Coverage/risk, RQ1, RQ2, estimability | `metrics.py`, `primary_protocol.aggregate` | IMPLEMENTED_AND_TESTED (integrated) |
| Paired family uncertainty | `uncertainty.py` via runner | IMPLEMENTED_AND_TESTED (integrated) |
| Provenance, artifact validation | run manifest (config / feature hashes, git commit, seed), A12 tools | IMPLEMENTED_AND_TESTED |
| **Runner** | `src/h2prism/experiments/primary_protocol.py` + CLI `tools/experiments/run_primary_protocol.py` | **IMPLEMENTED_AND_TESTED** (new) |

## Defects found and fixed in Phase 8 (each with a regression test)

| # | Defect | Effect if unfixed | Fix | Test |
| --- | --- | --- | --- | --- |
| 1 | `feature_table.py` required Phase-3 column names; the pinned manifest v0.2 uses `label_mapped`, `eligible_primary`, `file_*` | Builder fails on the selected manifest (no experiment possible) | `normalize_manifest_columns` (refuses ambiguous mixes) | `test_regression_feature_builder_accepts_manifest_v02_schema` |
| 2 | Provenance columns (`realization`, `feature_version`) were not in `METADATA_COLUMNS`, so they would be taken as model features | Leakage path: any provenance column (for example time in run) becomes a model input | Added to `METADATA_COLUMNS`; the runner additionally accepts only registered `<channel>__<stat>` features and fails on any mismatch | `test_regression_provenance_columns_are_never_features`; runner preflight |
| 3 | Runner availability mask used s_C finiteness for all methods | Baselines could be wrongly marked unavailable | Mask depends only on flags; each method's own score finiteness is applied separately | covered by the end-to-end run |
| — | Baseline selection loop duplicated logic needed by the runner | Risk of divergent selection rules | Extracted `select_on_development`; `run_grouped_evaluation` uses it unchanged | existing 17 baseline tests pass |

## Finding: protocol limitation, not changed

Random Forest probabilities are often exactly 1.0, so s_C saturates and many windows share an identical score. Rank matching accepts ties together (protocol-defined), so the realized coverages of s_C and s_C−D can differ (synthetic: 0.45 vs 0.55 at target 0.30). The runner reports both realized coverages in `rq1.csv`. **The protocol defines no tie-break or matched-coverage tolerance.** This is a decision for Faisal before execution (`FINAL_READINESS_VERDICT.md`).

## Validation executed

| Command | Result |
| --- | --- |
| `python -m compileall -q src tools tests` | OK |
| `pytest tests/test_primary_protocol.py` | 16 passed (17 required cases; about 90 s) |
| `pytest tests/test_phase6_components.py` | 11 passed (includes 2 regression tests) |
| `pytest` (full) | **193 passed, 2 skipped, 0 failed** (195 collected). Skips are expected: they test the sample-data fallback, which applies only when raw data is absent |
| `validate_artifacts.py --spec configs/candidate_artifact_validation.yaml` | 33/33 PASS |
