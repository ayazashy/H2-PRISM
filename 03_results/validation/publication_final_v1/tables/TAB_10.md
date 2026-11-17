# TAB_10 — Focal competing-mechanism routing

The focal controlled queries include self-templates; only one withdrawal used a held template.

| query | self_template | truth | mechanism | forced_location | eligible | location_ranked | reason | mechanism_margin | location_margin |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SID213 | True | CONTROLLED_WITHDRAWAL | CONTROLLED_WITHDRAWAL | SID213 | True | SID213 | withdrawal_leads_both | 0.0283582 | 0.0284326 |
| SID312 | True | CONTROLLED_WITHDRAWAL | CONTROLLED_WITHDRAWAL | SID312 | True | SID312 | withdrawal_leads_both | 0.0294074 | 0.029388 |
| SID215 | True | CONTROLLED_WITHDRAWAL | CONTROLLED_WITHDRAWAL | SID215 | True | SID215 | withdrawal_leads_both | 0.00218503 | 0.0279627 |
| PRESSURE | True | PRESSURE_COMMAND_CHANGE | PRESSURE_COMMAND_CHANGE | SID215 | False | — | operational_leader | 0.0369241 | — |
| ALT | False | CONTROLLED_WITHDRAWAL | CONTROLLED_WITHDRAWAL | SID213 | True | SID213 | withdrawal_leads_both | 0.0283582 | 0.0284325 |
| TIMING | True | COMMAND_ISSUANCE_SHIFT | COMMAND_ISSUANCE_SHIFT | SID215 | False | — | timing_sensitive_or_tied | 0.0116331 | — |
| NOMINAL | False | NORMAL_OPERATION | NORMAL_OPERATION | SID213 | False | — | operational_leader | 0.251431 | — |
| QUIET | False | NORMAL_OPERATION | NORMAL_OPERATION | SID215 | False | — | operational_leader | 0.00216293 | — |
