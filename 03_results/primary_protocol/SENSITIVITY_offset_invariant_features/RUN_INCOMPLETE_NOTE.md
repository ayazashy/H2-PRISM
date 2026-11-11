# Run incomplete: offset_invariant_features (run_key ff9cc78ab2ca)

- **Status:** EXECUTED, INCOMPLETE.
- **Authorization:** `06_audit_preparation/sensitivity_authorizations/EXECUTION_AUTHORIZATION_SENSITIVITY_offset_invariant_features.yaml`, given by the project lead on 2026-11-11.
- **Manifest:** `run_manifest.json` still records `RUNNING` because the runner stopped. The file is left exactly as the runner wrote it.

## What happened

- Folds 1 (Center) and 2 (Downstream) completed (`folds/fold_*/DONE.json`).
- Fold 3 (Upstream held out; development data = Center and Downstream) stopped in the development stage with:
  `ValueError: development data contain a single correctness outcome; meta-model not estimable`
  (`h2prism.combined_score.fit_combined_score`; log: `logs/SENSITIVITY_offset_invariant_features_run.log`).
- **Cause:** the registered combined score s_C is a logistic meta-model of development correctness. With only the five offset-invariant statistics, every development out-of-fold prediction in fold 3 had the same correctness outcome, so the meta-model cannot be fitted.

## Why it is not "fixed"

- The runner is deterministic, so a rerun reproduces the same stop.
- Continuing would require a new rule, for example "s_C not estimable in this fold". That would be a protocol amendment, so it is not made here.
- No aggregate RQ1/RQ2 tables exist for this analysis. A pooled result requires all three folds.

## What can be used, descriptively only

- **Fold 1 (Center held out):** accuracy 0.035. NORMAL is predicted for every class except 336 NORMAL windows, which are predicted LEAK. R2 accuracy was 0.213.
- **Fold 2 (Downstream held out):** accuracy 0.783. LEAK is predicted for every window. R2 accuracy was 0.929.
- **Interpretation:** removing absolute-level statistics does not restore cross-topology transfer. This is evidence against absolute-level run fingerprints being the main cause of the Center failure, and consistent with the source-dataset configuration swap (L12 / R-18), which remains visible in variability statistics of active versus inactive channels.

Window-level fold outputs are kept locally. Their SHA-256 values are listed in `logs/SENSITIVITY_offset_invariant_features_OUTPUT_HASHES.sha256`.
