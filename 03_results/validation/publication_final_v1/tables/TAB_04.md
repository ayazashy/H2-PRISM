# TAB_04 — Frozen 120 s decision replay

Episode counts and rates use the archived observation duration.

| model | mode | scenarios | events | false_episodes | inactive_hours | new_alert_detections | active_positive_detections | median_alarm_delay_s | missed_events | false_episodes_per_inactive_hour |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| always_event | clean | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| always_event | correlated_noise | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| always_event | delayed | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| always_event | drift | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| always_event | stuck | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| always_event | white_noise | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| linear_svm | clean | 51 | 48 | 2 | 65.6283 | 37 | 37 | 84 | 11 | 0.0304746 |
| linear_svm | correlated_noise | 51 | 48 | 230 | 65.6283 | 48 | 48 | 699 | 0 | 3.50458 |
| linear_svm | delayed | 51 | 48 | 17 | 65.6283 | 35 | 37 | 84 | 13 | 0.259034 |
| linear_svm | drift | 51 | 48 | 2 | 65.6283 | 37 | 37 | 84 | 11 | 0.0304746 |
| linear_svm | stuck | 51 | 48 | 15 | 65.6283 | 18 | 20 | 64 | 30 | 0.22856 |
| linear_svm | white_noise | 51 | 48 | 175 | 65.6283 | 40 | 40 | 624 | 8 | 2.66653 |
| logistic | clean | 51 | 48 | 10 | 65.6283 | 42 | 42 | 84 | 6 | 0.152373 |
| logistic | correlated_noise | 51 | 48 | 213 | 65.6283 | 48 | 48 | 699 | 0 | 3.24555 |
| logistic | delayed | 51 | 48 | 24 | 65.6283 | 39 | 41 | 84 | 9 | 0.365696 |
| logistic | drift | 51 | 48 | 7 | 65.6283 | 40 | 40 | 84 | 8 | 0.106661 |
| logistic | stuck | 51 | 48 | 14 | 65.6283 | 21 | 23 | 84 | 27 | 0.213322 |
| logistic | white_noise | 51 | 48 | 91 | 65.6283 | 43 | 43 | 699 | 5 | 1.3866 |
| majority | clean | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| majority | correlated_noise | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| majority | delayed | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| majority | drift | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| majority | stuck | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| majority | white_noise | 51 | 48 | 51 | 65.6283 | 0 | 48 | — | 48 | 0.777103 |
| random_forest | clean | 51 | 48 | 16 | 65.6283 | 48 | 48 | 84 | 0 | 0.243797 |
| random_forest | correlated_noise | 51 | 48 | 400 | 65.6283 | 48 | 48 | 84 | 0 | 6.09493 |
| random_forest | delayed | 51 | 48 | 16 | 65.6283 | 48 | 48 | 84 | 0 | 0.243797 |
| random_forest | drift | 51 | 48 | 7 | 65.6283 | 48 | 48 | 84 | 0 | 0.106661 |
| random_forest | stuck | 51 | 48 | 37 | 65.6283 | 43 | 48 | 84 | 5 | 0.563781 |
| random_forest | white_noise | 51 | 48 | 374 | 65.6283 | 47 | 48 | 84 | 1 | 5.69876 |
| rbf_svm | clean | 51 | 48 | 6 | 65.6283 | 30 | 30 | 84 | 18 | 0.0914239 |
| rbf_svm | correlated_noise | 51 | 48 | 45 | 65.6283 | 0 | 42 | — | 48 | 0.685679 |
| rbf_svm | delayed | 51 | 48 | 20 | 65.6283 | 30 | 30 | 84 | 18 | 0.304746 |
| rbf_svm | drift | 51 | 48 | 4 | 65.6283 | 30 | 30 | 84 | 18 | 0.0609493 |
| rbf_svm | stuck | 51 | 48 | 44 | 65.6283 | 30 | 30 | 84 | 18 | 0.670442 |
| rbf_svm | white_noise | 51 | 48 | 45 | 65.6283 | 0 | 42 | — | 48 | 0.685679 |
| xgboost | clean | 51 | 48 | 6 | 65.6283 | 41 | 42 | 84 | 7 | 0.0914239 |
| xgboost | correlated_noise | 51 | 48 | 345 | 65.6283 | 48 | 48 | 219 | 0 | 5.25688 |
| xgboost | delayed | 51 | 48 | 42 | 65.6283 | 41 | 42 | 84 | 7 | 0.639967 |
| xgboost | drift | 51 | 48 | 15 | 65.6283 | 44 | 48 | 99 | 4 | 0.22856 |
| xgboost | stuck | 51 | 48 | 69 | 65.6283 | 19 | 42 | 84 | 29 | 1.05138 |
| xgboost | white_noise | 51 | 48 | 260 | 65.6283 | 48 | 48 | 204 | 0 | 3.9617 |
