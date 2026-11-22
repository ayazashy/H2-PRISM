### T02 — Reference prediction benchmark

Frozen one-step references on held-out data, in native units (units never combined). Δ = Ridge − persistence; negative favours Ridge. HY2RES 'Ridge' is the contextual Ridge reference.

| study | channel | unit | scope | rows | persistence_MAE | ridge_MAE | persistence_RMSE | ridge_RMSE | delta_MAE | delta_RMSE |
|---|---|---|---|---|---|---|---|---|---|---|
| MHC | P-2 | barg | 3 held-out runs pooled | 15,885 | 0.1615 | 0.1759 | 0.3883 | 0.386 | 0.01443 | -0.002353 |
| MHC | P-2 | barg | run 24 | 4,940 | 0.1273 | 0.1472 | 0.3815 | 0.3807 | 0.01988 | -0.000771 |
| MHC | P-2 | barg | run 28 | 5,002 | 0.1505 | 0.1635 | 0.3171 | 0.3164 | 0.01303 | -0.000713 |
| MHC | P-2 | barg | run 29 | 5,943 | 0.1992 | 0.2103 | 0.4444 | 0.4398 | 0.01109 | -0.004526 |
| MHC | MFC-3 | ln/min | 3 held-out runs pooled | 15,885 | 0.03221 | 0.0429 | 0.2967 | 0.2964 | 0.01068 | -0.000279 |
| MHC | MFC-3 | ln/min | run 24 | 4,940 | 0.017 | 0.03106 | 0.2176 | 0.2178 | 0.01406 | 0.000116 |
| MHC | MFC-3 | ln/min | run 28 | 5,002 | 0.03771 | 0.04627 | 0.2952 | 0.2948 | 0.008558 | -0.000437 |
| MHC | MFC-3 | ln/min | run 29 | 5,943 | 0.04023 | 0.0499 | 0.3501 | 0.3497 | 0.00967 | -0.000382 |
| HY2RES | pres_buf | bar | test, overall | 43,168 | 0.003964 | 0.0055 | 0.01991 | 0.01714 | 0.001537 | -0.002771 |
| HY2RES | pres_buf | bar | test, electrolyzer_active | 42,367 | 0.003574 | 0.004973 | 0.0189 | 0.01647 | 0.0014 | -0.002434 |
| HY2RES | pres_buf | bar | test, multiple_active | 801 | 0.02459 | 0.03336 | 0.04959 | 0.03847 | 0.008765 | -0.01112 |
| HY2RES | pres_comp | bar | test, overall | 43,168 | 0.0256 | 0.02514 | 0.0506 | 0.0407 | -0.000456 | -0.009901 |
| HY2RES | pres_comp | bar | test, electrolyzer_active | 42,367 | 0.02564 | 0.02507 | 0.05064 | 0.04072 | -0.000577 | -0.009922 |
| HY2RES | pres_comp | bar | test, multiple_active | 801 | 0.02322 | 0.02913 | 0.04819 | 0.03944 | 0.005912 | -0.00875 |
| HY2RES | h2_flow | NL/h | test, overall | 43,168 | 0.03273 | 0.178 | 1.257 | 1.185 | 0.1453 | -0.07171 |
| HY2RES | h2_flow | NL/h | test, electrolyzer_active | 42,367 | 0.03139 | 0.1717 | 1.269 | 1.193 | 0.1403 | -0.07555 |
| HY2RES | h2_flow | NL/h | test, multiple_active | 801 | 0.1036 | 0.5116 | 0.1347 | 0.6465 | 0.408 | 0.5118 |

Source: `study_b/.../replayed_predictions.csv.gz, run_metrics.csv`; `hy2res publication/TABLE_2_HELD_OUT.csv` · Script: `publication_q1/scripts/build_tables.py`
