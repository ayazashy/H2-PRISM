# Execution-readiness check: V2 NORMAL-support package v2

- **Checked:** 2026-11-13T12:48:45Z.
- **Repository:** `audit/preparation-integration`; authorization committed in `960a7b7`; line-ending pin committed in `484f58c`.
- **Integrity:** the authorization record was not changed or revoked.

## Result per condition

| # | Condition | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Authorization valid now and not consumed | **MET** | `python tools/simulation/v2_normal_authorization.py` → `ACTIVE: Ahmed Zayed (project lead) 2026-11-13`. The record has no expiry clause; it lapses on any bound-file change or after one execution attempt. History status is `ACTIVE_NOT_YET_EXECUTED`. No `data/generated/`, no `results/`, no preflight report exist. |
| 2 | Hash-bound files unchanged | **MET in this checkout; the defect affecting other checkouts was corrected** | All 5 bound hashes match the working files. Design pin `c59caa77…` matches. All six released models match `MODEL_FILES.csv`. |
| 3 | Gas properties disclosed; no hydrogen-specific claim | **MET (disclosed below)** | Gas Properties (G) block, identical in all six released models |
| 4 | Package is exploratory NORMAL-support generation from the released models only | **MET** | Scope and `not_covered` of the authorization record. Purpose statement added to `EXECUTION_CHECKLIST.md` §0. |
| 5 | MATLAB preflight executable in R2025a or later | **NOT VERIFIABLE HERE → blocker for execution in this environment** | No MATLAB installation and no MATLAB Engine for Python on this machine. Must be verified on the executor's machine (step A below). The generator itself refuses releases older than R2025a and missing Simulink/Simscape licences. |
| 6 | Confirmation partition sealed; training, evaluation and activation restrictions preserved | **MET** | No confirmation data exist. The validator records confirmation runs as PASS/FAIL only and seals only on full acceptance. The authorization's `not_covered` excludes training, evaluation, any inspection of the confirmation partition, RC1 and protocol activation. |

### Condition 2: what was wrong and what was corrected

- **The problem:** two bound files (`postprocess_v2_normal_runs.py`, `validate_v2_normal_outputs.py`) were bound as their Windows CRLF bytes, and two (`generate_v2_normal_support.m`, `v2_normal_authorization.py`) as LF. Git stores all four as LF.
- **The consequence:** a fresh checkout elsewhere (Linux/macOS, or Windows with `core.autocrlf=true` for the LF files) would have produced different bytes. That would void the authorization, and the fail-closed tools would correctly refuse to run.
- **The minimum correction (`484f58c`):** `.gitattributes` pins each of the four files to its bound line endings. **No bound file's content changed.**
- **Proof:** fresh clones with `core.autocrlf` = true, false and input all reproduce every bound hash, and the authorization check reports `ACTIVE` inside them.

### Condition 3: gas represented by the released models (all six identical)

| Parameter | Value in the models | Air | Hydrogen |
| --- | --- | --- | --- |
| Specific gas constant R | **0.287 kJ/kg/K** | 0.287 | 4.124 |
| Compressibility Z | 0.998386 | ≈ 1 | ≈ 1.0006 at 0.1 MPa |
| cp (reference) | 0.3469 kJ/kg/K | 1.005 | 14.3 |
| Viscosity (reference) | 10.98 µPa·s | 18.2 | 8.8 |
| Thermal conductivity (reference) | 48.2 mW/m/K | 25.9 | 180 |
| Property tables | consistent with air (e.g. ρ = p/(R T) with R = 0.287 at 150 K) | — | — |
| Specification switch `gas_spec` | stored value `1` (the active specification must be read in MATLAB, step A) | — | — |
| Validity limits | 0.001–10 MPa, 150–2,000 K; out-of-range = **error** | — | — |

**Reading:**

