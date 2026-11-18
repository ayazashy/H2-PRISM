# Faisal Repository Implementation Audit (F1)

This audit records the implementation evidence used for Faisal's Stage 2
workstream. Teammate-owned plans, audit code, data files, and authored reports
were treated as read-only inputs. Historical/demo artifacts are not treated as
experimental evidence.

| Component | Status | Evidence and disposition |
|---|---|---|
| Dataset inventory, family mapping, label mapping, timing, readiness | `REUSE_AS_READ_ONLY_INPUT` | Existing Yazan audit package, provisional manifest, class map, and folds are consumed without modification. |
| Scenario data access | `REUSE_WITH_LIMITATION` | Existing data loader is used by existing tests; the new experiment runner uses its own strict fold loader so missing required scenarios fail instead of being silently skipped. |
| Windowing and features | `IMPLEMENTED_FOR_FAISAL` | `src/h2prism/windows.py`, focused tests, and `PREPROCESSING_WINDOW_FEATURE_SPEC.md`. |
| Outer fold evaluation | `IMPLEMENTED_WITH_EXPLICIT_LIMITATION` | `src/h2prism/evaluation.py` validates supplied topology-heldout folds and reports base-family overlap; protocol is explicitly cross-topology transfer. |
| Baseline, calibration, empirical support, comparators, policy | `IMPLEMENTED_FOR_FAISAL` | `src/h2prism/evaluation.py`, relevant methodology specifications, and result tables from `scripts/run_experiments.py`. |
| Primary comparisons and uncertainty | `IMPLEMENTED_FOR_FAISAL` | `src/h2prism/experiments.py` writes matched-coverage, per-family, bootstrap, and sign-flip outputs. Interpret inferential results cautiously given the small number of independent families. |
| Existing `scripts/visualize.py --demo` and existing dashboard/figures | `DEMO_ONLY_NOT_EVIDENCE` | Demo source uses hard-coded or synthetic model figures/KPIs. These existing artifacts are not overwritten and must not be presented as Stage 2 findings. |
| Shared interface contracts and teammate audit artifacts | `PRESERVED_UNMODIFIED` | The existing interface YAML, fold file, provisional freeze, audit scripts, and team plans remain read-only inputs. |
| Existing visualization package import | `STATIC_REVIEW_FINDING_NOT_MODIFIED` | `src/h2prism/visualization/dashboard.py` annotates with `Any` without importing it. This is outside the Faisal-owned pipeline change set and was left untouched. |

## Status boundary

The code additions implement Faisal's pipeline and result generation; they do
not complete Ahmed's manuscript/provenance responsibilities or Yazan's data
audit responsibilities. A static audit is not a substitute for the recorded
test run and full experiment. Validation results and any runtime blockers are
recorded in `04_validation/TEST_RESULTS.md`.
