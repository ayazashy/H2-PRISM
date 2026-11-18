### T06a — Center categorical location ranking

Categorical rank of candidate outlets; not a localization distance or accuracy. Unsupported = the true outlet has no independent template.

| query | condition | true_SID | candidate_SIDs | score_SID213 | score_SID312 | score_SID215 | top1 | top1_result | margin | status | relevant_sensors |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SID213 | loto | 213 | 215, 312 | — | 0.0405 | 0.02843 | 215 | unsupported | 0.01207 | UNSUPPORTED | MFS3 (branch meter SID 218), PS1 (junction SID 50) |
| SID213 | loto_replicate | 213 | 213, 215, 312 | 2.76e-05 | 0.0405 | 0.02843 | 213 | correct | 0.0284 | CORRECT | MFS3 (branch meter SID 218), PS1 (junction SID 50) |
| SID312 | loto | 312 | 215, 213 | 0.04052 | — | 0.02939 | 215 | unsupported | 0.01114 | UNSUPPORTED | MFS1 (branch meter SID 311) |
| SID312 | loto_replicate | 312 | 215, 213 | 0.04052 | — | 0.02939 | 215 | unsupported | 0.01114 | UNSUPPORTED | MFS1 (branch meter SID 311) |
| SID215 | loto | 215 | 213, 312 | 0.02796 | 0.0289 | — | 213 | unsupported | 0.000935 | UNSUPPORTED | PS4/PS8, PS9 (no branch flow meter) |
| SID215 | loto_replicate | 215 | 213, 312 | 0.02796 | 0.0289 | — | 213 | unsupported | 0.000935 | UNSUPPORTED | PS4/PS8, PS9 (no branch flow meter) |
| ALT | loto | 213 | 213, 215, 312 | 2.76e-05 | 0.04052 | 0.02846 | 213 | correct | 0.02843 | CORRECT | MFS3 (branch meter SID 218), PS1 (junction SID 50) |
| ALT | loto_replicate | 213 | 213, 215, 312 | 2.76e-05 | 0.04052 | 0.02846 | 213 | correct | 0.02843 | CORRECT | MFS3 (branch meter SID 218), PS1 (junction SID 50) |

Source: `03_results/validation/center_evidence_enhancement/tables/TAB_C03.csv` · Script: `publication_q1/scripts/build_tables.py`
