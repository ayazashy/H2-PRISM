# Execution Clearance Record (primary run)

- **Date:** 2026-11-11.
- **Basis:** the governance rule recorded in `FINAL_PROTOCOL_DECISION.md` and `final_acceptance/FINAL_GOVERNANCE_AND_GATE_RECORD.md` §3. Each named-owner item is either attested by its owner or waived in writing by the project lead, naming the item.

## Decision given in writing in the session chat by Ahmed Zayed, project lead

Answering an explicit question that named each item, Ahmed Zayed:
- waived F-D15, F-D16 and A-D10;
- approved PA-1;
- authorized ONE primary run (noise_added, config `f788b6d8…`, output `03_results/primary_protocol/PRIMARY`).

**These are project-lead waivers, not signatures of the named owners.** Faisal's and Yazan's personal reviews were not given and remain open follow-ups.

| Item | Status for this run | Technical evidence | Remaining (non-blocking) follow-up |
| --- | --- | --- | --- |
| F-D15 Faisal code acceptance | WAIVED_BY_PROJECT_LEAD | independent review `final_acceptance/FINAL_CODE_AND_METHOD_AUDIT.md`; full regression suite | Faisal review |
| F-D16 Faisal contract v2 acceptance | WAIVED_BY_PROJECT_LEAD | `configs/interface_contracts.yaml` enforced by `tests/test_interface_contract.py` | Faisal review |
| A-D10 Gates 1–3 attestation | WAIVED_BY_PROJECT_LEAD | `00_governance/GATE_DECISIONS.md` (Gate 1 PASS; Gates 2–3 CONDITIONAL; engineering re-verification) | Yazan (gate owner) / Ahmed attestation |
| PA-1 matched-coverage tie rule | APPROVED_BY_PROJECT_LEAD | `FINAL_PROTOCOL_DECISION.md` Amendment PA-1; `tests/test_tie_policy.py` | Faisal (F10 owner) concurrence |

**Consequence:** results from this run are reported with the note "executed under project-lead waivers of F-D15, F-D16 and A-D10". They are subject to change if a later owner review finds a defect.

## Verified artifact identities (2026-11-11)

| Artifact | SHA-256 |
| --- | --- |
| FINAL_EXPERIMENT_CONFIG.yaml (final-protocol-1.1) | `f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae` |
| manifest v0.2 | `36bcbaf97bb17659995f393884d1dcde3bbca9236c3dcdcc6e7651e61538fb59` |
| outer folds | `3b21d8231a40245140f32aa6cb5193e3f45b05bd57cbb079ccccd69aafa8b1dd` |
| inner folds | `ebff65da38a5e70e45e1f1e0c4303b518ba13f9874aed06a3a191bf9c0963c5b` |
| label mapping | `61a3182b04e0fd7c9728945f07ab7eee13fe8fb75a8f4b55a999244cb49c1f18` |
| feature register | `3dd5e927e3473d01168b39ca7539d51fd5d599621bb6263bae20bfdc25bfc137` |

Raw files are verified per file by the runner preflight (manifest SHA-256 per realization).

**Authorization file:** `06_audit_preparation/EXECUTION_AUTHORIZATION_PRIMARY.yaml`. It is validated by `primary_protocol.check_authorization`, whose gate is unchanged.

## R2: corrected rerun (2026-11-11)

- **Run 1 (`db9acd23ef58`):** invalid for conclusions because an order-reversing sigmoid calibration was selected in fold 3. It is archived with `INVALIDATION_NOTE.md`.
- **Fix:** `calibration.Calibrator.monotone`. `select_calibration` never selects a non-monotone map; regression test added. No protocol value changed.
- **Authorization:** the project lead explicitly authorized ONE corrected rerun under the same waivers and approval: `EXECUTION_AUTHORIZATION_PRIMARY_R2.yaml`.
