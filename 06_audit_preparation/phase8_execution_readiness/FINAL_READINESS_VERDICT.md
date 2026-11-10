# 06 Final Readiness Verdict (Phase 8)

## `ENGINEERING_READINESS_BLOCKED`

The engineering work is complete and verified. Two readiness criteria are not met, and both need human action. No code change can resolve them.

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Runner exists | ✔ | `tools/experiments/run_primary_protocol.py`, `src/h2prism/experiments/primary_protocol.py` |
| 2 | Interfaces compatible | ✔ (after 2 defect fixes) | `INTEGRATION_VALIDATION_REPORT.md` |
| 3 | Synthetic end-to-end run | ✔ | `END_TO_END_DRY_RUN_REPORT.md` |
| 4 | Real-data structural preflight | ✔ 25/25, both realizations | `REAL_DATA_PREFLIGHT_REPORT.md` |
| 5 | Config / manifest hashes | ✔ | preflight checks |
| 6 | Outer / inner fold separation | ✔ | preflight + runner assertions + tests |
| 7 | D(x) safeguards | ✔ | synthetic run + tests |
| 8 | Calibration fallback | ✔ | test case 9 |
| 9 | Estimability rules | ✔ | test case 11 |
| 10 | Reproducibility | ✔ determinism + resume byte-identical; LF rules cover new JSON/CSV/YAML | tests 14–15 |
| 11 | Critical tests | ✔ 193 passed, 0 failed | full suite |
| 12 | No execution-blocking governance issue | **✘** F-D15 (code acceptance), F-D16 (contract), A-D10 (gate records) neither done nor waived | `GOVERNANCE_CLOSURE_REGISTER.md` |
| 13 | No missing configuration values | ✔ | final-config tests |
| 14 | No material protocol/implementation mismatch | **✘ (protocol gap)**: the protocol defines no tie-break or tolerance for matched coverage. With saturated RF outputs, s_C and s_C−D can be compared at different realized coverages (synthetic: 0.45 vs 0.55), which confounds the primary RQ1 comparison. Must be fixed **before** any outer-test run | `INTEGRATION_VALIDATION_REPORT.md` |

## Exact actions that would clear the verdict

1. **Faisal (protocol):** choose and pre-register a rank-matching tie rule, for example:
   - (a) keep ties and treat comparisons whose realized coverages differ by more than a stated tolerance as NOT_ESTIMABLE; or
   - (b) break ties deterministically by a label-free secondary key (such as confidence C, then window_id).

   The chosen rule must then be implemented with a test (small change in `primary_protocol._rank_threshold`).
2. **Faisal:** code acceptance (F-D15) and contract decision (F-D16). **Ahmed:** re-record Gates 1–3 (A-D10). The project lead may instead record explicit written waivers.
3. Then the project lead writes the authorization file (`EXPERIMENT_EXECUTION_GUIDE.md` step 3).

Even after these steps, primary execution needs explicit project-lead authorization.
