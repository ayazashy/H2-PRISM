# Execution ledger (v2)

| Step | Script | Status | Output |
|---|---|---|---|
| Baseline audit | audit_baseline.py | done; full suite 19 min | 01_audit/BASELINE_REPRODUCTION.csv |
| Test triage | triage_tests.py | done | 01_audit/TEST_FAILURE_TRIAGE.csv |
| D1 matrix and gate | d1_correction.py | matrix done; replicate BLOCKED (exit 3) | 01_audit/D1_* |
| D(x) X1–X5 | dx_experiments.py | done | 04_results/analysis/x* |
| R2 descriptive | r2_descriptive.py | done | 04_results/analysis/r1_* |
| D(Y) adversarial tests | tests/test_dy_adversarial.py | 44 tests pass | — |
| D(Y) synthetic stress | dy_stress.py | done | 04_results/analysis/s1_* |
| Isolability | dy_isolability.py | done | 04_results/analysis/i* |
| HY2RES port | hy2res_dy_adapter.py | done; frozen rule reproduced | 04_results/analysis/h* |
| Registers and tables | build_v2_tables.py | done | 01_audit, 02_design, 04_results/tables, 06_reports/ACCEPTANCE_CRITERIA |
| Figures | fig_v2.py | 6/6 APPROVED by QA | 05_figures |
| Reports | v2_reports.py | done | 06_reports, README |
| Deterministic re-run | run_all.py | see logs/RUN_ALL.csv | 03_execution/logs |
| Package verification | verify_v2.py | see 07_reproducibility/V2_VERIFICATION.csv | SHA256SUMS.csv |

Per-script runtimes are measured by run_all.py (`logs/RUN_ALL.csv`). Seeds: 20261118 (stress, X5), 0 (figure jitter).
