# 05 Experiment Execution Guide (do NOT run until authorized)

Run from the repository root with the project venv. All outputs carry an `artifact_class`.

1. **Re-verify (safe, any time):**
   ```
   python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out <tmp>/preflight --dry-run
   ```
   Expect `PREFLIGHT_PASSED` with 25/25 checks.
2. **Resolve blockers** (`FINAL_READINESS_VERDICT.md`):
   - matched-coverage tie handling (Faisal);
   - F-D15, F-D16, A-D10 completed or waived in writing by the project lead.

   If the protocol changes, regenerate `FINAL_EXPERIMENT_CONFIG.yaml` and record its new SHA-256.
3. **Write the authorization file** (by the project lead; never by the runner), for example `06_audit_preparation/EXECUTION_AUTHORIZATION_PRIMARY.yaml`:
   ```yaml
   authorized: true
   scope: PRIMARY_EXPERIMENT          # or ROBUSTNESS_EXPERIMENT for the clean realization
   config_sha256: <sha256 of FINAL_EXPERIMENT_CONFIG.yaml>
   authorized_by: <name>
   date: <YYYY-MM-DD>
   ```
4. **Execute the primary run** (single outer-test evaluation; resumable; same command resumes after interruption):
   ```
   python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out 03_results/primary_protocol/<run_id> --execute-primary --authorization 06_audit_preparation/EXECUTION_AUTHORIZATION_PRIMARY.yaml
   ```
   The runner refuses if the authorization scope or config hash does not match. It writes `run_manifest.json` (git commit, config / feature hashes, seed), per-fold outputs and `coverage_risk.csv`, `estimability.csv`, `rq1.csv`, `rq2.csv`.
5. **Robustness run:** the same command with `--execute-robustness` and a ROBUSTNESS_EXPERIMENT authorization.
6. **Do not** rerun with altered settings after seeing outer-test outputs. Report every outcome (including `NOT_ESTIMABLE`) under `AHMED_RESOLUTION.md` C6.

**Runtime expectation:** the real development stage fits the plan's RF grid (8 settings × 2 inner splits plus a refit) on about 19,000 development windows per fold, and computes k-NN supports for about 28,000 windows. Expect tens of minutes per realization on this machine. This is not measured.
