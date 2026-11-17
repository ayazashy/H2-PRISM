# 07 Session Handoff (Phase 8)

- **Branch:** `audit/preparation-integration`. Base `d9b4c3f`; the Phase 8 commits follow (see `SESSION_CHECKPOINT.md`).
- **Verdict:** `ENGINEERING_READINESS_BLOCKED`. Blockers: the matched-coverage tie rule (Faisal) and governance items F-D15, F-D16, A-D10 (not done, not waived).
- **Code paths:**
  - runner core `src/h2prism/experiments/primary_protocol.py`;
  - CLI `tools/experiments/run_primary_protocol.py`;
  - fixture `src/h2prism/experiments/synthetic_protocol_fixture.py`;
  - tests `tests/test_primary_protocol.py`.
  - Tie handling lives in `_rank_threshold` and `outer_stage`.
- **Safe command now:** `python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out <tmp> --dry-run`
- **Next step after the decisions:** implement the chosen tie rule plus a test, re-run the full suite, re-hash the config if it changed, then follow `EXPERIMENT_EXECUTION_GUIDE.md`.
- **Never** run `--execute-*` without the project lead's authorization file.
