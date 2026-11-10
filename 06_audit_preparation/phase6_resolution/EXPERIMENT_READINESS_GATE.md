# Experiment Readiness Gate (Phase 6)

| Question | Answer | Evidence |
| --- | --- | --- |
| Is the candidate dataset ready? | **Technically yes** (v0.2: deterministic, hash-pinned, consistent with folds and config). **Not approved** | `CANDIDATE_DATASET_MANIFEST_V02.md`, tests |
| Is the candidate experiment configuration complete? | **Yes, as a candidate**: no open value; every block PENDING_HUMAN_SIGNOFF | `CANDIDATE_EVALUATION_CONFIG.yaml`, `test_candidate_config.py` |
| Are all technical preparation components implemented? | **Yes**: windows/features builder, grouped runner, calibration with fallback, D(x) with thin-class flag, comparators, combined score, policy, metrics, bootstrap, ablation/sensitivity arms, validators, reporting | `IMPLEMENTATION_AND_TEST_REPORT.md`; 171 passed / 2 skipped |
| What still requires human sign-off? | 43 decisions (22 P0) | `HUMAN_SIGNOFF_REQUIREMENTS.md` |
| Can primary experiments begin? | **No** | no P0 sign-off is recorded; config not frozen; gates not re-recorded; no user authorisation |
| Exact next action | Yazan signs Y-D01, Y-D05b/d, Y-D06a, Y-D07 and Y-D08 on `YAZAN_SIGNOFF.md` (v0.2 hash `36bcbaf9…`) | — |

**Gate rule:** once all P0 sign-offs exist, copy the candidate config to `configs/frozen_evaluation_config.yaml` (record its hash and a change-control entry), re-record Gates 1–3 (A-D10), then request user authorisation:
1. first for the development-only stage;
2. then for the single outer-test evaluation.
