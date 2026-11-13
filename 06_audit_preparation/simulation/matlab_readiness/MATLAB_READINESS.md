# MATLAB environment integration and H2Net v1 execution readiness

Date: 2026-11-13. Machine: the project lead's Acer Aspire (AMD Ryzen 5, 8 GB RAM, Windows 11), academic licence for MATLAB, Simulink and Simscape.

## 0. What has and has not happened

| Item | Fact |
|---|---|
| MATLAB on this machine | **R2026b Update 1 (26.2)** under `C:\Program Files\MATLAB\R2026b`. On 2026-11-13 at 21:47 the MathWorks Product Installer was **still running** (install started 21:36, about 4.5 GB on disk). `toolbox\simulink` and `toolbox\physmod\simscape` are present. |
| MATLAB executions so far | Two `matlab -batch` probes (`disp(version)`) **failed with exit status 1 while the installer was running**. No log was produced. **None of the readiness scripts has been run in MATLAB.** No environment, smoke-test or integration result exists yet. |
| R2026b vs the requirement | R2026b is later than the required R2025a. The released models were saved in R2025a. They open in later releases but **must never be saved** there, because saving upgrades the file format; the scripts only load temporary copies. |
| What was verified without MATLAB | The pinned expectations are current and consistent with the committed records. The `.m` scripts pass a static safety scan (no save, no `sim`, no parallel pool, no value-changing `set_param`, `close_system(…, 0)` only, released files only copied). The Python report checker is tested on synthetic reports (`tests/test_matlab_readiness.py`, 21 passed). |

## 1. Installation and compatibility checklist

| # | Requirement | How to confirm | Status |
|---|---|---|---|
| 1 | MATLAB ≥ R2025a | `version` | R2026b being installed |
| 2 | Simulink | `ver('simulink')` | folder present; licence untested |
| 3 | Simscape (Foundation library `fl_lib`, `nesl_utility`). Simscape Fluids is **not** needed. | `ver('simscape')`; `load_system('fl_lib')` | folder present; untested |
| 4 | Licences activated for MATLAB, Simulink and Simscape | `license('test', …)` and `license('checkout', …)` | untested |
| 5 | No Parallel Computing Toolbox pool | `gcp('nocreate')` is empty | n/a |
| 6 | ≥ 2.5 GB physical memory free before starting; ≥ 1.5 GB between models | `memory` | untested |
| 7 | About 10 GB free disk for MATLAB, plus a temporary folder for copies and the Simulink cache | Explorer | — |
| 8 | Repository Python `.venv` (authorization gates are called through `system()`) | `.venv\Scripts\python.exe` | present |
| 9 | Released `.slx` files under `data/raw/…/MATLAB_SIMSCAPE_Simulation` with pinned SHA-256 | E7 | files present (Python-verified hashes in `01_dataset_audit/raw_checksums.sha256`) |
| 10 | Hydrogen tables and `H2_REALGAS_TLU2_params.m` with pinned SHA-256 | E8 | present; hashes verify (`verify_frozen_hashes.py`) |

**Installation prerequisites** (if the installer has to be rerun):
- Products: MATLAB, Simulink, Simscape.
- Sign in with the academic MathWorks account and activate the licence for the Windows user that will run the checks.
- Let the installer finish, then start MATLAB once interactively to complete activation and first-run setup before any `-batch` use.

## 2. Resource-safe execution on 8 GB RAM

1. **Close other heavy applications** (browsers, IDE indexers) before starting. Keep one MATLAB instance only.
2. **One process, one model at a time.** The smoke test loads one temporary copy, inspects or compiles it, closes it **without saving**, deletes the copy, and only then moves to the next model.
3. **No parallelism.** Never run `parpool`, `parsim` or batch simulations. E5 fails if a pool is open.
4. **Memory guard.**
   - E4 requires ≥ 2.5 GB available before starting.
   - Before each model, the smoke test requires ≥ 1.5 GB. Otherwise it **stops safely**: it writes the report with `stopped` set and closes everything.
5. **Small footprints.**
   - Reports hold metadata only, never signals.
   - Each phase's variables are cleared before the next.
   - The Simulink cache and code-generation folders point to the per-model temporary folder and are deleted with it.
