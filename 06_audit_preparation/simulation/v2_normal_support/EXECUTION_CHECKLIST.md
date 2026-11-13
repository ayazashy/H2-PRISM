# V2 NORMAL-support simulation: execution and validation checklist (package v2)

- **Scope:** `SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION`.
- **Executor:** Yazan, or a person he designates.
- **Status:** not executed. The package v1 authorization is **void**. Package v2 is **authorized by the project lead (2026-11-13) for one execution attempt** (`AUTH_SIMULATION_GENERATION_V2_REQUEST.yaml`, `AUTHORIZATION_HISTORY.csv`). Executor acceptance is not recorded.

Every command below runs from the repository root. Nothing in this package modifies the released models or data.

## 0. Purpose and limits of the generated data

- **Exploratory NORMAL-support generation only**, using the released H2-SimNet NORMAL models unchanged.
- It adds independent NORMAL operating points so that support-dependent statistics (e.g. Distinguishability v2) *can* be defined later.
- It is **not** an experiment and produces no result about any method.
- The confirmation partition is generated and sealed for possible future use under a frozen protocol and a separate authorization. Generating it does not authorize any confirmatory analysis.
- **Gas:** the released models define an air-like gas (R = 0.287 kJ/kg/K; `READINESS_CHECK_2026-11-13.md`). Generated data must not be described as hydrogen-specific.

## 1. Verified dependencies and compatibility (from the `.slx` files themselves)

| Item | Verified value | Source |
| --- | --- | --- |
| MATLAB release | **R2025a or later**. The models were saved in R2025a, 25.1.0.2943329; Simulink cannot open a model in an older release. | `metadata/mwcorePropertiesReleaseInfo.xml` in each `.slx` |
| Products | **MATLAB, Simulink, Simscape.** Libraries used: `fl_lib` (Simscape foundation gas library), `nesl_utility` (Simscape), `simulink`. Simscape Fluids is **not** needed. | `SourceBlock` of every block |
| Model configuration | StopTime 20000 s, start 0, variable-step auto in the file. The launcher overrides to **ode14x, fixed step 0.8 s (center) / 0.9 s (down, up)**, as in the released `models_launcher.m`. | `simulink/configSet0.xml`; `models_launcher.m` |
| Logging | To Workspace blocks, SaveFormat **Timeseries**, sample time −1 (inherited), returned in the `SimulationOutput` object | logging subsystem |
| Gas model | Gas Properties block (identical in all six released models): R = 0.287 kJ/kg/K (**air-like, not hydrogen**; reference cp/μ/k inconsistent with either gas, see readiness check); pressure table 0.001–10 MPa; `properties_range_check = error` (out-of-range pressure stops the simulation); temperature table 150–2,000 K | block parameters |
| Released model SHA-256 (must match before and after) | center `710711f41e33adb9ea54220580adefd0065eeb9a8a376727dd045fc474ed7b1e`<br>down `2fcf47dfe91adf54b758b3f2562a727755e4f0ecd8bbc8e6783aaceced14f496`<br>up `5c3c76e9866dcbbe0a2ec6937d150c6ab9af3ec010ea92df19c2ff92426380d4` | `03_results/diagnostics/sensor_correspondence/MODEL_FILES.csv` |

**Parameter targets.** They are set by block SID through `Simulink.ID.getHandle`, which avoids block names containing line breaks. The SIDs are identical in all three models, and every value is read back and asserted.

| SID | Block | Parameter | Physical meaning | Design levels | Released value |
| --- | --- | --- | --- | --- | --- |
| 59 | PS Step | `final_value` | pressure-rise set-point of **Pressure Source (G)3** (the compressor fed by the supply reservoir) after t = 25 s | 6.1 / 6.4 / 6.7 MPa | 6.4 |
| 241 | PS Ramp | `slope` | ramp of the differential of **Pressure Source (G)1** (a let-down element: initial −0.3 MPa) | 0 / −1e-5 / −2e-5 MPa/s | −1e-5 |
| 213, 222, 312, 215 | Local Restriction (G)3…(G)6 | `restriction_area` | withdrawal openings G3–G6 to atmosphere (set jointly) | 0.75 / 1.0 / 1.25 × 1e-3 m² | 1e-3 |

