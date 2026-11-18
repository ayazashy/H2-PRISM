# Probability Calibration Specification (F6)

- **Status:** SPECIFIED from `src/h2prism/calibration.py`; IMPLEMENTED and TESTED.
- **Results:** CALIBRATION_RESULTS are POST_EXPERIMENT.
- **Config:** `calibration: {candidates: [none, sigmoid], criterion: log_loss, feasibility_rule: {min_groups_per_class: 2, fallback: none}}`.

1. **Feasibility (`calibration_feasibility`):**
   - Every class must occur in at least 2 independent groups (topologies) of the development data.
   - Otherwise only `none` is allowed, and the reason is recorded in `calibration.json`.
   - Isotonic is not a candidate (sample size).
2. **Selection (`select_calibration`):**
   - Grouped cross-fitting over the development out-of-fold probabilities (`inner_group_splits` by topology).
   - Log loss and Brier score are computed for each candidate.
   - `sigmoid` is chosen only if it is **strictly** better than `none` on log loss; otherwise `none`.
3. **Sigmoid (`fit_calibrator`):**
   - One-vs-rest per class: `LogisticRegression(C=1e6)` on logit(p_k), clipped at eps 1e-6.
   - Calibrated rows are then renormalised.
   - A class with only positives or only negatives keeps its raw probability.
   - Rows with zero calibrated mass fall back to the raw row; the count is recorded.
4. **Development probabilities for later stages:** cross-fitted, so each topology is calibrated by a calibrator fitted on the other development topology.
5. **Outer test:** a calibrator fitted on all development out-of-fold probabilities is applied to the refitted model's outer probabilities. Outer labels are never used.

**Tests:**
- `test_primary_protocol::test_calibration_fallback_recorded` (forces `none` with `min_groups_per_class=3`);
- calibration tests in `test_baseline.py` and `test_phase6_components.py`.