6. **Limited logging.**
   - One line per check on screen, plus one JSON report per phase.
   - No diary of solver output.
   - `-logfile` only when diagnosing a crash.
7. **Fidelity is not traded for memory.** Solver, tolerances and discretisation are recorded, never changed. If memory is insufficient, close applications or run models individually with the subset argument.
8. **Later authorized simulations (H2Net V2–V6)** follow the same rules: one run per MATLAB process, `SaveFormat` restricted to the logged sensors, decimated export only after the run, memory guard before each run.

## 3. Command sequence after installation finishes

Run in **one** MATLAB session, started from the repository root. Use the interactive desktop first, so that activation completes.

```matlab
cd('C:\Users\<user>\Documents\H2-PRISM')
addpath tools/matlab
out = fullfile('06_audit_preparation','simulation','matlab_readiness','run_2026-11-13');
r1 = h2prism_verify_environment(out);          % Phase 1  -> ENVIRONMENT_REPORT.json
r3 = h2prism_smoke_test_models(out, true);     % Phase 3  -> SMOKE_REPORT.json (six models, one at a time)
r4 = h2prism_check_h2_integration(out);        % Phase 4  -> H2_INTEGRATION_REPORT.json
% or all three, stopping at the first FAIL:  h2prism_run_readiness(out)
```

If memory is tight, run the smoke test for a subset at a time, for example:

```matlab
h2prism_smoke_test_models(out, true, {'Normal_HNetwork_gest_center'})
```

Then, from a terminal in the repository root:

```bash
.venv/Scripts/python.exe tools/matlab/check_matlab_reports.py 06_audit_preparation/simulation/matlab_readiness/run_2026-11-13
```

```bash
.venv/Scripts/python.exe tools/governance/verify_frozen_hashes.py
```

**Standalone run (recommended on this 8 GB laptop).** Close Claude and other applications, open a terminal **in the repository root**, and run the command below. `RUN_LOG.json` in the run folder records how far the run got and any error; `matlab_run.log` captures the console output. Both must be present for the validator to tie the reports to one run.

```bash
cd /c/Users/<user>/Documents/H2-PRISM
```

```bash
"/c/Program Files/MATLAB/R2026b/bin/matlab" -logfile 06_audit_preparation/simulation/matlab_readiness/run_2026-11-13/matlab_run.log -batch "addpath tools/matlab; exit(~h2prism_run_readiness('06_audit_preparation/simulation/matlab_readiness/run_2026-11-13'))"
```

Equivalent non-interactive run, once MATLAB has been activated:

```bash
"/c/Program Files/MATLAB/R2026b/bin/matlab" -batch "addpath tools/matlab; exit(~h2prism_run_readiness('06_audit_preparation/simulation/matlab_readiness/run_2026-11-13'))"
```

## 4. PASS/FAIL criteria

`check_matlab_reports.py` re-derives the verdict from the individual checks; it does not trust each report's own `overall` field.

| Phase | PASS requires | FAIL examples |
|---|---|---|
| 1 Environment | E1 release ≥ R2025a; E2/E3 products installed and licences check out; E4 memory not FAIL; E5 no pool; E6 Python runs; E7 all 6 released models with pinned hashes; E8 hydrogen files with pinned hashes and a consistent parameter struct; E9 H2Net v1 grant-bound files unchanged; E10 `fl_lib`, `nesl_utility`, `simulink` load | missing licence, hash mismatch, < 2.5 GB free |
| 3 Smoke (per model) | .1 released hash; .2 copy loads; .3 no unresolved library links; .5 Gas Properties (G) SID 4 has `gas_spec = 1` and R = 0.287 (as recorded in `GAS_MODEL_LIMITATION.md`); .6 every sensor SID exists; .7 To Workspace variables equal the expected set (13 or 16); .8 interface SIDs 59/241/213/222/312/215 readable (normal models); .9 update diagram succeeds; .10 released file hash **and** timestamp unchanged afterwards; no memory-guard stop | a gas specification that contradicts the recorded limitation is a **FAIL to investigate**, not something to correct silently |
| 4 Integration | I1 grant-bound files; I3 parameter-file hash; I4 Gas Properties (G) exposes every table field; I5 a real-gas option exists | missing dialog parameter names (table layout must be adapted before X05) |

