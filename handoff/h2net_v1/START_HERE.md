# H2Net v1 — execution handoff (Windows, 16 GB)

**For Yazan.** Run everything from this repository checkout in **Windows PowerShell**. Steps run one at a time; there are no parallel workers.

Each script stops with `FAILED: <reason>` when a prerequisite is missing. Fix the reason and rerun the same script. When anything stops, run `05_PACKAGE_RETURN.ps1` and send the ZIP to Ahmed: partial results are useful, and nothing is ever fabricated.

## 0. One-time setup

**Status of the code.** The Python tools and gates are tested. **Every MATLAB step (build, structural edits, validation, scenarios) is implemented but has never been executed**, so treat its first run as verification. Physical validation exists only once `VALIDATION_REPORT.json` says `overall: PASS`.

**Released raw models (not in Git).** Download the H2-SimNet archive (Zenodo record 17871393) and extract it to `data\raw\H2-SimNet-Dataset\`, as described in `01_dataset_audit/HOW_TO_ACCESS_DATA.md`. The archive MD5 is in `01_dataset_audit/DATASET_AUDIT_AMENDMENT_2026-11.md`. Step 01 verifies the six model hashes.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements-lock.txt
```

- MATLAB R2025a or later, with Simulink and Simscape licensed. R2026b is fine.
- If `matlab.exe` is not on PATH, set `$env:H2PRISM_MATLAB` to its full path.
- If PowerShell blocks the scripts, run them as `powershell -ExecutionPolicy Bypass -File handoff\h2net_v1\01_PREFLIGHT.ps1`.

## 1. Decisions (yours, the modeller's and Faisal's; nobody else can record them)

1. Read `06_audit_preparation/simulation/h2net_v1/H2NET_V1_DESIGN_FREEZE_SPEC.md` and `H2NET_V1_APPROVAL_CHECKLIST.md`.
2. Copy the sections of `06_audit_preparation/simulation/h2net_v1/PARAMETER_DECISIONS_TEMPLATE.yaml` into `PARAMETER_DECISIONS.yaml` in the same folder. Replace **every** `<...>` and set `status` and `date`. Each section's `decided_by` must name the person who decided it.
3. The project lead (Ahmed) fills `EXECUTOR_DESIGNATION.yaml` from `EXECUTOR_DESIGNATION_TEMPLATE.yaml`, in the same folder.
4. Check the decision gates:

   ```powershell
   .venv\Scripts\python.exe tools\simulation\h2net_v1_gates.py check build
   ```

   This lists every missing item.

## 2. Run

| Step | Command | Gate |
|---|---|---|
| 01 | `handoff\h2net_v1\01_PREFLIGHT.ps1` | Python, MATLAB, RAM ≥ 15 GB, disk ≥ 20 GB, frozen and model hashes |
| 02 | `handoff\h2net_v1\02_VALIDATE_ENVIRONMENT.ps1` | R0 MATLAB readiness. Close other applications first. |
| 03 | `handoff\h2net_v1\03_BUILD_AND_VALIDATE.ps1` | decisions, executor, grant, R0. Builds the `h2net_v1_*` copies, runs V2–V6, evaluates. |
| 04 | `handoff\h2net_v1\04_RUN_AUTHORIZED_SCENARIOS.ps1` | **only** with validation PASS, Faisal's methods review (cited noise model) and the separate grant `AUTH_H2NET_V1_DATASET.yaml` |
| 05 | `handoff\h2net_v1\05_PACKAGE_RETURN.ps1` | always. It packages what exists. |

**Rules for every step:**
- The original released models are never opened for saving; only copies are built.
- If a structural build operation fails, the copy is discarded and `BUILD_REPORT.json` names the failing operation.
- V7 (transients) needs its own grant `AUTH_H2NET_V1_V7.yaml` and is not part of step 03.

## 3. Return to Ahmed

Send both files from `h2net_v1_run\return\`:
- `H2NET_V1_RETURN_<time>.zip`
- `H2NET_V1_RETURN_<time>.zip.sha256`

The ZIP contains the decision records, all reports and logs, the built models, and the dataset if one was generated. It carries a status file and checksums. It excludes licences and caches.
