# Integrated tables T01–T10

### T01 — Study source and data qualification

Evidence sources, identity checks and independent units. Studies are never pooled.

| study | system | data | source_identity | independent_units | verification | qualification |
|---|---|---|---|---|---|---|
| Center | controlled Simscape network simulation (air-like gas, R = 0.287 kJ/(kg·K)) | 12 accepted captures; 13 sensors (PS1–PS10 MPa, MFS1–MFS3 kg/s); 0.2 s step | frozen baseline h2prism-center-baseline-v1 (6fee8a0); per-capture raw SHA-256 | one source family; 0 verified independent generating families | baseline_freeze --verify: 12 captures, 410 files matched | VERIFIED (integrity); controlled simulation only |
| R2 / H2-SimNet | simulated pipeline topologies (Center, Downstream, Upstream) | 27,993 windows of 60 s, 128 features; 4 classes | run key a10530f1fcf2; predictions SHA-256 4338c8c9ecec… | 51 runs, 39 families, 17 scenario ancestors | 161 H1 reproduction checks matched | REGISTERED (inspected); 36/57 runs attribution disputed (D1 pending) |
| MHC (Study B) | dual-stage metal-hydride hydrogen compressor (MHC v1.2, CC BY 4.0) | 29 workbooks; 8 eligible; P-2 (barg), MFC-3 (ln/min) | ZIP SHA-256 91755fb1e555…, MD5 64cbe2a68c0a… | 3 held-out runs of one apparatus (rows serially dependent) | frozen replay bit-identical (24/24 metrics) | VALIDATED WITHIN SCOPE (reference prediction) |
| HY2RES (Study C) | residential PV–electrolyzer–storage–fuel-cell hydrogen system (Zenodo 15166733 v1) | 300,768 rows at 5 s; targets pres_buf, pres_comp (bar), h2_flow (NL/h) | 38,621,947 bytes; MD5 9a3c3e3b1668…; SHA-256 c9adf30dc1ac… | one system, 414 test segments (serially dependent) | 60/60 archived metrics reconciled; decision counts reproduced | VERIFIED WITHIN SCOPE (reference, evidence validity) |

Source: `center execution_manifest.json`; `study_b replay_manifest.json, TAB_B01.csv`; `hy2res analysis_manifest.json, recording_grid.csv`; `h1_validation/analysis` · Script: `publication_q1/scripts/build_tables.py`

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

### T03 — Errors and recording resolution

Errors divided by the observed recording increment (dimensionless). The increment is recorded quantization, not instrument resolution or accuracy (undocumented in both sources).

| study | channel | unit | recording_increment | on_grid_fraction | persistence_exact_share | persistence_MAE_incr | ridge_MAE_incr | persistence_RMSE_incr | ridge_RMSE_incr | delta_MAE_incr | delta_RMSE_incr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MHC | P-2 | barg | 0.2 | 1 | 0.7058 | 0.8075 | 0.8797 | 1.942 | 1.93 | 0.07217 | -0.01177 |
| MHC | MFC-3 | ln/min | 0.01 | 1 | 0.9071 | 3.221 | 4.29 | 29.67 | 29.64 | 1.068 | -0.02791 |
| HY2RES | pres_buf | bar | 0.1 | 1 | 0.9604 | 0.03964 | 0.055 | 0.1991 | 0.1714 | 0.01537 | -0.02771 |
| HY2RES | pres_comp | bar | 0.1 | 1 | 0.744 | 0.256 | 0.2514 | 0.506 | 0.407 | -0.004562 | -0.09901 |

Source: `study_b/.../analysis/resolution.csv`; `hy2res .../analysis/quantization_comparison.csv, recording_grid.csv` · Script: `publication_q1/scripts/build_tables.py`

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

### T04b — HY2RES outcomes per power-defined operating state

Operating-state labels are power-defined, not fault labels. majority_baseline_agree = rows a constant 'electrolyzer only' rule would match.

| primary_reason | rows | segments | specific | ambiguous | unresolved | unresolved_out_of_support | unresolved_invalid | unresolved_empty_cell | majority_baseline_agree |
|---|---|---|---|---|---|---|---|---|---|
| electrolyzer_active | 43,167 | 405 | 10,762 | 1,126 | 31,279 | 30,973 | 0 | 306 | 43,167 |
| multiple_active | 817 | 12 | 0 | 201 | 616 | 616 | 0 | 0 | 0 |
| unknown | 413 | 413 | 0 | 0 | 413 | 0 | 413 | 0 | 0 |

