### T04a — HY2RES decision taxonomy and unresolved reasons

Frozen state-rule decisions on the 44,397 test rows with the reconstructed exclusive primary reason. OUT_OF_SUPPORT, INVALID_INPUT and EMPTY_CELL are distinct from ambiguity.

| part | decision | primary_reason | rows | segments | electrolyzer_only | compressor_powered | unknown_power | pct_of_test_rows | pct_of_unresolved |
|---|---|---|---|---|---|---|---|---|---|
| decision taxonomy | Ambiguous | — | 1,327 | 15 | 1,126 | 201 | 0 | 0.02989 | — |
| decision taxonomy | Electrolyzer only | — | 10,762 | 106 | 10,762 | 0 | 0 | 0.2424 | — |
| decision taxonomy | Unresolved | EMPTY_CELL (no state with >=2 development segments) | 306 | 3 | 306 | 0 | 0 | 0.006892 | 0.009471 |
| decision taxonomy | Unresolved | INVALID_INPUT (nonfinite origin measurement) | 413 | 413 | 0 | 0 | 413 | 0.009302 | 0.01278 |
| decision taxonomy | Unresolved | OUT_OF_SUPPORT (pres_comp) | 31,589 | 299 | 30,973 | 616 | 0 | 0.7115 | 0.9777 |

Source: `hy2res .../analysis/unresolved_taxonomy.csv` · Script: `publication_q1/scripts/build_tables.py`
