# Grouped Evaluation Protocol (F4)

- **Status:** SPECIFIED and IMPLEMENTED. Selected under the project lead's Phase-7 protocol delegation. Faisal attestation NOT_RECORDED.
- **Frozen config:** `06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml` (`f788b6d8…`; pointer: `configs/frozen_evaluation_config.yaml`).

| Element | Decision | Evidence |
| --- | --- | --- |
| Independence unit | Scenario_Family_ID (39 primary families, nested in topology) | manifest v0.2 |
| Outer design | leave-one-topology-out, 3 folds (test: Center / Downstream / Upstream; 17 test runs and 13 families each) | `pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv` (`3b21d823…`) |
| Why LOTO | the only design with every class in every training and test fold and no cross-split family dependence; generalisation target = an unseen withdrawal topology of the simulated network | `EVALUATION_FEASIBILITY_REPORT.md` (F-D02) |
| Inner design | leave-one-topology-out within the 2 training topologies (2 inner splits), used for RF selection, calibration selection, combined-score cross-fitting and the development D(x) reference | `CANDIDATE_INNER_FOLDS.csv` scheme `LOTO_within_train` (`ebff65da…`); the runner derives identical splits from topology and the preflight checks the match |
| Class presence | each test fold: NORMAL 1, LEAK 13, FAULT 2, DELAY 1 runs; each training fold: twice that | fold summary |
| Leakage assertions | family, topology and run disjoint between development and test (`assert_group_disjoint`, preflight `fold_family_isolation`, `fold_topology_isolation`) | preflight 27/27 |
| Pooling | primary results pooled over the 3 outer folds; per-fold (per-topology) results are retained | aggregate outputs |
| Realizations | noise_added primary; clean as a separate robustness run; never pooled | config |
| Frozen before outer test | yes (hash-pinned; an authorization is bound to the hash) | `NEXT_PHASE_EXECUTION_HANDOFF.md` |

**Restrictions:** per-class results for NORMAL, FAULT and DELAY are descriptive only. Inference is conditional on three simulated topologies.