Source: `hy2res .../analysis/state_outcomes.csv` · Script: `publication_q1/scripts/build_tables.py`

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

### T06b — Center sensor-dependent outlet contrasts

Template contrast between outlet pairs per sensor group (B3, dimensionless) and largest native contrasts (MPa, kg/s), ±1 s.

| a | b | group | b3_rms | flow_share | max_abs_pressure_MPa | max_abs_flow_kg_s |
|---|---|---|---|---|---|---|
| SID213 | SID312 | all | 0.0405 | 1 | 0.001148 | 0.6913 |
| SID213 | SID312 | pressure | 7.99e-05 | 0 | 0.001148 | — |
| SID213 | SID312 | flow | 0.08431 | 1 | — | 0.6913 |
| SID213 | SID312 | omit_MFS3 | 0.03009 | 1 | 0.001148 | 0.6467 |
| SID213 | SID215 | all | 0.02843 | 0.9999 | 0.005474 | 0.6913 |
| SID213 | SID215 | pressure | 0.000377 | 0 | 0.005474 | — |
| SID213 | SID215 | flow | 0.05918 | 1 | — | 0.6913 |
| SID213 | SID215 | omit_MFS3 | 0.002127 | 0.9738 | 0.005474 | 0.000301 |
| SID213 | ALT | all | 2.76e-05 | 1 | 2.45e-06 | 0.000684 |
| SID213 | ALT | pressure | 1.41e-07 | 0 | 2.45e-06 | — |
| SID213 | ALT | flow | 5.75e-05 | 1 | — | 0.000684 |
| SID213 | ALT | omit_MFS3 | 7.95e-07 | 0.9739 | 2.45e-06 | 1.49e-06 |
| SID312 | SID215 | all | 0.02939 | 0.9999 | 0.004797 | 0.6468 |
| SID312 | SID215 | pressure | 0.000347 | 0 | 0.004797 | — |
| SID312 | SID215 | flow | 0.06117 | 1 | — | 0.6468 |
| SID312 | SID215 | omit_MFS3 | 0.03059 | 0.9999 | 0.004797 | 0.6468 |
| SID312 | ALT | all | 0.04054 | 1 | 0.001173 | 0.6919 |
| SID312 | ALT | pressure | 8.35e-05 | 0 | 0.001173 | — |
| SID312 | ALT | flow | 0.0844 | 1 | — | 0.6919 |
| SID312 | ALT | omit_MFS3 | 0.0306 | 1 | 0.001173 | 0.6468 |
| SID215 | ALT | all | 0.02799 | 0.9999 | 0.005523 | 0.6919 |
| SID215 | ALT | pressure | 0.000388 | 0 | 0.005523 | — |
| SID215 | ALT | flow | 0.05826 | 1 | — | 0.6919 |
| SID215 | ALT | omit_MFS3 | 0.002146 | 0.9727 | 0.005523 | 0.000312 |

Source: `03_results/validation/center_evidence_enhancement/analysis/pair_contrasts.csv` · Script: `publication_q1/scripts/build_tables.py`

### T07a — Formal D(Y) decisions by universe, sensor group and clock bound

CONDITIONAL_HYPOTHETICAL_BOUNDS — not calibrated uncertainty. 42 cells per row (6 queries × 7 bound scenarios); rows are repeated views of the same captures.

| universe | group | clock_bound_s | cells | specific | specific_correct | specific_wrong | ambiguous | unresolved |
|---|---|---|---|---|---|---|---|---|
| full | all | 0 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | all | 1 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | flow | 0 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | flow | 1 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | omit_MFS3 | 0 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | omit_MFS3 | 1 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | pressure | 0 | 42 | 0 | 0 | 0 | 0 | 42 |
| full | pressure | 1 | 42 | 0 | 0 | 0 | 0 | 42 |
| restricted | all | 0 | 42 | 10 | 8 | 2 | 4 | 28 |
| restricted | all | 1 | 42 | 10 | 8 | 2 | 4 | 28 |
| restricted | flow | 0 | 42 | 11 | 8 | 3 | 8 | 23 |
| restricted | flow | 1 | 42 | 12 | 8 | 4 | 7 | 23 |
| restricted | omit_MFS3 | 0 | 42 | 4 | 4 | 0 | 12 | 26 |
| restricted | omit_MFS3 | 1 | 42 | 4 | 4 | 0 | 12 | 26 |
| restricted | pressure | 0 | 42 | 4 | 4 | 0 | 14 | 24 |
| restricted | pressure | 1 | 42 | 4 | 4 | 0 | 14 | 24 |

