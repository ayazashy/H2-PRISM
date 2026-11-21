### TAB_H01 — Dataset and recording integrity

Full source (300,768 rows). Recording increment = smallest step between distinct recorded values.

| channel | unit | valid_rows | missing_rows | distinct_values | minimum | maximum | smallest_positive_step | modal_step | on_0p1_grid_fraction | off_grid_rows | decimals_observed | source | interval_definition | causal_segments | qualification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pres_buf | bar | 300767 | 1 | 64 | 28 | 34.3 | 0.1 | 0.1 | 1 | 0 | 1 | Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…) | 5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps | 2793 | 0.1 bar recording grid; instrument resolution/accuracy undocumented |
| pres_comp | bar | 300767 | 1 | 263 | 84.5 | 110.7 | 0.1 | 0.1 | 1 | 0 | 1 | Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…) | 5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps | 2793 | 0.1 bar recording grid; instrument resolution/accuracy undocumented |
| h2_flow | NL/h | 300767 | 1 | 25465 | 0 | 376.9 | 0.0005 | 0.001 | 0.897598 | 30799 | 15 | Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…) | 5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps | 2793 | not quantised at 0.1; normalised volumetric production over preceding interval |


### TAB_H02 — Quantisation and frozen prediction comparison

Archived frozen predictions on the shared 43,168-row mask (409 segments). Increment units are descriptive ratios to the 0.1 bar recording increment.

| channel | unit | recording_increment | n | segments | persistence_exact_hits | persistence_exact_rate | nonzero_step_rows | nonzero_step_rate | persistence_mae | ridge_mae | delta_mae | rel_delta_mae | persistence_rmse | ridge_rmse | delta_rmse | rel_delta_rmse | persistence_mae_incr | ridge_mae_incr | persistence_rmse_incr | ridge_rmse_incr | delta_mae_incr | delta_rmse_incr | persistence_signed_mean | ridge_signed_mean | ridge_on_grid_fraction | ridge_equals_recorded_value |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pres_buf | bar | 0.1 | 43168 | 409 | 41457 | 0.960364 | 1711 | 0.0396358 | 0.00396358 | 0.0055002 | 0.00153662 | 0.387684 | 0.0199088 | 0.0171375 | -0.00277123 | -0.139197 | 0.0396358 | 0.055002 | 0.199088 | 0.171375 | 0.0153662 | -0.0277123 | 3.01149e-05 | -5.87682e-05 | 0 | 0 |
| pres_comp | bar | 0.1 | 43168 | 409 | 32119 | 0.744047 | 11049 | 0.255953 | 0.0255977 | 0.0251415 | -0.000456179 | -0.0178211 | 0.0505987 | 0.0406982 | -0.00990053 | -0.195668 | 0.255977 | 0.251415 | 0.505987 | 0.406982 | -0.00456179 | -0.0990053 | -6.02298e-05 | -0.000229063 | 0 | 0 |


### TAB_H03 — Error contribution by recorded target step

Step class = (y_t − y_{t−1}) / 0.1 bar. Ridge predictions are not rounded.

| channel | step_class | n | share_rows | persistence_mae | ridge_mae | persistence_sse | ridge_sse | persistence_sse_share | ridge_sse_share | delta_sse | delta_sse_share_of_net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pres_buf | 0 (unchanged) | 41457 | 0.960364 | 0 | 0.00281801 | 0 | 3.23028 | 0 | 0.25479 | 3.23028 | -0.728888 |
| pres_buf | ±1 increment | 1711 | 0.0396358 | 0.1 | 0.0704888 | 17.11 | 9.44792 | 1 | 0.74521 | -7.66208 | 1.72889 |
| pres_buf | ±2 increments | 0 | 0 | — | — | 0 | 0 | 0 | 0 | 0 | -0 |
| pres_buf | ≥3 increments | 0 | 0 | — | — | 0 | 0 | 0 | 0 | 0 | -0 |
| pres_comp | 0 (unchanged) | 32119 | 0.744047 | 0 | 0.0110094 | 0 | 15.1672 | 0 | 0.212126 | 15.1672 | -0.388713 |
| pres_comp | ±1 increment | 11048 | 0.25593 | 0.1 | 0.0662169 | 110.48 | 56.3161 | 0.999638 | 0.787627 | -54.1639 | 1.38814 |
| pres_comp | ±2 increments | 1 | 2.31653e-05 | 0.2 | 0.132844 | 0.04 | 0.0176475 | 0.000361925 | 0.000246814 | -0.0223525 | 0.000572862 |
| pres_comp | ≥3 increments | 0 | 0 | — | — | 0 | 0 | 0 | 0 | 0 | -0 |


