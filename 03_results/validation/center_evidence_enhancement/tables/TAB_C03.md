### TAB_C03 — Categorical location ranking

loto = frozen withdrawal templates minus the query's own; loto_replicate adds the alternate-profile SID 213 capture as a second SID 213 template. Unsupported = true outlet has no independent template.

| query | condition | true_SID | candidate_SIDs | score_SID213 | score_SID312 | score_SID215 | rank_SID213 | rank_SID312 | rank_SID215 | top1 | top1_result | top2_includes_true | margin | status | relevant_sensors | independence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SID213 | loto | 213 | 215, 312 | — | 0.0404991 | 0.0284326 | — | 2 | 1 | 215 | unsupported | unsupported | 0.0120665 | UNSUPPORTED | MFS3 (branch meter SID 218), PS1 (junction SID 50) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| SID213 | loto_replicate | 213 | 213, 215, 312 | 2.7612e-05 | 0.0404991 | 0.0284326 | 1 | 3 | 2 | 213 | correct | yes | 0.028405 | CORRECT | MFS3 (branch meter SID 218), PS1 (junction SID 50) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| SID312 | loto | 312 | 215, 213 | 0.0405235 | — | 0.029388 | 2 | — | 1 | 215 | unsupported | unsupported | 0.0111355 | UNSUPPORTED | MFS1 (branch meter SID 311) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| SID312 | loto_replicate | 312 | 215, 213 | 0.0405235 | — | 0.029388 | 2 | — | 1 | 215 | unsupported | unsupported | 0.0111355 | UNSUPPORTED | MFS1 (branch meter SID 311) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| SID215 | loto | 215 | 213, 312 | 0.0279627 | 0.0288979 | — | 1 | 2 | — | 213 | unsupported | unsupported | 0.000935145 | UNSUPPORTED | PS4/PS8, PS9 (no branch flow meter) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| SID215 | loto_replicate | 215 | 213, 312 | 0.0279627 | 0.0288979 | — | 1 | 2 | — | 213 | unsupported | unsupported | 0.000935145 | UNSUPPORTED | PS4/PS8, PS9 (no branch flow meter) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| ALT | loto | 213 | 213, 215, 312 | 2.7612e-05 | 0.0405185 | 0.0284601 | 1 | 3 | 2 | 213 | correct | yes | 0.0284325 | CORRECT | MFS3 (branch meter SID 218), PS1 (junction SID 50) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
| ALT | loto_replicate | 213 | 213, 215, 312 | 2.7612e-05 | 0.0405185 | 0.0284601 | 1 | 3 | 2 | 213 | correct | yes | 0.0284325 | CORRECT | MFS3 (branch meter SID 218), PS1 (junction SID 50) | one source family; ALT↔SID 213 differ only by a +0.005 MPa reservoir overlay |
