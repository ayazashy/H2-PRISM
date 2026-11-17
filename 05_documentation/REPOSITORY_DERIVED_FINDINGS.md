# Repository-Derived Findings (A3)

- **Status:** PRE-EXPERIMENT. These are findings about the repository's earlier artifacts and the corrections now in force. **None is a research result.**

| # | Finding | Correction in force | Evidence |
| --- | --- | --- | --- |
| RF-1 | Original folds put every family on both sides of every fold (ISS-01); one byte-identical run pair crossed folds (ISS-02) | Leave-one-topology-out folds on manifest v0.2; 0 overlap | FOLD_VALIDATION_REPORT.md |
| RF-2 | Families were path/label-derived and merged across topologies (ISS-07) | 39 evidence-based families nested in topology | FAMILY_RELATIONSHIP_EVIDENCE.csv |
| RF-3 | Figures 3–6 and the dashboard were built from invented numbers and showed a positive RQ1 answer (ISS-03) | Quarantined in `03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/`; labelled illustrative | FIGURE_SPECIFICATION.md |
| RF-4 | Inherited "121 files / 2.42 M rows" was marked REFUTED although it describes the clean subtree | Re-classified REVISED (scope) | DATASET_AUDIT_AMENDMENT_2026-11.md |
| RF-5 | 8 local raw files had CRLF→LF conversion; the checksum list held a `.gitkeep` | Official archive checksums (264/264) | CHECKSUM_RECONCILIATION.csv |
| RF-6 | Annotation anomalies in the source data (G5G6; `brokenC1G5_weak`; delay label end) | Exclusions and restrictions | LABEL_CONSISTENCY.csv |
| RF-7 | Directory-derived phase is wrong for compressor files | Phase not used as an input | LABEL_AND_TIMING_CORRECTIONS.md |
| RF-8 | Legacy performance numbers are not reproducible | Not cited as results | 00_governance/LEGACY_RESULTS_STATUS.md |
| RF-9 | Interface contract v1 described columns never produced | Contract v2.0.0 with tests | configs/interface_contracts.yaml |
| RF-10 | Tie-inclusive rank matching compared methods at different coverages | Protocol amendment PA-1 (exact count) | FINAL_PROTOCOL_DECISION.md |
| RF-11 | Absolute-level features act as run fingerprints; DELAY confounded with start-up | Recorded as limitations L5 and L6; registered sensitivity | DATASET_LIMITATIONS.md |