Source: `03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json` · Script: `publication_q1/scripts/build_tables.py`

### T07b — Formal D(Y) decision reasons (all sensors, ±1 s)

Engine reason codes per universe; 42 cells per universe.

| universe | decision | reason | cells_all_sensors_1s |
|---|---|---|---|
| full | UNRESOLVED | INDETERMINATE_HYPOTHESES | 42 |
| restricted | AMBIGUOUS | MULTIPLE_FEASIBLE | 4 |
| restricted | SPECIFIC | UNIQUE_FEASIBLE | 10 |
| restricted | UNRESOLVED | MODEL_MISMATCH | 28 |

Source: `center TAB_C06.csv` · Script: `publication_q1/scripts/build_tables.py`

### T08a — RQ1 / H1 — registered result

Registered primary-contrast rows of R2 (both policy variants). Verdict: NOT_ESTIMABLE; H1 not established.

| evidence | variant | target | mode | status | folds_estimable | n_folds |
|---|---|---|---|---|---|---|
| registered R2 (s_C vs s_C−D) | primary | 0.6 | rank_matched | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 2 | 3 |
| registered R2 (s_C vs s_C−D) | primary | 0.6 | threshold_transfer | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | primary | 0.8 | rank_matched | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | primary | 0.8 | threshold_transfer | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | primary | 0.9 | rank_matched | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | primary | 0.9 | threshold_transfer | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | warning_only | 0.6 | rank_matched | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 2 | 3 |
| registered R2 (s_C vs s_C−D) | warning_only | 0.6 | threshold_transfer | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | warning_only | 0.8 | rank_matched | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | warning_only | 0.8 | threshold_transfer | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | warning_only | 0.9 | rank_matched | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |
| registered R2 (s_C vs s_C−D) | warning_only | 0.9 | threshold_transfer | NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL | 0 | 3 |

Source: `03_results/primary_protocol/PRIMARY/rq1.csv` · Script: `publication_q1/scripts/build_tables.py`

### T08b — RQ1 / H1 — exploratory shared-coverage contrast

EXPLORATORY_POST_HOC on inspected windows; Δ = R_sel(s_C) − R_sel(s_C−D); 95 % family and ancestor bootstrap intervals; errors among windows from undisputed runs. Not a test of H1.

| coverage | accepted_each | risk_s_C | risk_comparator | delta_R | family_ci_low | family_ci_high | ancestor_ci_low | ancestor_ci_high | ancestors_discordant_errors | errors_undisputed_runs_s_C | errors_undisputed_runs_comparator |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.05 | 1,401 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 0.1 | 2,802 | 0 | 0.1003 | -0.1003 | -0.365 | 0 | -0.3926 | 0 | 1 | 0 | 0 |
| 0.15 | 4,200 | 0.03548 | 0.1693 | -0.1338 | -0.3166 | 0 | -0.312 | 0 | 2 | 0 | 0 |
| 0.2 | 5,601 | 0.1012 | 0.1896 | -0.08838 | -0.2134 | 0.001363 | -0.1819 | 0.001153 | 3 | 0 | 0 |
| 0.25 | 6,999 | 0.1456 | 0.1517 | -0.006144 | -0.04941 | 0.03373 | -0.04422 | 0.02301 | 3 | 0 | 0 |

Source: `h1_validation/tables/H1-T04.csv` · Script: `publication_q1/scripts/build_tables.py`

### T09a — RQ2 — development ablation of D(x)

Protocol 2.0 development arms (exploratory). Where estimable, s_C = s_C−D = confidence: no incremental value of D(x).

