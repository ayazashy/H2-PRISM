# Expected outputs (all under `h2net_v1_run\`, git-ignored)

| Step | File | PASS means |
|---|---|---|
| 01 | `preflight/PREFLIGHT.json` | `overall: PASS` |
| 02 | `readiness/ENVIRONMENT_REPORT.json`, `SMOKE_REPORT.json`, `H2_INTEGRATION_REPORT.json`, `RUN_LOG.json` | `check_matlab_reports.py` prints `READY_FOR_AUTHORIZED_STEPS` |
| 03 | `targets/V2_TARGETS.json` | computed from the current decision-record hash |
| 03 | `build/H2NET_V1_BUILD_SPEC_DECIDED.json` | `status: SPECIFICATION_DECIDED` |
| 03 | `build/models/h2net_v1_{center,up,down}.slx` | the down model is absent if its let-down is deferred |
| 03 | `build/BUILD_REPORT.json` | `status: COMPLETE`; one diff entry per operation; released hashes unchanged |
| 03 | `validation/VALIDATION_RAW.json` | raw steady-state values only |
| 03 | `validation/VALIDATION_REPORT.json` | `overall: PASS` (V2, V3, V4, V5, V6, V8, D1). `NOT_EVALUABLE` means a threshold or decision is missing, never a pass. |
| 04 | `scenarios/SCENARIO_PLAN.json`, `LABELS.csv`, `PARTITIONS.json` | the plan check passes: opaque run ids, shared onset per family, no shared ancestor across partitions |
| 04 | `dataset/raw/<run_id>.csv`, `dataset/noisy/<run_id>.csv`, `dataset/RUN_MANIFEST.jsonl` | one COMPLETED line per run; failures recorded, never hidden |
| all | `logs/*.log` | MATLAB command-window logs |
| 05 | `return/H2NET_V1_RETURN_<time>.zip` (+ `.sha256`) | contains `RETURN_STATUS.json` (PASS / INCOMPLETE, with missing stages) and `SHA256SUMS.txt` |

**Not physical validation:** steps 01 and 02, and the static tests in the repository.

**Physical validation:** only `VALIDATION_REPORT.json` with `overall: PASS`, produced by real MATLAB simulation on this machine.
