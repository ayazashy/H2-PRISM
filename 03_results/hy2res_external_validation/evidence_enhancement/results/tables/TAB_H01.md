### TAB_H01 — Dataset and recording integrity

Full source (300,768 rows). Recording increment = smallest step between distinct recorded values.

| channel | unit | valid_rows | missing_rows | distinct_values | minimum | maximum | smallest_positive_step | modal_step | on_0p1_grid_fraction | off_grid_rows | decimals_observed | source | interval_definition | causal_segments | qualification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pres_buf | bar | 300767 | 1 | 64 | 28 | 34.3 | 0.1 | 0.1 | 1 | 0 | 1 | Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…) | 5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps | 2793 | 0.1 bar recording grid; instrument resolution/accuracy undocumented |
| pres_comp | bar | 300767 | 1 | 263 | 84.5 | 110.7 | 0.1 | 0.1 | 1 | 0 | 1 | Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…) | 5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps | 2793 | 0.1 bar recording grid; instrument resolution/accuracy undocumented |
| h2_flow | NL/h | 300767 | 1 | 25465 | 0 | 376.9 | 0.0005 | 0.001 | 0.897598 | 30799 | 15 | Zenodo 15166733 v1, HY2RES_202404.csv (MD5 9a3c3e3b…) | 5 s source clock; causal segments break at OPEN/CLOSE and non-5-s steps | 2793 | not quantised at 0.1; normalised volumetric production over preceding interval |