### TAB_H04 — Chronological distributions by frozen partition

Raw source values per partition (origin lags not applied). dev_rule_min/max are the frozen rule's support limits (development origin rows with finite inputs and known power).

| partition | channel | unit | start | end | rows | valid_rows | missing_rows | segments | minimum | p01 | p05 | median | p95 | p99 | maximum | dev_rule_min | dev_rule_max | above_dev_max_rate | below_dev_min_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | pres_buf | bar | 2024-03-27 11:34:27 | 2024-04-09 02:34:59 | 210537 | 210537 | 0 | 1940 | 28 | 28 | 28.6 | 29.8 | 33.4 | 33.8 | 34.3 | 28 | 34.3 | 0 | 0 |
| development | pres_comp | bar | 2024-03-27 11:34:27 | 2024-04-09 02:34:59 | 210537 | 210537 | 0 | 1940 | 84.5 | 85.9 | 87.5 | 94.2 | 105.7 | 106.1 | 106.6 | 84.5 | 106.6 | 0 | 0 |
| development | h2_flow | NL/h | 2024-03-27 11:34:27 | 2024-04-09 02:34:59 | 210537 | 210537 | 0 | 1940 | 0 | 0 | 0 | 0 | 336.595 | 354.31 | 376.9 | 0 | 376.9 | 0 | 0 |
| validation | pres_buf | bar | 2024-04-09 03:35:05 | 2024-04-12 11:13:50 | 44396 | 44396 | 0 | 429 | 28.3 | 28.3 | 28.4 | 28.9 | 29.4 | 29.4 | 29.5 | 28 | 34.3 | 0 | 0 |
| validation | pres_comp | bar | 2024-04-09 03:35:05 | 2024-04-12 11:13:50 | 44396 | 44396 | 0 | 429 | 100.2 | 100.3 | 100.5 | 102.4 | 104.8 | 104.8 | 104.9 | 84.5 | 106.6 | 0 | 0 |
| validation | h2_flow | NL/h | 2024-04-09 03:35:05 | 2024-04-12 11:13:50 | 44396 | 44396 | 0 | 429 | 0 | 0 | 0 | 0 | 0 | 0 | 119.181 | 0 | 376.9 | 0 | 0 |
| embargo | pres_buf | bar | 2024-04-09 02:35:04 | 2024-04-12 12:13:51 | 1438 | 1438 | 0 | 14 | 28.4 | 28.4 | 28.4 | 29 | 30 | 30.2 | 30.3 | 28 | 34.3 | 0 | 0 |
| embargo | pres_comp | bar | 2024-04-09 02:35:04 | 2024-04-12 12:13:51 | 1438 | 1438 | 0 | 14 | 100.5 | 100.6 | 100.6 | 101.75 | 103.7 | 103.8 | 103.8 | 84.5 | 106.6 | 0 | 0 |
| embargo | h2_flow | NL/h | 2024-04-09 02:35:04 | 2024-04-12 12:13:51 | 1438 | 1438 | 0 | 14 | 0 | 0 | 0 | 0 | 254.922 | 302.984 | 316.67 | 0 | 376.9 | 0 | 0 |
| test | pres_buf | bar | 2024-04-12 12:13:56 | 2024-04-15 02:00:00 | 44397 | 44396 | 1 | 414 | 28.9 | 29.3 | 29.6 | 30.8 | 33 | 33.6 | 34 | 28 | 34.3 | 0 | 0 |
| test | pres_comp | bar | 2024-04-12 12:13:56 | 2024-04-15 02:00:00 | 44397 | 44396 | 1 | 414 | 103.8 | 104.3 | 105.7 | 107.8 | 110.5 | 110.6 | 110.7 | 84.5 | 106.6 | 0.718263 | 0 |
| test | h2_flow | NL/h | 2024-04-12 12:13:56 | 2024-04-15 02:00:00 | 44397 | 44396 | 1 | 414 | 0 | 0 | 0 | 0 | 328.385 | 343.718 | 361.537 | 0 | 376.9 | 0 | 0 |


