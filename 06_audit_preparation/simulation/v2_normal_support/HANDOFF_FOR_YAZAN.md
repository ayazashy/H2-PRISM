# Handoff: one authorized execution of the V2 NORMAL package (package v3)

**Status (2026-11-13): NOT READY TO EXECUTE.**

- Package v3 implements the project lead's attempt policy (`POLICY_CLARIFICATION_2026-11-13.yaml`). That implementation changed hash-bound files, which voided the v2 authorization (never executed).
- The **v3 request is not yet authorized** (`AUTH_SIMULATION_GENERATION_V3_REQUEST.yaml`).
- Read `05_documentation/GAS_MODEL_LIMITATION.md` first. The released models do not represent hydrogen, and their active gas constants are physically inconsistent.
- The tag `v2-normal-handoff-1` points to the superseded v2 package. **Do not use it.** A new tag will be named once v3 is authorized.

**For:** Yazan (dataset owner) or a person he designates. **Your acceptance is not recorded;** record it yourself in step 5.

**What it is:** 27 exploratory NORMAL simulations (9 operating points × 3 released models), with the released, air-like, physically inconsistent gas definition. **Not hydrogen-specific. Not a validation. No training, no evaluation.**

## Attempt policy, enforced by `tools/simulation/v2_normal_authorization.py`

- **Preflight and read-only checks do not consume the authorization** and may be repeated.
- **The attempt begins when `generate_v2_normal_support(..., 'run')` starts.** The generator atomically creates `06_audit_preparation/simulation/v2_normal_support/claims/v3__<record>.claim.json` before any simulation.
- **A claim consumes the authorization permanently**, on success, failure or interruption. A second `'run'`, also into another folder or from a concurrent process, is refused.
- Post-processing and validation accept only the claimed folder and only provenance carrying the claim's attempt ID.

## Requirements

- MATLAB **R2025a or later** with **Simulink** and **Simscape**.
- Python 3.12 (`pandas`, `numpy`, `pyyaml`), reachable as `python` or through the environment variable `H2PRISM_PYTHON`.
- About 1 GB free disk space.
- `data/generated/` must not exist.
- Run everything **from the repository root**.

## Steps (stop at the first failure)

**0 (shell).** Check the gate and the release:

```bash
python tools/simulation/v2_normal_authorization.py check
sha256sum data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets/Normal_HNetwork_gest_*.slx
```

Expected:
- `ACTIVE_UNCLAIMED: <grantor> <date>`;
- center `710711f4…`, down `2fcf47df…`, up `5c3c76e9…`.

**A (MATLAB, read-only).** Check the environment and the gas specification (unchanged from the v2 handoff):

```matlab
assert(~isMATLABReleaseOlderThan('R2025a')); assert(license('test','Simulink') && license('test','Simscape'));
v = ver; disp({v.Name; v.Version}')
rel = 'data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets';
des = '06_audit_preparation/simulation/v2_normal_support/DESIGN.csv';
tmp = tempname; mkdir(tmp); copyfile(fullfile(rel,'Normal_HNetwork_gest_center.slx'), tmp);
load_system(fullfile(tmp,'Normal_HNetwork_gest_center.slx'));
g = Simulink.ID.getHandle('Normal_HNetwork_gest_center:4');
spec = foundation.enum.gas_spec(str2double(get_param(g,'gas_spec')))   % expected: perfect
close_system('Normal_HNetwork_gest_center', 0);
addpath('06_audit_preparation/simulation/v2_normal_support')
```

**1 (MATLAB).** Preflight (non-consuming, repeatable):

```matlab
generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support_preflight', 'preflight')
```

Expected: `PREFLIGHT_REPORT.json` with `n_ok: 27`, `n_failed: 0`. No claim is created.

**2 (MATLAB).** The single attempt (claims, then simulates):

```matlab
generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support', 'run')
```

Expected:
- `claims/v3__AUTH_SIMULATION_GENERATION_V3_REQUEST.claim.json` exists;
- 27 solver-grid CSV files plus 27 provenance files, each carrying the claim's `attempt_id`;
- no error.

**3 (shell).** Post-process:

```bash
python tools/simulation/postprocess_v2_normal_runs.py data/generated/v2_normal_support
```

Expected: exit 0; 20,000-row `_clean.csv` and `_noise_added.csv` per run.

**4 (shell).** Validate and seal:

```bash
python tools/simulation/validate_v2_normal_outputs.py data/generated/v2_normal_support
```

Expected output: `ACCEPTED_AND_SEALED: 0 problem(s)`, plus the seal (36 lines plus the aggregate) and an 18-row development manifest.

**5 (record).**

1. Copy the reports, the seal, the manifest and the 27 provenance files into `results/`.
2. Write `results/EXECUTION_NOTE.md` containing:
   - your name and acceptance;
   - the time;
   - the MATLAB products;
   - `spec`;
   - the mandatory sentence from `GAS_MODEL_LIMITATION.md`, verbatim.
3. Set the v3 history row to `EXECUTED`.
4. **Commit the claim file together with the results.**

## Stop conditions

- Step 0 is not `ACTIVE_UNCLAIMED`, or a model hash differs.
- Step A fails, or `spec` is not `perfect`.
- The preflight has failures.
- The run is refused or raises an error, or any `*_FAILED.json` appears.
- Post-processing exits non-zero.
- The validator prints `REJECTED_NOT_SEALED`.

**After a stop that happened after step 2 started:**

1. The attempt is consumed (the claim stays).
2. Rename the output to `data/generated/_quarantine_<UTC>/` and do not open `confirmation/`.
3. Report the failure, and set the history row to `EXECUTION_FAILED`.
4. Commit the claim.

Any further simulation needs a new authorization record.

## Never

- Open, summarise or plot the confirmation partition.
- Train or evaluate.
- Modify RC1 or activate Protocol 2.0.
- Generate event scenarios.
- Describe results as hydrogen-specific or physically validated.
- Delete or edit a claim file.
