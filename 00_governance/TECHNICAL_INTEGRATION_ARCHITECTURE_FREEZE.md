# Technical Integration Architecture Freeze (F12)

- **Status:** ARCHITECTURE RECORDED 2026-11-11 (technical review). Faisal attestation NOT_RECORDED (F-D16).
- **Interfaces:** `configs/interface_contracts.yaml` v2.0.0, enforced by `tests/test_interface_contract.py`.
- **Change control:** `00_governance/CHANGE_CONTROL_LOG.csv`.

## Components and data flow

```
manifest v0.2 (pinned) ──► feature_table.build_feature_table ──► windows.generate_windows ──► features
        │                         (one realization; per-file SHA-256)                          │
        ▼                                                                                       ▼
 preflight (27 checks, fail closed) ───────────────► runner primary_protocol.run ◄── FINAL_EXPERIMENT_CONFIG (pinned)
                                                        │ per outer fold (LOTO)
                         development_stage: baseline.select_on_development → calibration → D(x) (other topology)
                                            → comparators → combined_score (cross-fitted) → development thresholds
                         outer_stage (authorized only): refit → calibrate → D(x) (development reference)
                                            → scores → policy (threshold transfer + PA-1 rank matching)
                                                        ▼
                         aggregate: coverage_risk, estimability, rq1 (5 comparisons), rq2, tie_sensitivity
```

## Frozen interfaces

| Interface | Owner | Version / hash | Enforced by |
| --- | --- | --- | --- |
| Manifest v0.2 | Yazan → Faisal | `36bcbaf9…` | preflight hash + schema; contract test |
| Label mapping | Yazan | `61a3182b…` | preflight hash |
| Outer / inner folds | Yazan evidence, Faisal design | `3b21d823…` / `ebff65da…` | preflight hash, isolation, inner-fold match |
| Feature register | Faisal | `3dd5e927…` | preflight hash; exact feature-set check |
| Experiment config | Faisal (delegated selection) | final-protocol-1.1 `f788b6d8…` | authorization binds the hash |
| Window / feature / prediction / decision / aggregate schemas | Faisal | contract v2.0.0 | `test_interface_contract.py` |
| Execution gate | project lead | authorization YAML with governance_clearance | `check_authorization`; 8 gate tests |
| Sensitivity overrides | Faisal | `SENSITIVITY_OVERRIDES` (code registry, one deviation each) | `test_every_registered_sensitivity_has_an_override` |
| Reporting inputs (A13) | Ahmed | consumes aggregate CSVs | `test_reporting_outputs.py` |

## Change-control rule

After this freeze, any change to IDs, mappings, eligibility, manifests, folds, features, protocol values or schemas requires:
- a new entry in `CHANGE_CONTROL_LOG.csv`;
- a new config hash where the protocol changes;
- re-running the full test suite and the real-data preflight.

An authorization file bound to an old hash is refused automatically.