### TAB_H05 — Development-support failure attribution (test rows)

Denominator 44,397 test rows; unresolved 32,308. Non-exclusive per channel/condition; primary_reason_rows is the exclusive count.

| channel | condition | rows | fraction_of_test | fraction_of_unresolved | overlap_with_other_channel_outside | segments | primary_reason_rows | max_excess |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pres_buf | below | 0 | 0 | 0 | 0 | 0 | — | — |
| pres_buf | above | 0 | 0 | 0 | 0 | 0 | — | — |
| pres_buf | outside | 0 | 0 | 0 | 0 | 0 | 0 | — |
| pres_buf | nonfinite | 413 | 0.00930243 | 0.0127832 | 0 | 413 | — | — |
| pres_comp | below | 0 | 0 | 0 | 0 | 0 | — | — |
| pres_comp | above | 31589 | 0.711512 | 0.977745 | 0 | 299 | — | 4.1 |
| pres_comp | outside | 31589 | 0.711512 | 0.977745 | 0 | 299 | 31589 | 4.1 |
| pres_comp | nonfinite | 413 | 0.00930243 | 0.0127832 | 0 | 413 | — | — |
| h2_flow | below | 0 | 0 | 0 | 0 | 0 | — | — |
| h2_flow | above | 0 | 0 | 0 | 0 | 0 | — | — |
| h2_flow | outside | 0 | 0 | 0 | 0 | 0 | 0 | — |
| h2_flow | nonfinite | 413 | 0.00930243 | 0.0127832 | 0 | 413 | — | — |


### TAB_H05b — Exact violation combinations among unresolved rows

Each unresolved row appears once.

| combo | rows | segments | fraction_of_unresolved |
| --- | --- | --- | --- |
| pres_comp | 31589 | 299 | 0.977745 |
| nonfinite | 413 | 413 | 0.0127832 |
| none | 306 | 3 | 0.00947134 |


### TAB_H06 — Decision taxonomy (frozen decision + additive reason)

Frozen decision labels are unchanged; primary_reason is reconstructed with documented precedence.

| decision | primary_reason | rows | segments | electrolyzer_only | compressor_powered | unknown_power | pct_of_test_rows | pct_of_unresolved |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ambiguous | — | 1327 | 15 | 1126 | 201 | 0 | 0.0298894 | — |
| Electrolyzer only | — | 10762 | 106 | 10762 | 0 | 0 | 0.242404 | — |
| Unresolved | EMPTY_CELL (no state with >=2 development segments) | 306 | 3 | 306 | 0 | 0 | 0.00689236 | 0.00947134 |
| Unresolved | INVALID_INPUT (nonfinite origin measurement) | 413 | 413 | 0 | 0 | 413 | 0.00930243 | 0.0127832 |
| Unresolved | OUT_OF_SUPPORT (pres_comp) | 31589 | 299 | 30973 | 616 | 0 | 0.711512 | 0.977745 |


### TAB_H07 — Operating-state decision outcomes

Power-defined labels at the forecast origin; not fault labels. majority_baseline_agree = rows a constant 'electrolyzer only' rule would match.

| state | rows | segments | specific | specific_correct | ambiguous | unresolved | unresolved_out_of_support | unresolved_invalid | unresolved_empty_cell | majority_baseline_agree |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| electrolyzer_active | 43167 | 405 | 10762 | 10762 | 1126 | 31279 | 30973 | 0 | 306 | 43167 |
| multiple_active | 817 | 12 | 0 | 0 | 201 | 616 | 616 | 0 | 0 | 0 |
| unknown | 413 | 413 | 0 | 0 | 0 | 413 | 0 | 413 | 0 | 0 |


