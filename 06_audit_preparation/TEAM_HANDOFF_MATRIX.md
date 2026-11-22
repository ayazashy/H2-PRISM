# Team Handoff Matrix

No owner approval was recorded on anyone's behalf. Every item below waits for the named person.

## To Yazan (dataset evidence owner)

| # | Handoff | Evidence | Decision or approval needed | Unblocks |
| --- | --- | --- | --- | --- |
| Y-1 | Merge `SCEN_UNKNOWN_UNKNOWN_LEAKG4` into `SCEN_UPSTREAM_TRANSIENT_LEAKG4`; derive Scenario_IDs from content-equivalence classes | ISS-02; `splits.content_equivalence_groups` | Yazan correction | Y5, F4 |
| Y-2 | Decide the canonical export tree (the clean tree matches the 121-file / 2.42 M-row description) and keep one file per scenario | ISS-04, ISS-05 | Yazan decision, Faisal review | F3, F4 |
| Y-3 | Rebuild families from evidence; report conservative and strict views; Ahmed samples the decisions | ISS-07 | Yazan; Ahmed sample review | Y5, F4 |
| Y-4 | Correct sampling and phase statements; give onsets in rows and seconds | ISS-06, ISS-10 | Yazan | F3, A3 |
| Y-5 | Consistent compound rule; NORMAL rule; pre-event policy (jointly with Faisal) | ISS-09 | Yazan + Faisal; Ahmed scientific approval | Y4 freeze |
| Y-6 | Regenerate folds; pass `validate_outer_folds`; add the family assertion to `test_dataset_audit.py` | ISS-01, ISS-17 | Yazan | F4 |
| Y-7 | Review loader changes (`load_fold` raises; checksum-verified sample fallback) | ISS-12 | Yazan review | — |
| Y-8 | Re-issue Y7 after Y-1…Y-6; withdraw the "approved by Ahmed" statement until it is recorded | Y7 section | Yazan, Faisal, Ahmed | All primary work |

## To Faisal (technical and experimental owner)

| # | Handoff | Decision or approval needed |
| --- | --- | --- |
| F-1 | Review and accept or modify `io.py`, `windows.py`, `features.py`; choose window/stride, `label_mode`, the feature set | Faisal technical acceptance |
| F-2 | Decide the F4 design once Y-1…Y-6 are done; write the protocol and `configs/frozen_evaluation_config.yaml`; Ahmed approves before the outer test | Faisal decision; Ahmed approval |
| F-3 | Accept `baseline.py` / `calibration.py` as the F5/F6 implementation, or replace them | Faisal |
| F-4 | Make the D design decisions (k, weighting, prior correction, flag thresholds, scenario balancing) | Faisal; Ahmed math review (A4) |
| F-5 | Make the policy decisions (candidate source, singleton handling, max set size, blocking flags) and the development threshold procedure | Faisal; Ahmed validity review |
| F-6 | Implement the F10 cross-fitted correctness meta-model and runner; F11 family bootstrap | Faisal |
| F-7 | Accept or adjust the proposed F12 contract amendments; start `CHANGE_CONTROL_LOG.csv` | Faisal |
| F-8 | Technical acceptance of A12–A16 (integration gate: source/test review → config/fold check → reproducibility → schema/provenance → acceptance) | Faisal |
| F-9 | Verify the F1 component classification in `REPOSITORY_BASELINE.md` | Faisal |

## To Ahmed (research lead)

| # | Handoff | Decision or approval needed |
| --- | --- | --- |
| A-1 | Decide whether to keep or delete the quarantined illustrative files; correct README §6–7 and `05_documentation/FIGURE_SPECIFICATION.md`, which still describe fabricated figures and a "zero leakage" design | Ahmed |
| A-2 | Re-record `GATE_DECISIONS.md`: Gates 1–3 cannot stay PASS on the current evidence; adopt the plan status vocabulary in `MASTER_TASK_REGISTER.csv` | Ahmed (A9) with the gate owners |
| A-3 | Review the draft symbol register and problem formulation (A4) | Ahmed |
| A-4 | Write A10 provenance from the Yazan evidence plus `PROVENANCE_INDEX.csv`; A3 after the Y corrections | Ahmed |
| A-5 | Add "Plan 2" PDFs to `assets/` (ISS-19) | Ahmed |
| A-6 | A14–A16: submit for Faisal acceptance once F3/F4 exist; nothing executes before then | Faisal acceptance |
