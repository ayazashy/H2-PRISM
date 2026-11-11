# Invalidation note: primary run db9acd23ef58 (executed 2026-11-11)

- **Run:** authorized PRIMARY_EXPERIMENT (project-lead authorization, see `06_audit_preparation/EXECUTION_CLEARANCE_RECORD.md`), config `f788b6d8…`, git `38d7dfa`, 3/3 folds COMPLETED. This directory is preserved exactly as written by the runner (this note is the only addition). File hashes: `../../logs/PRIMARY_db9acd23ef58_OUTPUT_HASHES.sha256`.
- **Status: INVALID FOR SCIENTIFIC CONCLUSIONS.** It must not be used for RQ1/RQ2 claims.

## Confirmed implementation defect

- **Where:** outer fold 3 (held-out Upstream).
- **What happened:** development selected sigmoid calibration. The development out-of-fold probabilities came from single-topology inner models and were confidently wrong (log loss of "none" = 27.9), so Platt scaling learned a negative slope and reversed the ordering of the class probabilities. Applied to the outer test:
  - the uncalibrated RF top label was correct for 100% of Upstream windows;
  - the calibrated top label was correct for 0%.
- **Why it matters:** these calibrated probabilities feed C, M, H, s_C, s_C−D, the decisions and every RQ1/RQ2 table. The combined-score development data were calibrated with the same mapping.
- **Unaffected folds:** folds 1 and 2 selected calibration "none".

**Fix (code; no protocol value changed):**
- `calibration.Calibrator.monotone`: a calibration map must preserve the ordering of each class probability.
- `select_calibration` never selects a non-monotone map (cross-fitted or final), so the registered fallback "none" applies.
- Regression test: `tests/test_phase6_components.py::test_regression_order_reversing_sigmoid_is_never_selected`.

**Disclosure:** the defect was discovered while inspecting outer-test outputs. The rule (calibration must be order-preserving) does not depend on any outcome, and no threshold, feature, label or target was changed.

**Observations kept for the record (not conclusions):**
- Pooled RQ1 was NOT_ESTIMABLE at every registered target: the held-out-Center fold reached at most 25.8% coverage under the primary safeguards.
- The uncalibrated RF misclassified held-out Center LEAK windows as NORMAL. That fold used calibration "none", so this is a cross-topology transfer failure, not this defect.