- The released models do **not** represent hydrogen. The gas constant and the property tables are air's.
- The constant reference values match neither gas. If the perfect-gas (constant-property) specification is the active one, they imply cp/(cp − R) ≈ 5.8, which is physically impossible.
- **Generated results must not be described as hydrogen-specific.** The correct wording is: "simulated with the released H2-SimNet network models, whose gas definition is air-like (R = 0.287 kJ/kg/K); hydrogen behaviour is not verified."
- This applies equally to the released dataset and to every existing result in this repository.
- It is reported to the dataset owner, not changed.

## Minimum actions before execution

1. **Executor environment (condition 5).** Yazan, or his designee, runs step A on the execution machine. If it fails, stop: no simulation, nothing to quarantine. The correction is an R2025a-or-later installation with Simulink and Simscape licences.
2. **Executor acceptance.** Yazan records his acceptance of execution, with name and date, in `AUTHORIZATION_HISTORY.csv` when he starts. It is currently NOT_RECORDED, and nothing in this repository records it on his behalf.

## Exact execution instructions for Yazan

Run everything from the repository root of a fresh clone of this branch at or after `484f58c`. Do not edit any file in `06_audit_preparation/simulation/v2_normal_support/` or `tools/simulation/` before or during execution: any edit voids the authorization.

**Step 0 (shell):** confirm the authorization and the release.

```bash
python tools/simulation/v2_normal_authorization.py
sha256sum data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets/Normal_HNetwork_gest_*.slx
```

Expected:
- `ACTIVE: Ahmed Zayed (project lead) 2026-11-13`;
- model hashes center `710711f4…`, down `2fcf47df…`, up `5c3c76e9…` (full values in `EXECUTION_CHECKLIST.md` §1).

**Step A (MATLAB):** check the environment and record the active gas specification. This step is read-only: it uses a temporary copy and never saves.

```matlab
assert(~isMATLABReleaseOlderThan('R2025a')); assert(license('test','Simulink') && license('test','Simscape'));
v = ver; disp({v.Name; v.Version}')
rel = 'data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets';
tmp = tempname; mkdir(tmp); copyfile(fullfile(rel,'Normal_HNetwork_gest_center.slx'), tmp);
load_system(fullfile(tmp,'Normal_HNetwork_gest_center.slx'));
g = Simulink.ID.getHandle('Normal_HNetwork_gest_center:4');
disp(get_param(g,'gas_spec')); disp(get_param(g,'R'));
close_system('Normal_HNetwork_gest_center', 0);
```

Record the printed products and `gas_spec` in the execution note (step 5).

**Steps 1–5:** exactly as `EXECUTION_CHECKLIST.md` §5, in this order. Stop at the first failure and follow §7.

1. **MATLAB preflight:**

   ```matlab
   generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support_preflight', 'preflight')
   ```

   Expect `n_ok: 27`, `n_failed: 0`.
2. **MATLAB run:**

   ```matlab
   generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support', 'run')
   ```

   Here `des = '06_audit_preparation/simulation/v2_normal_support/DESIGN.csv'` and the package folder is on the MATLAB path:

   ```matlab
   addpath('06_audit_preparation/simulation/v2_normal_support')
   ```

3. Post-process:

   ```bash
   python tools/simulation/postprocess_v2_normal_runs.py data/generated/v2_normal_support
   ```

4. Validate and seal:

   ```bash
   python tools/simulation/validate_v2_normal_outputs.py data/generated/v2_normal_support
   ```

   Expected output: `ACCEPTED_AND_SEALED: 0 problem(s)`.
5. **Record.**
   - Copy the reports, the seal, the development manifest and the 27 provenance files to `06_audit_preparation/simulation/v2_normal_support/results/`.
   - Add an execution note with the executor, the date, the MATLAB products and the `gas_spec` from step A.
   - Set the v2 row of `AUTHORIZATION_HISTORY.csv` to `EXECUTED` (or `EXECUTION_FAILED`).
   - Commit locally.

**After a success or a failure, this authorization is consumed.** It covers one attempt; any further run needs a new record.

## Restrictions that remain in force

- No training.
- No evaluation of Distinguishability v2 or any other method.
- No change to RC1.
- No protocol activation.
- No event-class generation.
- No summary, statistic, plot or inspection of the confirmation partition.
- No hydrogen-specific claim.
