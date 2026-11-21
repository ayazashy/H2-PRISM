### V2-T01_dx_incremental_utility — D(x) incremental utility (leave-one-template-out)

Correctness models on frozen scores; groups = scenario templates; EXPLORATORY (disputed labels, inspected windows).

| model | oof_log_loss | oof_brier | oof_auroc | n | groups | errors |
|---|---|---|---|---|---|---|
| conf | 0.9065 | 0.1364 | 0.1773 | 16009 | 16 | 1741 |
| conf+D | 0.9947 | 0.144 | 0.2426 | 16009 | 16 | 1741 |
| conf+margin+negH | 0.6933 | 0.0762 | 0.7049 | 16009 | 16 | 1741 |
| conf+margin+negH+D | 0.828 | 0.08989 | 0.7039 | 16009 | 16 | 1741 |
