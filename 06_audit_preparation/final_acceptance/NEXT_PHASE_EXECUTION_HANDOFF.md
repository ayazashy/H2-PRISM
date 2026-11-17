# Next-Phase Execution Handoff

- **Branch:** `audit/preparation-integration`, local only. See `SESSION_CHECKPOINT.md` for the HEAD.
- **Verdict:** `PRE_EXPERIMENT_ACCEPTANCE_BLOCKED`. Only the human items in step 1 remain.
- No primary or robustness experiment has been run.

## 1. Clear the blockers (humans only)

| Item | Who | Evidence to review |
| --- | --- | --- |
| F-D15 code acceptance | Faisal | `FINAL_CODE_AND_METHOD_AUDIT.md`, `FINAL_VALIDATION_EVIDENCE.md` |
| F-D16 interface contract v2.0.0 | Faisal | `configs/interface_contracts.yaml`, `FINAL_EXPERIMENT_CONTRACT.md` |
| PA-1 matched-coverage tie rule | Faisal (F10), or the project lead under the delegation | `FINAL_PROTOCOL_DECISION.md` (Amendment PA-1) |
| A-D10 Gates 1–3 | Ahmed, with Yazan as gate owner | `FINAL_GOVERNANCE_AND_GATE_RECORD.md`, `00_governance/GATE_DECISIONS.md` |

Each item is either attested by the named owner (name and date) or waived in writing by the project lead.

## 2. Re-verify (safe at any time; no model fitting)

```
python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out <tmp>/preflight --dry-run
```

Expect `PREFLIGHT_PASSED`, 28/28 checks, 27,993 windows, feature table `4d1310a6…`.

## 3. Authorization file (written by the project lead; the runner never creates it)

For example `06_audit_preparation/EXECUTION_AUTHORIZATION_PRIMARY.yaml`:

```yaml
authorized: true
scope: PRIMARY_EXPERIMENT            # ROBUSTNESS_EXPERIMENT for the clean realization
config_sha256: f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae
authorized_by: <name>
date: <YYYY-MM-DD>
governance_clearance:                # each value must start with ATTESTED or WAIVED
  F-D15: <ATTESTED by Faisal YYYY-MM-DD | WAIVED by project lead YYYY-MM-DD: reason>
  F-D16: <...>
  A-D10: <...>
  PA-1: <...>
```

The runner refuses to run if any field is missing, the scope or config hash does not match, or any clearance is absent or does not start with ATTESTED or WAIVED.

## 4. Execute (once only; resumable with the same command)

```
python tools/experiments/run_primary_protocol.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out 03_results/primary_protocol/PRIMARY --execute-primary --authorization 06_audit_preparation/EXECUTION_AUTHORIZATION_PRIMARY.yaml
```

- **Output directory:** use exactly `03_results/primary_protocol/PRIMARY`; `configs/reporting_figures.yaml` reads from there.
- **Registered sensitivity analyses (Phase 10):** one authorization per analysis, `scope: SENSITIVITY_EXPERIMENT:<name>`:
  `--execute-sensitivity --sensitivity <name> --out 03_results/primary_protocol/SENSITIVITY_<name>`.
  `policy_warning_only` needs no separate run (it is produced inside every run).
- **Reports:** after execution, `python tools/reporting/build_research_figures.py --config configs/reporting_figures.yaml --out-dir <dir>` (likewise `build_research_tables.py`).

- **Robustness run:** `--execute-robustness` with a ROBUSTNESS_EXPERIMENT authorization and its own `--out`.
- **Runtime:** unmeasured. Expect tens of minutes per realization (RF grid of 8 settings × 2 inner splits + refit per fold).
- Do not rerun with altered settings after seeing outer-test outputs.
- Report every outcome, including NOT_ESTIMABLE and tie sensitivity.

## 5. After execution (not part of pre-experiment acceptance)

- F5/F6/F10/F11 result files and A8/A11 writing.
- Sensitivity-analysis runs (all 9 paths implemented in Phase 10).
- Owner documentation gaps listed in `TEAM_PLAN_COMPLETION_MATRIX.csv`.