**Verdict `READY_FOR_AUTHORIZED_STEPS`** means software, load, compile and interface readiness only.
- It is **not physical validation**: no V2–V8 result exists.
- It **does not open the H2Net v1 build gate**.
- WARN results (non-empty model callbacks, total memory below 7 GB) are reported for review but do not fail.

Data recorded for open items:
- **X04:** the smoke report's `extra.models.<name>.gas_block` and `.pipes` hold the resolved `gas_spec` options and every Pipe (G) friction parameter. That is the evidence X04 needs, once it has actually been run.

## 5. H2Net v1 integration path (not executed)

1. Phases 1, 3 and 4 PASS. Commit the three reports.
2. Owners record `PARAMETER_DECISIONS.yaml` → `status: DECIDED` (X03: S2–S6, S8 and V8 with sources). This is not done, and acceptance cannot be recorded on the owners' behalf.
3. X06: `python tools/simulation/h2net_v1_envelope_screening.py --targets` computes V2 reference targets **before** any simulation. It currently refuses (exit 2).
4. X05, under grant (b) of `MODEL_DEVELOPMENT:H2NET_V1_PROPERTIES_AND_STEADY_STATE`:
   - copy each released model to a new file named `h2net_v1_<…>.slx` outside `data/raw`;
   - load the copy and call `h2prism_apply_h2_gas_to_copy(copy, <real-gas value from H2_INTEGRATION_REPORT>)`. It refuses unless the name prefix, the location, the grant hashes, the table hash and `DECIDED` all check out;
   - apply S2–S8;
   - save the **copy**;
   - record the parameter diff against the released SIDs.
5. X07, under grant (c): run only the V2–V6 validation simulations, one per process, against the X06 targets.

Hydrogen properties are never substituted into the released models.

## 6. Remaining blockers before authorized H2Net v1 model construction

| Blocker | Owner | Clears |
|---|---|---|
| MATLAB installation finishing, activation, then Phases 1, 3 and 4 PASS on this laptop | project lead (run the commands above) | X27; part of G-03; evidence for X04 / A-16 / A-17 |
| H2Net v1 engineering parameters S2–S6, S8 and V8 decided with sources | Yazan + modeller (Faisal reviews) | X03, which opens the build gate and X06 |
| V2 reference targets computed before simulation | Ahmed (X06, after X03) | X07 acceptance basis |
| Executor named in the grant: "Yazan or a designated modeller" | project lead / Yazan | executing X05 and X07 on this laptop requires the project lead to be designated, or Yazan to run them |

## 7. Execution record

| When (2026-11-13) | What | Result |
|---|---|---|
| 21:42, 21:45 | `matlab -batch` probes during installation | exit 1, no log (installer still running) |
| 22:59 | version probe after installation | R2026b Update 1 (26.2.0.3433840); Simulink 26.2, Simscape 26.2; licences test = 1 |
| 23:01 | first readiness run | aborted in `h2prism_sha256file`: **no Java runtime in R2026b** (tooling defect; fixed in `f0bfddd` with pure-MATLAB SHA-256) |
| 23:04 | Phase 1 rerun (`ENVIRONMENT_REPORT.json`) | **FAIL**, 26 PASS / 1 FAIL. All six released models and four hydrogen files reproduce their Python-pinned hashes; licences check out; libraries load; **E4: 771 MB available < 2500 MB** (MATLAB 1642 MB of 7413 MB) |
| after 23:13 restart | RAM remeasured before launch | 657–694 MB available (non-paged kernel pool about 840 MB; Claude about 1.6 GB, Chrome, Edge WebView2, Discord running). MATLAB not launched |
| about 23:17–23:20 | standalone run by the project lead | **no report written** (no file newer than 23:04 in the run folder; MATLAB debug logs empty). Cause not recoverable. The runner now writes `RUN_LOG.json` at start, after each phase and on any error, and the validator rejects reports without a run log or older than the run |

Status: **Phases 1, 3 and 4 not verified.** Validator verdict: NOT_READY.
