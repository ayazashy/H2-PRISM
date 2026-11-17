# Frozen prediction protocol

- Target: each publisher-defined pressure/flow channel at the next verified 5-second sample, using measurements available through the preceding sample only.
- Persistence baseline: last available value of the target channel.
- Single candidate: per-channel Ridge regression (alpha 10), standardized features and target; lag 1–3 target pressures/flows and documented equipment powers.
- Chronological roles and embargo are recorded in `split_manifest.csv`; the complete protocol and cutoffs are in `protocol.json`.
- Model selection used validation only: Validation selected **contextual_ridge** (mean contextual-to-persistence RMSE ratio 0.8784 across 3/5 channels with nonzero persistence RMSE; +12.16% reduction by the selection statistic). Other channels had undefined ratios because persistence RMSE was zero.
- Final test transforms/model were fitted without test rows; the test was scored once. Operating-regime results are descriptive and use equipment-power state at t-1.
- No predictions bridge OPEN/CLOSE markers, duplicate timestamps, or any interval other than 5 seconds. Missing values are not imputed.
