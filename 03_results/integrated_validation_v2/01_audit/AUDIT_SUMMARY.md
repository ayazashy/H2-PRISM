# 01 — Audit

## Repository inventory and baseline reproduction
Branch `research/integrated-validation`, HEAD `6b98a8a` at audit. Machine-readable checks: `BASELINE_REPRODUCTION.csv`.

| check | observed | status |
|---|---|---|
| git branch | research/integrated-validation | PASS |
| git HEAD at audit | 6b98a8a | PASS |
| tracked changes outside v2 package | 0 | PASS |
| sha256 r2_predictions.parquet | 4338c8c9ececc477 | PASS |
| sha256 r2_decisions.parquet | 1f4579271b8fa5ec | PASS |
| sha256 FINAL_EXPERIMENT_CONFIG.yaml | f788b6d870183303 | PASS |
| sha256 source_model_attribution.csv | 8ae38caf0de31cbc | PASS |
| Center raw captures re-hashed on load | 12 | PASS |
| HY2RES CSV md5 | 9a3c3e3b16685968 | PASS |
| v1 publication package verifier | exit 1; rewritten QC files 2 (restored) | PASS |
| v1 advanced-validation verifier | exit 1; rewritten QC files 1 (restored) | PASS |
| full pytest suite | 13 failed, 743 passed, 42 skipped, 1254 warnings, 1 error in 1147.18s (0:19:07) | FAIL |
| known blocker: tests/test_faisal_pipeline.py import | tests/test_faisal_pipeline.py | PASS |
| tracked files rewritten by the test suite (restored) | 00_governance/ACTION_EXECUTION_STATUS.csv; 00_governance/ISSUE_CLOSURE_MATRIX.csv | FAIL |

The full suite has 14 non-passing items, none caused by this package (`TEST_FAILURE_TRIAGE.csv`):
- CHECKOUT-DEPENDENT HASH PIN (verified): 9
- CHECKOUT-DEPENDENT HASH PIN (probable): 2
- DEFECT INTRODUCED BY e944e1b (this project): 1
- ENVIRONMENT (external dataset path): 1
- KNOWN_BLOCKED (owner): 1

The test suite rewrote two tracked governance files (`00_governance/ACTION_EXECUTION_STATUS.csv`, `ISSUE_CLOSURE_MATRIX.csv`). Their committed bytes were restored, and the event is recorded.

## Data integrity
- Frozen R2 predictions, decisions, configuration and attribution match the SHA-256 recorded by the v1 H1 package.
- The 12 Center raw captures are re-hashed on every load.
- The HY2RES CSV matches the MD5 asserted by the frozen builder. Raw data stay outside Git.

## D1 decision requirements (dataset owner)
- `D1_CORRECTION_MATRIX.csv` lists, per run, the measured sensor signature, the inferred source model and the proposed topology change. 36 of 57 runs change topology (32 eligible); 0 event labels change.
- Owner decision record present: **False**. Corrected replication therefore stays BLOCKED_BY_PROVENANCE.
- What unblocks it:
  1. The owner records `06_audit_preparation/protocol2/OWNER_DECISION_D1.yaml` with decision B, the owner's name, the date, and approved manifest SHA-256 `f8ce526159b1b9239c7a2c329b0a61c3283239a4ed381295c6011da541b7e3b0`.
  2. The project lead issues an `EXPLORATORY_REPLICATION` authorization.
  3. `d1_correction.py replicate` then prints the frozen-runner command.
- This package never creates either record.

## Leakage register, provenance map and risks
- `LEAKAGE_REGISTER_V2.csv` (v1 L01–L16 plus L17–L22) is also the scientific risk register: it gives severity, impacted claims, corrective action and approver for each entry.
- `BOUND_ORIGIN_AUDIT.csv` covers bound provenance for D(Y).
- Provenance map:
  - R2 → `H2PRISM_R2_RUN` (frozen run a10530f1…);
  - Center → hash-verified MAT captures in the Center workspace;
  - HY2RES → checksum-matched Zenodo CSV plus the frozen validity mask;
  - MHC → v1 Study B archive (unchanged, not used here).
