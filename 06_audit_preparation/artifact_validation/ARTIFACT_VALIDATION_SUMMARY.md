# Artifact validation summary (generated, read-only)

Spec: `configs/artifact_validation.yaml`

| Outcome | Count |
| --- | ---: |
| MISSING_ARTIFACT | 2 |
| PASS | 28 |
| UNSUPPORTED_STATUS | 1 |

Non-PASS rows:

- **UNSUPPORTED_STATUS** `00_governance/MASTER_TASK_REGISTER.csv` [status_vocabulary[status]] unsupported: ['COMPLETED', 'IN_PROGRESS', 'READY_TO_START']
- **MISSING_ARTIFACT** `03_results/BASELINE_PREDICTIONS.parquet` [exists] file not found
- **MISSING_ARTIFACT** `05_documentation/PROVENANCE_REGISTER.csv` [exists] file not found
