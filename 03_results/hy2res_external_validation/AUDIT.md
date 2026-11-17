# Data and time audit

- Parsed rows/columns: 300,768/23; timestamps are nondecreasing: True.
- Duplicate timestamp intervals: 21; exact 5-second intervals: 297,975; all other intervals: 2,792.
- `Breaks` markers: 20 OPEN and 20 CLOSE; paired: 20; unmatched OPEN/CLOSE: 0/0.
- Segmentation produced 2,793 segments; 4 measured intervals exceeded 60 seconds. Every row is retained, no gap is interpolated, and every non-5-second step begins a new segment.
- Channel missingness and documented/undocumented schema are listed in `channel_missingness.csv` and `schema_audit.csv`. Undocumented columns are excluded from prediction.
- The row-level validity mask and role/channel eligibility counts are saved as `validity_mask.csv.gz` and `validity_summary.csv`. A prediction is eligible only when its target and all lagged predictors are finite and all lags remain in the same segment.
- Target value ranges and variation are audited in `target_channel_audit.csv`; pres_pila and h2_flow_pila are constant zero throughout this source, so their zero-error metrics are uninformative.
- Coverage denominators are observed target rows in the applicable test period/regime.