## 2. Operating-range validity (before execution) and what can only be checked after

> **Erratum (final check, 2026-11-13).** The bullets below used the gas block's *table* fields (0.001–10 MPa, 150–2,000 K) and air (γ = 1.4). Those fields are inactive if `gas_spec = 1` selects the perfect-gas specification (expected; confirmed in step A of `HANDOFF_FOR_YAZAN.md`).
>
> - **Active limits:** pressure ≥ **0.1 MPa** (range check = error), with no upper pressure or temperature limit.
> - **Active constants:** imply γ ≈ 5.75 and an estimated compressor outlet temperature of about **1,920–2,060 K**, the same as in the released runs.
> - **Static validity of the 9 points:** still holds under these limits. The lowest pressures are the atmospheric withdrawal ends at p_atm = 0.1 MPa, as in the release.
> - Details: `FINAL_PRE_EXECUTION_CHECK.md`.

**Static validity (as originally written; see the erratum above):**

- **Highest pressure:** about 0.684 MPa (supply reservoir) + 6.7 MPa = **7.38 MPa**, below the 10 MPa table limit. The released maximum is 7.12 MPa.
- **Compressor outlet temperature (isentropic, air):** at most about 580 K, inside 150–2,000 K.
- **Let-down differential at t = 20,000 s:** −0.3 (slope 0) to −0.7 MPa (−2e-5).
- **Lowest pressures:** the atmospheric withdrawal ends at about 0.1 MPa, above the 0.001 MPa limit.
- **Withdrawal flows** scale with the opening (±25%) and stay positive.

**Dynamic stability cannot be proven without running.** It is therefore tested after the run with checks fixed **now**, derived from the released clean NORMAL runs, which all pass them (released values in brackets):

| Check | Criterion | Released NORMAL |
| --- | --- | --- |
| P1 grid | 20,000 rows at t = 0…19,999 s, all finite | pass |
| P2 pressure | every PS in [0.09, 9.5] MPa | 0.10–7.12 |
| P3 withdrawal | MFS1, MFS3 > 0 for t ≥ 1,000 s | ≥ 5.9 |
| P4 drift (steady 1,000–19,000 s) | max slope of consecutive 60 s means ≤ 7.5e-4 MPa/s (PS), 2.75e-3 kg/s² (MFS) | 1.5e-4, 5.4e-4 |
| P5 oscillation | max \|60 s mean − centred 11-window mean\| ≤ 0.053 MPa (PS), 0.163 kg/s (MFS) | 0.011, 0.033 |
| P6 noise (development only) | SD(noisy − clean) within 5% of 0.0005 MPa / 0.25 kg/s | — |

## 3. Correlated evidence (how the 27 runs may be counted)

- **Within an operating point:** the three runs share every parameter, so they are **one independence group** (`IG_V2N_…`), not three observations.
  - They differ only in network configuration.
  - In leave-one-topology-out work the same operating point in another topology is excluded from the reference, as for the existing groups.
- **Unit of inference:** the operating point. That gives **6 development and 3 confirmation units** — not 27 runs and not about 540,000 windows.
- **Across operating points:** points are independently parameterised but share factor levels. The confirmation points are new *combinations* of levels already present in development. They test interpolation within the design range, not extrapolation to new levels.
- **Across all runs:** every run comes from the same three model files and the same gas model (air). Any model-structure error is shared by all of them. New NORMAL groups add operating-point diversity, not model diversity.
- **Noise:** seeds are derived per run and are never scenarios. The noise is white at 1 Hz (verified on the release), so overlapping windows of one run are strongly dependent through the signal, not through the noise.
- **What 3 confirmation units allow:** a bootstrap is not meaningful. Results are reported per unit by enumeration, with no p-values.