### TAB_H08 — Empirical distinguishability (rank probability)

P(compressor-state value > electrolyzer-only value) + ½ P(tie); descriptive.

| pair | channel | unit | flow_rule | n_electrolyzer_only | n_compressor | segments_electrolyzer_only | segments_compressor | rank_probability | exact_value_overlap | compressor_min | compressor_max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| compressor-powered vs electrolyzer only | pres_buf | bar | all rows | 43167 | 817 | 405 | 12 | 0.582997 | 0.5599 | 29 | 34 |
| compressor-powered vs electrolyzer only | pres_buf | bar | positive flow only | 5353 | 817 | 55 | 12 | 0.465438 | 0.900475 | 29 | 34 |
| compressor-powered vs electrolyzer only | pres_comp | bar | all rows | 43167 | 817 | 405 | 12 | 0.527531 | 0.576883 | 104.7 | 110.4 |
| compressor-powered vs electrolyzer only | pres_comp | bar | positive flow only | 5353 | 817 | 55 | 12 | 0.494166 | 0.332266 | 104.7 | 110.4 |
| compressor-powered vs electrolyzer only | h2_flow | NL/h | all rows | 43167 | 817 | 405 | 12 | 0.944746 | 0.00553664 | 318.704 | 338.969 |
| compressor-powered vs electrolyzer only | h2_flow | NL/h | positive flow only | 5353 | 817 | 55 | 12 | 0.554427 | 0.0446479 | 318.704 | 338.969 |


### TAB_H09 — Claims and evidence qualification

Project evidence vocabulary.

| claim | evidence | numerical_result | layer | qualification | establishes | does_not_establish |
| --- | --- | --- | --- | --- | --- | --- |
| Source identity | MD5/size of restored source | 38,621,947 bytes, MD5 9a3c3e3b… | Layer I | VERIFIED WITHIN SCOPE | Exact official file | Calibration or synchronisation |
| Pressure recording grid | TAB_H01 | both pressures 100 % on 0.1 bar grid | Layer I | NUMERICALLY VERIFIED | Errors must be read against 0.1 bar | Instrument accuracy |
| Ridge vs persistence | TAB_H02/H03 | buffer ΔMAE +0.015 incr., ΔRMSE −0.028 incr.; tank −0.005/−0.099 | Layer II | DESCRIPTIVELY SUPPORTED | Ridge partly anticipates single 0.1 bar steps | Practical superiority; new held-out claim |
| Tank-pressure drift | TAB_H04, FIG_H04 | dev max 106.6 bar; 71.8 % of test source rows above | Layer II | DESCRIPTIVELY SUPPORTED | Test period outside development support | Physical cause |
| Unresolved mechanism | TAB_H06 | 31,589 / 32,308 unresolved = tank out of support | Layer II | NUMERICALLY VERIFIED (reconciled) | Abstention reflects domain shift, not state ambiguity | That abstention is diagnostically correct |
| Minority state | TAB_H07 | 0 of 817 compressor rows specific | Layer II | DESCRIPTIVELY SUPPORTED | Rule cannot recognise the minority state | Compressor fault detection |
| Positive-flow distinction | TAB_H08 | flow rank probability 0.945 → 0.554 | Layer II | DESCRIPTIVELY SUPPORTED | Separation is zero vs positive production | Classification accuracy |
| Formal D(Y) | source scope | no qualified bounds, fault library, labels or locations | Layer III | NOT ESTABLISHED | Formal D(Y) not established for HY2RES | Any exclusion or certified diagnosis |
| Fault / leak / localization / transfer | source scope | no truth | Layer III | BLOCKED BY EVIDENCE | None | Any accuracy, localization or generalisation claim |


### TAB_H00a — Gate B — archived metric reconciliation

Recomputed from archived predictions; tolerance 1e-12 relative.

