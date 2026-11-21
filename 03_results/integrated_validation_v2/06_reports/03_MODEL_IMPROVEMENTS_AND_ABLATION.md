# Model improvements and ablation

**No model or D(x) variant was changed or refit in this round.** The only evaluation data are inspected windows with disputed labels. Any gain found there could not be separated from leakage or label effects (Part 19).

## Ablation evidence
- v1 matched ablation, s_C vs s_C − D at coverage 0.25: risk 0.146 vs 0.152; ancestor interval [-0.044, 0.023].
- v2 incremental utility, leave-one-template-out (V2-T01):

| model | oof_log_loss | oof_brier | oof_auroc | groups | errors |
|---|---|---|---|---|---|
| conf | 0.906 | 0.136 | 0.177 | 16 | 1741 |
| conf+D | 0.995 | 0.144 | 0.243 | 16 | 1741 |
| conf+margin+negH | 0.693 | 0.0762 | 0.705 | 16 | 1741 |
| conf+margin+negH+D | 0.828 | 0.0899 | 0.704 | 16 | 1741 |

- Registered sensitivities (k = 10, 50; clean realization; prior-corrected D; 60 s windows) are all NOT_ESTIMABLE (`x4_registered_sensitivities.csv`).
- Synthetic method check (V2-T02): D lowers log-loss only for the classifier blind to an informative feature. Δ = -0.006, -0.023, -0.046 at separations 0.5, 1, 2.

## Why D(x) shows no value here
- The classifier already uses the same feature space that D summarises, so D is largely redundant with confidence.
- Where D differs from confidence, it follows the source-model artifact (L17), not correctness.

## Defensible next improvement
After D1 and D2: compute D on a common-sensor representation, and evaluate on templates absent from development.
