### T05 — Center mechanism recognition

Nearest-mechanism decisions (normalized B3 RMS, all sensors, 30 s prefix, ±1 s). frozen = own template present; loto = own template excluded. One source family; counts, not rates.

| query | condition | true_mechanism | templates | predicted | best_template | runner_up | margin | status | near_duplicate |
|---|---|---|---|---|---|---|---|---|---|
| SID213 | frozen | Withdrawal | 7 | Withdrawal | SID213 | Normal | 0.02836 | CORRECT | SID213 |
| SID213 | loto | Withdrawal | 6 | Normal | NORMAL_ZERO | Withdrawal | 7.44e-05 | INCORRECT | — |
| SID312 | frozen | Withdrawal | 7 | Withdrawal | SID312 | Normal | 0.02941 | CORRECT | SID312 |
| SID312 | loto | Withdrawal | 6 | Withdrawal | SID215 | Normal | 1.94e-05 | CORRECT | — |
| SID215 | frozen | Withdrawal | 7 | Withdrawal | SID215 | Normal | 0.002185 | CORRECT | SID215 |
| SID215 | loto | Withdrawal | 6 | Normal | NORMAL_ZERO | Timing shift | 0.009448 | INCORRECT | — |
| PRESSURE | frozen | Pressure command | 7 | Pressure command | PRESSURE | Timing shift | 0.03692 | CORRECT | PRESSURE |
| PRESSURE | loto | Pressure command | 6 | Timing shift | TIMING | Withdrawal | 0.01042 | UNSUPPORTED | — |
| TIMING | frozen | Timing shift | 7 | Timing shift | TIMING | Withdrawal | 0.01163 | CORRECT | TIMING |
| TIMING | loto | Timing shift | 6 | Withdrawal | SID215 | Normal | 0.001984 | UNSUPPORTED | — |
| ALT | frozen | Withdrawal | 7 | Withdrawal | SID213 | Normal | 0.02836 | CORRECT | SID213 |
| ALT | loto | Withdrawal | 7 | Withdrawal | SID213 | Normal | 0.02836 | CORRECT | SID213 |
| NOMINAL | frozen | Normal | 7 | Normal | NORMAL_TRANSIENT | Withdrawal | 0.2514 | CORRECT | NORMAL_TRANSIENT |
| NOMINAL | loto | Normal | 7 | Normal | NORMAL_TRANSIENT | Withdrawal | 0.2514 | CORRECT | NORMAL_TRANSIENT |

Source: `03_results/validation/center_evidence_enhancement/tables/TAB_C02.csv` · Script: `publication_q1/scripts/build_tables.py`
