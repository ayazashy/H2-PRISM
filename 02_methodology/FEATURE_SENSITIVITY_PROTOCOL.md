# Feature Sensitivity Protocol (A15)

- **Status:** module IMPLEMENTED and TESTED (`src/h2prism/experiments/feature_sensitivity.py`, `tests/test_feature_sensitivity.py`). Split out of `SUPPORTING_MODEL_SPECS_A14_A16.md` §A15.
- **Registered path in the primary protocol:** the offset-invariant arm is pre-registered as sensitivity analysis `offset_invariant_features`. It **runs through the primary runner** (`--execute-sensitivity --sensitivity offset_invariant_features`), with the same folds, D(x), policy and gate (`SENSITIVITY_ANALYSIS_SPEC.md`). Real structural dry run: 27/27 checks, 80 features.
- **The A15 module** (rule-resolved arms `all`, `offset_invariant`, `explicit`; RF baseline only) remains an EXPLORATORY_SECONDARY tool. Its outputs cannot choose the primary feature set.
- **Before any additional A15 arm runs on held-out data:** Faisal approves the arm list and Yazan confirms channels and units. Not done.
- **Motivation:** limitation L5 (run fingerprint of absolute-level features).
