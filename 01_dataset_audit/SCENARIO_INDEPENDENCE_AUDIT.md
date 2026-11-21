> **AMENDED 2026-11:** statements in this 2026-10-30 document are superseded where listed in [DATASET_AUDIT_AMENDMENT_2026-11.md](DATASET_AUDIT_AMENDMENT_2026-11.md). The original text below is kept unchanged as the historical record.

# H2-PRISM Scenario Independence Audit (Task Y2)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30 18:22:42 UTC

### Forensic Independence Assessment:
- **Total Physical Data Files**: 242
- **Reconciled Distinct Scenarios**: 61
- **Independent Scenario Families**: 13
- **Identified Cross-Scenario Edges**: 481 (recorded in `SCENARIO_RELATIONSHIP_EDGES.csv`)

### Edge Classifications:
1. `EXPORT_FORMAT_OR_TREE_DUPLICATE`: Connects identical simulation outputs exported in CSV and Parquet. **Requires joint grouping**.
2. `INTRA_FAMILY_PARAMETER_VARIANT`: Connects weak and strong variants of the same event. **Requires joint grouping**.
3. `CROSS_TOPOLOGY_IDENTICAL_EVENT_CONFIG`: Connects identical fault injection setups executed across different withdrawal points (Downstream, Center, Upstream).
