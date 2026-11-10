# Artifact Validation Report (A12), 2026-11-11

- **Tool:** `tools/research_audit/validate_artifacts.py`, read-only (tests: `tests/test_research_audit.py`).
- Faisal acceptance of A12 (F-D18) is NOT_RECORDED.

| Spec | Scope | Outcome |
| --- | --- | --- |
| `configs/artifact_validation.yaml` | plan-path artifacts (scenario map, provisional v0.1 manifest, manifest v0.2 against contract v2, legacy folds, file audit, task register, provenance register, checksum reconciliation) | **36 PASS, 1 MISSING_ARTIFACT**: `03_results/BASELINE_PREDICTIONS.parquet`, an F5 result that is POST_EXPERIMENT (expected) |
| `configs/candidate_artifact_validation.yaml` | pre-experiment candidate package (inventory, scenario manifest, family map, relationship evidence, outer/inner folds, checksum reconciliation) | **33 PASS** |

## Changes made to reach this state (2026-11-11)

- **`artifact_validation.yaml`:**
  - The superseded v0.1 provisional manifest is now checked against its own columns, not the v2 contract.
  - Manifest v0.2 (in force) was added and is checked against `manifest_schema`.
- **`00_governance/MASTER_TASK_REGISTER.csv`:**
  - Statuses moved to the plan vocabulary; the earlier `COMPLETED` / `IN_PROGRESS` / `READY_TO_START` values are kept in `status_2026_10_30`.
  - A12–A16 rows were added.
- **`05_documentation/PROVENANCE_REGISTER.csv`:** created (A10).

**Provenance reconciliation:** `PROVENANCE_RECONCILIATION.csv` is produced by `tools/research_audit/build_provenance_index.py` over the tracked documentation and configuration folders. Run-level fields (config, manifest and fold hashes, seed) are UNKNOWN for documents, by design. They are filled from `run_manifest.json` only for runner outputs, after execution.