## 4. Prerequisites (all must hold before step 5)

1. MATLAB R2025a or later with Simulink and Simscape licences. Python 3.12 with the repository environment (`pandas`, `numpy`, `pyyaml`).
2. About 1 GB free disk space: 27 solver-grid files plus 54 files at 1 Hz.
3. The released NORMAL models are present and match the SHA-256 values in §1:

   ```bash
   sha256sum data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets/Normal_HNetwork_gest_*.slx
   ```

4. The project lead's authorization is recorded in `AUTH_SIMULATION_GENERATION_V2_REQUEST.yaml` (done 2026-11-13). Confirm it is still active, i.e. no bound file has changed since:

   ```bash
   python tools/simulation/v2_normal_authorization.py
   ```

   Expected output: `ACTIVE: <name> <date>`, exit code 0. Anything else: stop.
5. `data/generated/v2_normal_support/` and `data/generated/v2_normal_support_preflight/` do not exist yet.

## 5. Execution

| Step | Command | Expected result | Stop if |
| --- | --- | --- | --- |
| 1 | `python tools/simulation/v2_normal_authorization.py` | `ACTIVE`, exit 0 | not ACTIVE |
| 2 Preflight (MATLAB, no simulation) | see block A | `PREFLIGHT_REPORT.json` with `n_ok: 27`, `n_failed: 0`; no signal files | any `*_FAILED.json`, or n_ok < 27 |
| 3 Generate (MATLAB) | see block B | 27 × `<run>_clean_solver_grid.csv` + `<run>_provenance.json` in `development/` (18) and `confirmation/` (9); last time ≥ 19,999 s; the function returns without error and asserts the released models unchanged | an error or any `*_FAILED.json` |
| 4 Post-process | `python tools/simulation/postprocess_v2_normal_runs.py data/generated/v2_normal_support` | per run `<run>_clean.csv` and `<run>_noise_added.csv`: 20,000 rows; columns `Timestamp, PS1…PS10, MFS1…MFS3` (center, up) or `Timestamp, PS1…PS12, MFS1…MFS4` (down); provenance updated | non-zero exit |
| 5 Validate and seal | `python tools/simulation/validate_v2_normal_outputs.py data/generated/v2_normal_support` | prints `ACCEPTED_AND_SEALED: 0 problem(s)`; writes `VALIDATION_REPORT.json` (development values; confirmation PASS/FAIL only), `CONFIRMATION_PARTITION.sha256` (36 lines = 9 runs × 4 files, plus `# aggregate …`), `DEVELOPMENT_MANIFEST.csv` (18 rows) | `REJECTED_NOT_SEALED` |
| 6 Record | copy `PREFLIGHT_REPORT.json`, `VALIDATION_REPORT.json`, `CONFIRMATION_PARTITION.sha256`, `DEVELOPMENT_MANIFEST.csv` and the 27 `*_provenance.json` into `06_audit_preparation/simulation/v2_normal_support/results/`; record the executor's name and date in `AUTHORIZATION_HISTORY.csv` (status `EXECUTED`); commit those files only | signal files never enter git (`data/generated/` is ignored) | — |

**Block A (MATLAB, repository root):**

```matlab
addpath('06_audit_preparation/simulation/v2_normal_support')
rel = 'data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets';
des = '06_audit_preparation/simulation/v2_normal_support/DESIGN.csv';
generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support_preflight', 'preflight')
```

**Block B:**

```matlab
generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support', 'run')
```

## 6. Confirmation partition rules

- The confirmation runs are V2N_A0B0C0, V2N_A1B1C2 and V2N_A2B2C1, each in three models. Their files are written to `confirmation/` and read by software only:
  - for resampling and noise (generation);
  - for the PASS/FAIL checks P1–P5.
