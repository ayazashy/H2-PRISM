# Maintenance closure report

Branch `research/integrated-validation`, HEAD `02cc44e` at report generation. All commits are local; nothing is pushed or merged.
Every count below is read from the cited records by `03_results/maintenance/build_closure_report.py`.

## Commits in the maintenance phase
- `02cc44e Record the final full-suite run and maintenance verification tooling`
- `eb2a9f5 Partly resolve L20: restore Stage-2 modules under non-colliding names`
- `6114f6c Resolve L21: pin line endings of checksum-bound files to their certified bytes`
- `adebb73 Scope the v1 verifier's integrity check to protected files via a change register`
- `1eb820d Repair L22: rename v1 Q1 figure manifest to Q1_FIGURE_MANIFEST.csv`

## Resolved issues

- **L22 — manifest-name collision.**
  - The v1 Q1 QA manifest was renamed to `Q1_FIGURE_MANIFEST.csv`, byte-identical.
  - Provenance: `publication_q1/quality_control/MANIFEST_RENAME_RECORD.csv`.
- **v1 verifier scope.**
  - The blanket "no file outside v1 may differ from 6eddd4a" check was replaced by a hash-pinned change register (`POST_BASELINE_CHANGE_REGISTER.csv`, 24 rows).
  - The check runs against two baselines: outside v1 against 6eddd4a, and v1 against its release 6b98a8a.
  - It compares committed blob content, so the result does not depend on line endings.
  - Unregistered additions, modifications, deletions and drift are still detected (`tests/test_verifier_scope.py`).
- **L21 — checkout-dependent checksum pins.**
  - All 210 affected files were identified (`L21_CRLF_PIN_SCAN.csv`).
  - 108 were pinned with `eol=crlf` and 98 with `eol=lf`.
  - Every re-pinned working copy now equals its pin: 206 files.
  - No pin, record, dataset or blob was edited (`L21_MIGRATION_LOG.csv`).
- **L20 — Stage-2 import conflict (software part).**
  - The Stage-2 windowing module and runner were restored under non-colliding names (`simnet_windows.py`, which is byte-identical, and `simnet_experiments.py`).
  - The frozen Center `windows.py` is unchanged.
  - Details: `L20_STAGE2_RESOLUTION.md`.

## Final verification

**Full test suite** (`logs/pytest_full_final.log`): 2 failed, 774 passed, 43 skipped, 1258 warnings in 1199.71s (0:19:59)

| | passed | failed | skipped | collection/other errors |
|---|---|---|---|---|
| before maintenance (v2 audit, `integrated_validation_v2/03_execution/logs/pytest_full.log`) | 743 | 13 | 42 | 1 |
| after maintenance | 774 | 2 | 43 | 0 |

The two runs differ in more than repairs: this phase also added regression-test modules, and the Stage-2 module now collects.

### Remaining failures and root causes
| test | root cause |
|---|---|
| `tests/test_faisal_pipeline.py::test_accepted_frozen_config_is_supported` | L20 remainder (governance): the shared frozen evaluation config is the registered final-protocol-1.1; Stage-2 expects its own config 1.0.2 |
| `tests/test_h2net_candidate_evidence.py::test_released_network_extraction_is_current_and_matches_known_structure` | environment: needs the external H2-SimNet Simscape release (SLX files) outside the repository |

Unclassified failures: 0.

### Package verifiers
| verifier | result | status |
|---|---|---|
| v2 validation package | 35/35 checks pass | PASS |
| v1 advanced validation | 57/57 checks pass | PASS |
| v1 publication package | 275/275 checks pass | PASS |

### Protected-scope check (v1 `SCOPE_CHECK.csv`)
| scope | authorized | exempt | unauthorized |
|---|---|---|---|
| outside_v1 | 143 | 0 | 0 |
| v1 | 11 | 1 | 0 |

## Artifact integrity
- **Scientific results:** no result, figure, table, dataset, label, partition, model or frozen manifest changed.
  - L21 changed only `.gitattributes` and working-copy line endings; blobs are identical.
  - L22 renamed one file with identical bytes.
  - L20 added and renamed code modules.
  - The v1/v2 checksum manifests and figure hashes verify (table above).
- **Frozen artifacts:** the Center baseline `windows.py`, the R2 frozen run, Protocol 2.0 records and figure-system manifests are byte-unchanged in content.
  - Every committed change outside the v1/v2 packages is listed with exact before/after hashes in the change register.

## Remaining blockers

| Blocker | Type | Owner | Exact action |
|---|---|---|---|
| D1 topology/label attribution | **Scientific approval** (external) | Dataset owner | Record `06_audit_preparation/protocol2/OWNER_DECISION_D1.yaml` (decision, decider, date, approved manifest SHA-256). Then the project lead authorizes `EXPLORATORY_REPLICATION`. |
| L20 remainder: Stage-2 frozen config 1.0.2 and 7 Stage-2 methodology specs | **Methodological / governance** | Project lead + Stage-2 (F4) owner | Choose: retire 1.0.2 (superseded by final-protocol-1.1), or keep it as a separately named LEGACY config with labelled historical specs. See `L20_STAGE2_RESOLUTION.md`. |
| `certified_evidence.py` pinned LF by `baseline_freeze_v1` and CRLF by `center_evidence_enhancement` execution manifest | Engineering (provenance), no test affected | Center baseline owner | Decide which record is authoritative, or annotate the other as recorded on a CRLF working copy. No line-ending rule can satisfy both. |
| H2-SimNet released Simscape files needed by `test_h2net_candidate_evidence` | Environment | Data custodian | Provide the SLX release path on the test machine. |
| Test suite rewrites `00_governance/ACTION_EXECUTION_STATUS.csv` and `ISSUE_CLOSURE_MATRIX.csv` | Engineering (test hygiene) | Governance-tooling owner | Make those tests write to a temporary directory. Meanwhile, restore the files after a full run (done here). |

Scientific blockers: D1. Methodological: the L20 remainder. Everything else is engineering or environment.

`integrated_validation_v2/01_audit/LEAKAGE_REGISTER_V2.csv` and `TEST_FAILURE_TRIAGE.csv` are the audit-time snapshot taken before this phase. For L20 and L21 they are superseded by this report and are intentionally left unchanged.

## Repository readiness
- Maintenance phase: **closed**. Every safely executable repair is committed and verified.
- Ready for scientific-results finalization: **yes**, within the evidence limits recorded in `integrated_validation_v2` (diagnostic claims exploratory; H3 is the only hypothesis supported within scope).
- Not ready: confirmatory diagnostic claims (D1), and Stage-2 pipeline execution (L20 governance decision).

## Next actions for the research team
1. Dataset owner: record the D1 decision. Then run `integrated_validation_v2/03_execution/scripts/d1_correction.py replicate` under a project-lead authorization.
2. Project lead + F4 owner: decide the Stage-2 config question (option a or b in `L20_STAGE2_RESOLUTION.md`).
3. Center baseline owner: resolve the `certified_evidence.py` dual pin.
4. Begin scientific-results finalization from `integrated_validation_v2/06_reports` and the hypothesis registry.
5. Before every release, run `verify_package.py`, `verify_av.py` and `verify_v2.py`. Record each further post-baseline change with `03_results/maintenance/register_change.py`.