| setting | evidence | s_C_estimable_dev_topologies | s_C_group_balanced_risk_mean | s_C_minus_D_group_balanced_risk_mean | confidence_group_balanced_risk_mean | min_auroc_confidence_over_dev_topologies | min_auroc_D_only_over_dev_topologies | auroc_s_C_minus_auroc_s_C_minus_D_mean | meta_model_undefined_folds |
|---|---|---|---|---|---|---|---|---|---|
| A_P11_DEV | development ablation (exploratory) | 1 | 0 | 0 | 0 | 0.07296 | 0.494 | -0.006561 | 0 |
| B_TOPOLOGY | development ablation (exploratory) | 0 | — | — | — | 0.5135 | 0.5 | 0.01163 | 1 |
| C_COMMON_SENSORS | development ablation (exploratory) | 2 | 0.04545 | 0.04545 | 0.04545 | 0.005 | 0.289 | -0.0153 | 0 |
| F_EVIDENCE_MARGIN | development ablation (exploratory) | 0 | — | — | — | 0.07296 | 0.4903 | — | 2 |
| G1_DATA_CORRECTIONS | development ablation (exploratory) | 2 | 0.09091 | 0.09091 | 0.09091 | 0.6148 | 0.341 | 0.02979 | 0 |
| G2_FULL_CANDIDATE | development ablation (exploratory) | 2 | 0.09091 | 0.09091 | 0.09545 | 0.6148 | 0.2692 | 0.1215 | 2 |

Source: `03_results/ablation/ARM_SUMMARY.csv` · Script: `publication_q1/scripts/build_tables.py`

### T09b — RQ3 — registered three-outcome shares (s_C, target 0.60)

Shares of each class's windows in the two folds where 0.60 is attainable; specific_correct and ambiguity_inclusion are rates among SPECIFIC and ambiguity sets ('—' = none).

| class | n | n_families | specific | ambiguity_set | unresolved | specific_correct | ambiguity_inclusion | reporting |
|---|---|---|---|---|---|---|---|---|
| COMPRESSOR_DELAY | 62 | 2 | 0 | 0.5 | 0.5 | — | 1 | descriptive_only |
| COMPRESSOR_FAULT | 2,656 | 2 | 0 | 0 | 1 | — | — | descriptive_only |
| LEAK | 14,614 | 20 | 0.7322 | 0 | 0.2678 | 1 | — | restricted |
| NORMAL | 1,330 | 2 | 0.3737 | 0 | 0.6263 | 1 | — | descriptive_only |

Source: `03_results/primary_protocol/PRIMARY/rq2.csv` · Script: `publication_q1/scripts/build_tables.py`

### T10 — Claim-to-evidence matrix

Every claim of the integrated package with its evidence, number and qualification, quoted from the accepted study claim tables and the H1 qualification table.

