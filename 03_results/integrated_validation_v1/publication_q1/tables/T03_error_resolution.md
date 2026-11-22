### T03 — Errors and recording resolution

Errors divided by the observed recording increment (dimensionless). The increment is recorded quantization, not instrument resolution or accuracy (undocumented in both sources).

| study | channel | unit | recording_increment | on_grid_fraction | persistence_exact_share | persistence_MAE_incr | ridge_MAE_incr | persistence_RMSE_incr | ridge_RMSE_incr | delta_MAE_incr | delta_RMSE_incr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MHC | P-2 | barg | 0.2 | 1 | 0.7058 | 0.8075 | 0.8797 | 1.942 | 1.93 | 0.07217 | -0.01177 |
| MHC | MFC-3 | ln/min | 0.01 | 1 | 0.9071 | 3.221 | 4.29 | 29.67 | 29.64 | 1.068 | -0.02791 |
| HY2RES | pres_buf | bar | 0.1 | 1 | 0.9604 | 0.03964 | 0.055 | 0.1991 | 0.1714 | 0.01537 | -0.02771 |
| HY2RES | pres_comp | bar | 0.1 | 1 | 0.744 | 0.256 | 0.2514 | 0.506 | 0.407 | -0.004562 | -0.09901 |

Source: `study_b/.../analysis/resolution.csv`; `hy2res .../analysis/quantization_comparison.csv, recording_grid.csv` · Script: `publication_q1/scripts/build_tables.py`