- No value, summary, plot, window, feature or prediction from them may be produced, printed or viewed. This rules out model selection, threshold choice, exploratory analysis and visual checks.
- After sealing, opening them requires a frozen protocol, a new scoped authorization, and verification of `CONFIRMATION_PARTITION.sha256`.
- A seal from a partial or rejected set is never produced: the validator writes nothing to seal unless all checks pass.

## 7. Failure procedure

1. **Stop at the first failure.** Do not re-run, post-process, validate or seal a partial set.
2. **Preflight failure** (licence, release, missing block, parameter not settable):
   - nothing has been simulated;
   - fix the environment. Repeat the preflight **only if** the project lead has confirmed that preflight does not consume the authorization; otherwise a new authorization record is needed (`FINAL_PRE_EXECUTION_CHECK.md` §1);
   - if the fix needs a change to any bound file (design, generator, post-processing, validator or authorization check), go to step 5.
3. **Run, post-process or validation failure:**
   - rename the whole output folder to `data/generated/_quarantine_<UTC timestamp>/` and do not open anything in its `confirmation/` subfolder;
   - report the `*_FAILED.json` files and the validator's problem list. The validator gives development values but only check names for confirmation runs.
   - quarantined outputs are never used, and the same seeds regenerate identical noise.
4. **A physical check (P2–P5) failing on any run** means that operating point is not a valid stable NORMAL state for that model. The **design** must then be revised (and with it the partition) before any new attempt. Thresholds are never loosened after seeing a failure.
5. **Any change to a bound file voids the authorization automatically**, because the hashes no longer match and the tools refuse to run.
   - Record the void record in `AUTHORIZATION_HISTORY.csv`.
   - Write a new request (`AUTH_SIMULATION_GENERATION_V3_REQUEST.yaml`, …) bound to the new hashes.
   - Obtain a new project-lead authorization.
6. **Each authorization covers one execution attempt.** A repeat attempt, even with unchanged files, needs a new record.

## 8. Observations for the dataset owner (not acted on)

- The Gas Properties block uses **air** (R = 0.287 kJ/kg/K), not hydrogen.
- The released noise is 0.0005 MPa (pressure) and 0.25 kg/s (flow). The README states "1–2% of range".
- The release grid is 1 s while the solver step is 0.8 or 0.9 s. The authors' resampling method is undocumented; this package uses linear interpolation, recorded in the provenance.
- Released center and up NORMAL files contain padded channels (PS11, PS12, MFS4). Generated files contain each model's own sensors only.

## 9. What remains before independent FAULT, DELAY and LEAK scenarios can be generated

| Class | Supported now | Missing (owner) |
| --- | --- | --- |
| LEAK at G3 | variable restriction SID 213 driven by `PS Step1` in `Anomalous_HNetwork_gest_*.slx` (onset time, area) | weak/medium/strong areas defined by prespecified clean-signal detectability; matched no-event baseline per run (Yazan) |
| LEAK at G4, G5, G6 | restrictions exist (SIDs 222, 312, 215) but are **fixed** in the saved models | how the released G4–G6 leaks were imposed (block edits, parameters, timings); converting them to variable restrictions changes the models and needs the authors' specification (Yazan / authors) |
| Weak-leak definition | — | whether the released weak G4/G5 runs (which settle onto the NORMAL operating point) are intended physics (root-cause report §3) |
| COMPRESSOR_FAULT ("BROKENC1") | — | the fault mechanism: which block (Pressure Source 1 or 3?), which parameter, what severities. Not recoverable from the saved models. |
| COMPRESSOR_DELAY ("STARTDELAYC1") | — | the delay mechanism and its parameter (start time of which source) |
| All event classes | position map, generator pattern, post-processing, validator and sealing of this package | an anomalous-model generator with block-identity export; event-specific physical checks; ≥ 3 independent groups per class for development and ≥ 2 for confirmation (`02_methodology/DISTINGUISHABILITY_V2.md` §6); a separate scoped authorization per class |
