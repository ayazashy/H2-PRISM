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
