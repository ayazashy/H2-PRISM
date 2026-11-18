# Experiment F — corrected-attribution replication (NOT AUTHORIZED, NOT RUN)

## Confirmed facts

- **Defect.** In the H₂-SimNet release, event folders `anom_gestcent` and `anom_gestdown` carry each other's source model: 36 of 57 manifest runs, 32 of 51 eligible. The NORMAL runs and all Upstream runs are consistent (`05_documentation/FORENSIC_FINDINGS_REPORT.md`).
- **Affected metrics.** R2 Center and Downstream classification:
  - Center accuracy 0.213;
  - Center LEAK → NORMAL in 7,307 windows;
  - Downstream NORMAL → LEAK/FAULT in 665 windows;
  - together 99.5 % of R2 errors.
  The RQ1 attainable-coverage limit also shifts.
- **Still valid.** The registered R2 status (RQ1 NOT_ESTIMABLE), Upstream results, the provenance and leakage audits, and the Protocol 2.0 development finding of no incremental value from D(x).
- **Correction status.** Candidate manifest v0.3 (`06_audit_preparation/protocol2/CANDIDATE_MANIFEST_V03.csv`) passes integrity checks. Owner decision **D1 (A: keep, B: adopt v0.3, C: ask authors) is not recorded**. Protocol 2.0 is "not active and cannot run until the decisions below are recorded" (`PROTOCOL_2_0_OWNER_DECISIONS.md`).
- **Inspection status.** Every R2 outer-test window has already been inspected, and the Protocol 2.0 arms re-used them. No untouched partition exists.

## Proposed experiment (requires D1 = B and a separate written authorization)

- **Label:** `EXPLORATORY_REPLICATION`. Never confirmatory, and never a replacement for R2.
- **Frozen inputs:** manifest v0.3; `FINAL_EXPERIMENT_CONFIG.yaml` (`f788b6d8…`) with only the topology column changed; the same 27,993-window feature table (`4d1310a6…`).
- **Outputs:**
  - per-topology confusion matrix with independence-group counts;
  - attainable coverage per fold;
  - RQ1 estimability reason codes.
- **Command (after authorization only):** the frozen runner `tools/experiments/run_primary_protocol.py` with the v0.3 manifest and a new authorization file. The current runner refuses execution without one.
- **Limitations:**
  - Families are still per topology.
  - Cross-topology replicas share scenarios.
  - Results cannot test H1.
