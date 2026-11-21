# TAB_03 — Historical event-window model comparison

All 39 scored scenarios carry LEAK annotations; recall denominator is fixed.

| variant | model | hits | cases | recall |
| --- | --- | --- | --- | --- |
| defaults_sensitivity | linear_svm | 24 | 39 | 0.615385 |
| defaults_sensitivity | rbf_svm | 0 | 39 | 0 |
| defaults_sensitivity | xgboost | 39 | 39 | 1 |
| flow | linear_svm | 23 | 39 | 0.589744 |
| flow | logistic | 25 | 39 | 0.641026 |
| flow | random_forest | 37 | 39 | 0.948718 |
| flow | rbf_svm | 23 | 39 | 0.589744 |
| flow | xgboost | 39 | 39 | 1 |
| full | linear_svm | 33 | 39 | 0.846154 |
| full | logistic | 30 | 39 | 0.769231 |
| full | random_forest | 36 | 39 | 0.923077 |
| full | rbf_svm | 23 | 39 | 0.589744 |
| full | xgboost | 39 | 39 | 1 |
| pressure | linear_svm | 26 | 39 | 0.666667 |
| pressure | logistic | 27 | 39 | 0.692308 |
| pressure | random_forest | 36 | 39 | 0.923077 |
| pressure | rbf_svm | 20 | 39 | 0.512821 |
| pressure | xgboost | 39 | 39 | 1 |