| target | state | metric | n | frozen | recomputed | abs_diff | passed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| h2_flow | overall | persistence_mae | 43168 | 0.0327303 | 0.0327303 | 7.63278e-17 | True |
| h2_flow | overall | persistence_rmse | 43168 | 1.25697 | 1.25697 | 0 | True |
| h2_flow | overall | contextual_ridge_mae | 43168 | 0.178005 | 0.178005 | 8.32667e-17 | True |
| h2_flow | overall | contextual_ridge_rmse | 43168 | 1.18526 | 1.18526 | 0 | True |
| h2_flow | electrolyzer_active | persistence_mae | 42367 | 0.0313912 | 0.0313912 | 6.93889e-17 | True |
| h2_flow | electrolyzer_active | persistence_rmse | 42367 | 1.26866 | 1.26866 | 0 | True |
| h2_flow | electrolyzer_active | contextual_ridge_mae | 42367 | 0.171699 | 0.171699 | 2.77556e-17 | True |
| h2_flow | electrolyzer_active | contextual_ridge_rmse | 42367 | 1.1931 | 1.1931 | 0 | True |
| h2_flow | multiple_active | persistence_mae | 801 | 0.103561 | 0.103561 | 6.93889e-17 | True |
| h2_flow | multiple_active | persistence_rmse | 801 | 0.134692 | 0.134692 | 0 | True |
| h2_flow | multiple_active | contextual_ridge_mae | 801 | 0.511564 | 0.511564 | 0 | True |
| h2_flow | multiple_active | contextual_ridge_rmse | 801 | 0.646516 | 0.646516 | 0 | True |
| h2_flow_pila | overall | persistence_mae | 43168 | 0 | 0 | 0 | True |
| h2_flow_pila | overall | persistence_rmse | 43168 | 0 | 0 | 0 | True |
| h2_flow_pila | overall | contextual_ridge_mae | 43168 | 0 | 0 | 0 | True |
| h2_flow_pila | overall | contextual_ridge_rmse | 43168 | 0 | 0 | 0 | True |
| h2_flow_pila | electrolyzer_active | persistence_mae | 42367 | 0 | 0 | 0 | True |
| h2_flow_pila | electrolyzer_active | persistence_rmse | 42367 | 0 | 0 | 0 | True |
| h2_flow_pila | electrolyzer_active | contextual_ridge_mae | 42367 | 0 | 0 | 0 | True |
| h2_flow_pila | electrolyzer_active | contextual_ridge_rmse | 42367 | 0 | 0 | 0 | True |
| h2_flow_pila | multiple_active | persistence_mae | 801 | 0 | 0 | 0 | True |
| h2_flow_pila | multiple_active | persistence_rmse | 801 | 0 | 0 | 0 | True |
| h2_flow_pila | multiple_active | contextual_ridge_mae | 801 | 0 | 0 | 0 | True |
| h2_flow_pila | multiple_active | contextual_ridge_rmse | 801 | 0 | 0 | 0 | True |
| pres_buf | overall | persistence_mae | 43168 | 0.00396358 | 0.00396358 | 4.77049e-17 | True |
| pres_buf | overall | persistence_rmse | 43168 | 0.0199088 | 0.0199088 | 5.55112e-17 | True |
| pres_buf | overall | contextual_ridge_mae | 43168 | 0.0055002 | 0.0055002 | 4.77049e-17 | True |
| pres_buf | overall | contextual_ridge_rmse | 43168 | 0.0171375 | 0.0171375 | 9.02056e-17 | True |
| pres_buf | electrolyzer_active | persistence_mae | 42367 | 0.00357354 | 0.00357354 | 5.89806e-17 | True |
| pres_buf | electrolyzer_active | persistence_rmse | 42367 | 0.0189038 | 0.0189038 | 3.46945e-17 | True |
| pres_buf | electrolyzer_active | contextual_ridge_mae | 42367 | 0.0049735 | 0.0049735 | 5.11743e-17 | True |
| pres_buf | electrolyzer_active | contextual_ridge_rmse | 42367 | 0.0164702 | 0.0164702 | 3.1225e-17 | True |
| pres_buf | multiple_active | persistence_mae | 801 | 0.0245943 | 0.0245943 | 4.51028e-17 | True |
| pres_buf | multiple_active | persistence_rmse | 801 | 0.0495926 | 0.0495926 | 1.38778e-17 | True |
| pres_buf | multiple_active | contextual_ridge_mae | 801 | 0.033359 | 0.033359 | 5.55112e-17 | True |
| pres_buf | multiple_active | contextual_ridge_rmse | 801 | 0.0384695 | 0.0384695 | 2.77556e-17 | True |
| pres_comp | overall | persistence_mae | 43168 | 0.0255977 | 0.0255977 | 5.89806e-17 | True |
| pres_comp | overall | persistence_rmse | 43168 | 0.0505987 | 0.0505987 | 8.32667e-17 | True |
| pres_comp | overall | contextual_ridge_mae | 43168 | 0.0251415 | 0.0251415 | 5.55112e-17 | True |
| pres_comp | overall | contextual_ridge_rmse | 43168 | 0.0406982 | 0.0406982 | 6.93889e-17 | True |
| pres_comp | electrolyzer_active | persistence_mae | 42367 | 0.0256426 | 0.0256426 | 5.55112e-17 | True |
| pres_comp | electrolyzer_active | persistence_rmse | 42367 | 0.0506432 | 0.0506432 | 4.85723e-17 | True |
| pres_comp | electrolyzer_active | contextual_ridge_mae | 42367 | 0.025066 | 0.025066 | 1.04083e-17 | True |
| pres_comp | electrolyzer_active | contextual_ridge_rmse | 42367 | 0.0407216 | 0.0407216 | 6.93889e-17 | True |
| pres_comp | multiple_active | persistence_mae | 801 | 0.023221 | 0.023221 | 2.77556e-17 | True |
| pres_comp | multiple_active | persistence_rmse | 801 | 0.0481881 | 0.0481881 | 1.38778e-17 | True |
| pres_comp | multiple_active | contextual_ridge_mae | 801 | 0.029133 | 0.029133 | 6.59195e-17 | True |
| pres_comp | multiple_active | contextual_ridge_rmse | 801 | 0.039438 | 0.039438 | 8.32667e-17 | True |
| pres_pila | overall | persistence_mae | 43168 | 0 | 0 | 0 | True |
| pres_pila | overall | persistence_rmse | 43168 | 0 | 0 | 0 | True |
| pres_pila | overall | contextual_ridge_mae | 43168 | 0 | 0 | 0 | True |
| pres_pila | overall | contextual_ridge_rmse | 43168 | 0 | 0 | 0 | True |
| pres_pila | electrolyzer_active | persistence_mae | 42367 | 0 | 0 | 0 | True |
| pres_pila | electrolyzer_active | persistence_rmse | 42367 | 0 | 0 | 0 | True |
| pres_pila | electrolyzer_active | contextual_ridge_mae | 42367 | 0 | 0 | 0 | True |
| pres_pila | electrolyzer_active | contextual_ridge_rmse | 42367 | 0 | 0 | 0 | True |
| pres_pila | multiple_active | persistence_mae | 801 | 0 | 0 | 0 | True |
| pres_pila | multiple_active | persistence_rmse | 801 | 0 | 0 | 0 | True |
| pres_pila | multiple_active | contextual_ridge_mae | 801 | 0 | 0 | 0 | True |
| pres_pila | multiple_active | contextual_ridge_rmse | 801 | 0 | 0 | 0 | True |


### TAB_H00b — Gate C — frozen decision reproduction

Replica of the frozen rule against published counts.

| label | decision | frozen | reproduced | passed |
| --- | --- | --- | --- | --- |
| electrolyzer_active | Electrolyzer only | 10762 | 10762 | True |
| electrolyzer_active | Ambiguous | 1126 | 1126 | True |
| electrolyzer_active | Unresolved | 31279 | 31279 | True |
| multiple_active | Ambiguous | 201 | 201 | True |
| multiple_active | Unresolved | 616 | 616 | True |
| unknown | Unresolved | 413 | 413 | True |
| all | out of range or nonfinite | 32002 | 32002 | True |
