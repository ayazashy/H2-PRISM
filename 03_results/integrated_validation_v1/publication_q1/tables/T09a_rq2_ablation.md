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