| study | claim | evidence | numerical_result | qualification | limitation |
|---|---|---|---|---|---|
| Center | The 12 accepted captures and 410 frozen files are unchanged | baseline_freeze --verify (before and after) | 12 captures; 410 files matched | VERIFIED | integrity, not validity |
| Center | Center model is air-like | source SLX gas block R | R = 0.287 kJ/(kg·K), Z = 0.998386 | VERIFIED | no hydrogen material claim possible |
| Center | Mechanism recognition does not survive self-template removal | TAB C-02 | 3/5 supported queries agree; 2 unsupported; frozen library 7/7 with self or near-duplicate templates | DESCRIPTIVE (one family) | 7 queries, 1 family |
| Center | Withdrawal signatures are outlet-specific | TAB C-04, channel_signal.csv | SID 213→MFS3 0.691 kg/s; SID 312→MFS1 0.647 kg/s; SID 215 flow ≤3.9e-4 kg/s | DESCRIPTIVE | sensor configuration of one model |
| Center | Categorical location ranking with an independent same-outlet template | TAB C-03 | SID 213 ranked 1st for 2/2 supported queries (all four sensor groups); SID 312 and SID 215 unsupported | DESCRIPTIVE (2 queries, 1 outlet) | near-duplicate template |
| Center | Flow-dependent B3 localization; pressure contrasts exist in native units | TAB C-04 | B3 flow share ≥ 0.97 for every outlet pair; pressure contrasts 1.1–5.5 kPa; withholding MFS3 cuts the SID 213 margin 0.028→0.0021 while the correct/runner-up ratio rises 1,030×→2,676×; pressure alone 569× | DESCRIPTIVE | normalization by absolute level |
| Center | Conditional correct SPECIFIC window | TAB C-05/C-06 | pressure eps ∈ [2.5e-6, 5.1e-4) MPa; flow eps ∈ [6.8e-4, 0.69) kg/s | CONDITIONAL_HYPOTHETICAL_BOUNDS | hypothetical bounds; replicate template |
| Center | Restricted universe can be confidently wrong | TAB C-06 | 2 wrong vs 8 correct SPECIFIC cells (all sensors, 7 scenarios × 6 queries) | CONDITIONAL_HYPOTHETICAL_BOUNDS | true mechanism unrepresented |
| Center | Full declared universe never decides | TAB C-06 | 42/42 UNRESOLVED (INDETERMINATE_HYPOTHESES) | CONDITIONAL_HYPOTHETICAL_BOUNDS | unmodelled FAULT/DELAY/SID 222 |
| Center | Frozen 12/12 UNRESOLVED unchanged | TAB_13, research_evidence.json | 12/12 UNRESOLVED, INVALID_UNCERTAINTY; all hypotheses adapter=None | VERIFIED | — |
| Center | RQ1 (registered) | 03_results/primary_protocol/PRIMARY/rq1.csv | NOT_ESTIMABLE at 0.60/0.80/0.90 | REGISTERED RESULT | max Center coverage 0.258 |
| Center | H1 | PRIMARY + exploratory shared coverage | all intervals vs s_C−D include 0 | NOT ESTABLISHED | inspected partitions |
| Center | RQ2 (development) | PROTOCOL_2_ABLATION_REPORT.md | s_C = s_C−D = confidence at matched development coverage | NEGATIVE (exploratory) | 13 groups |
| Center | Leak localization / fault diagnosis in hydrogen pipelines | — | — | NOT ESTABLISHED | no field truth |
| MHC | Causal one-step prediction | frozen benchmark + bit-identical replay | 15,885 rows/channel, 3 runs | VALIDATED WITHIN SCOPE | prohibited: Generality beyond this apparatus |
| MHC | Reference error behaviour | replayed predictions | Ridge RMSE gain from rare large steps; MAE loss on unchanged rows | DESCRIPTIVELY SUPPORTED | prohibited: Practical superiority of Ridge |
| MHC | Measurement resolution | recorded values only | P-2 0.2 barg grid; MFC-3 0.01 ln/min grid | NUMERICALLY VERIFIED (observed grid) | prohibited: Certified accuracy statements |
| MHC | Controller role of MFC-3 | workbook notes + coupled P-2/MFC-3 data | P-2 ≤ outlet set pressure + 1 barg whenever MFC-3 = 0 (3/3 runs) | DESCRIPTIVELY SUPPORTED | prohibited: Modelling the control law (setpoint not recorded) |
| MHC | Operating-condition dependence | 3 runs, confounded settings | Run 29 carries 82 % of P-2 ΔSSE | DESCRIPTIVELY SUPPORTED | prohibited: Attribution to material, pressure or cycle time |
| MHC | Competing event hypotheses | operator notes (valve timing, safety valve, back-pressure error) | notes only | NOT ESTABLISHED | prohibited: Event labels |
| MHC | Fault classification / localization | none | — | BLOCKED BY EVIDENCE | prohibited: Any accuracy or localization metric |
| MHC | Formal D(Y) | none | — | BLOCKED BY EVIDENCE | prohibited: Exclusion or certified diagnosis |
| MHC | Independent equipment transfer | one apparatus | — | NOT ESTABLISHED | prohibited: Industrial generalization |
| HY2RES | Source identity | MD5/size of restored source | 38,621,947 bytes, MD5 9a3c3e3b… | VERIFIED WITHIN SCOPE | does not establish: Calibration or synchronisation |
| HY2RES | Pressure recording grid | TAB_H01 | both pressures 100 % on 0.1 bar grid | NUMERICALLY VERIFIED | does not establish: Instrument accuracy |
| HY2RES | Ridge vs persistence | TAB_H02/H03 | buffer ΔMAE +0.015 incr., ΔRMSE −0.028 incr.; tank −0.005/−0.099 | DESCRIPTIVELY SUPPORTED | does not establish: Practical superiority; new held-out claim |
| HY2RES | Tank-pressure drift | TAB_H04, FIG_H04 | dev max 106.6 bar; 71.8 % of test source rows above | DESCRIPTIVELY SUPPORTED | does not establish: Physical cause |
| HY2RES | Unresolved mechanism | TAB_H06 | 31,589 / 32,308 unresolved = tank out of support | NUMERICALLY VERIFIED (reconciled) | does not establish: That abstention is diagnostically correct |
| HY2RES | Minority state | TAB_H07 | 0 of 817 compressor rows specific | DESCRIPTIVELY SUPPORTED | does not establish: Compressor fault detection |
| HY2RES | Positive-flow distinction | TAB_H08 | flow rank probability 0.945 → 0.554 | DESCRIPTIVELY SUPPORTED | does not establish: Classification accuracy |
| HY2RES | Formal D(Y) | source scope | no qualified bounds, fault library, labels or locations | NOT ESTABLISHED | does not establish: Any exclusion or certified diagnosis |
| HY2RES | Fault / leak / localization / transfer | source scope | no truth | BLOCKED BY EVIDENCE | does not establish: Any accuracy, localization or generalisation claim |
| R2 / H1 | Registered RQ1 / H1 contrast (s_C vs s_C−D) | h1_validation | R2 rq1.csv: 12/12 rows; Center coverage 0.258 < 0.60 | NOT_ESTIMABLE | see H1_LIMITATIONS.md |
| R2 / H1 | D(x) neighbourhood statistic and s_C meta-model | h1_validation | 02_methodology/DISTINGUISHABILITY_MATHEMATICAL_SPEC.md | IMPLEMENTED, TESTED | see H1_LIMITATIONS.md |
| R2 / H1 | Reproduction of R2 selections and registered intervals | h1_validation | 161/161 checks (h1_verification.csv) | NUMERICALLY VERIFIED | see H1_LIMITATIONS.md |
| R2 / H1 | D(x) incremental value at development level | h1_validation | G1: s_C = s_C−D = confidence = 0.091 | NOT SUPPORTED (exploratory) | see H1_LIMITATIONS.md |
| R2 / H1 | s_C lower risk than s_C−D at shared coverage ≤ 0.25 | h1_validation | Δ ≤ 0 at 5/5 points; all intervals include 0; 0 errors outside disputed runs for both | EXPLORATORY EVIDENCE ONLY — INCONCLUSIVE | see H1_LIMITATIONS.md |
| R2 / H1 | Evidence guard withholds errors accepted by confidence abstention | h1_validation | 78.3 % of classifier errors blocked; ancestor CI < 0 at 3/5 points | EXPLORATORY, CONFOUNDED BY D1 DEFECT | see H1_LIMITATIONS.md |
| R2 / H1 | Three-outcome policy produces SPECIFIC / AMBIGUITY / UNRESOLVED | h1_validation | 0 wrong SPECIFIC of 11,198; 31/31 ambiguity sets include truth | DESCRIPTIVELY DEMONSTRATED (R2 folds 2–3) | see H1_LIMITATIONS.md |
| R2 / H1 | Formal D(Y) three outcomes on Center | h1_validation | restricted 48 correct / 11 wrong SPECIFIC; full universe 336/336 UNRESOLVED | CONDITIONALLY DEMONSTRATED (hypothetical bounds) | see H1_LIMITATIONS.md |
| R2 / H1 | Incomplete hypothesis library causes false specificity | h1_validation | 11/11 wrong SPECIFIC with unsupported truth; 0/48 with supported truth | CONDITIONALLY DEMONSTRATED | see H1_LIMITATIONS.md |
| R2 / H1 | Corrected-attribution replication | h1_validation | EXPERIMENT_F_PROPOSAL.md | BLOCKED (D1 not recorded) | see H1_LIMITATIONS.md |
| R2 / H1 | H1 independent confirmation | h1_validation | no untouched partition; 17 scenario ancestors | BLOCKED BY EVIDENCE | see H1_LIMITATIONS.md |
| R2 / H1 | Industrial / hydrogen-field transfer | h1_validation | simulated topologies; air-like Center model | NOT ESTABLISHED | see H1_LIMITATIONS.md |

Source: `center TAB_C08`; `study_b TAB_B08`; `hy2res TAB_H09`; `h1_validation/tables/H1-T07.csv` · Script: `publication_q1/scripts/build_tables.py`
