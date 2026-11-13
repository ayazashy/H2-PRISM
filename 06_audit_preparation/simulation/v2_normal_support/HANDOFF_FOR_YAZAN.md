# Handoff: one authorized execution of the V2 NORMAL package v2

**For:** Yazan (dataset owner) or a person he designates.

**Authorization:**

- `SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION`, package v2.
- Project lead, 2026-11-13; covers one attempt.
- **Your acceptance is not recorded.** Record it yourself in step 5.

**What it is:** 27 exploratory NORMAL simulations (9 operating points × 3 released models) with the released models and their released gas definition. That definition is air-like (R = 0.287 kJ/kg/K) with physically inconsistent constants (γ ≈ 5.75). **Not hydrogen-specific. Not a validation. No training, no evaluation.** Details: `FINAL_PRE_EXECUTION_CHECK.md`.

## Checkout

```bash
git checkout v2-normal-handoff-1
```

The tag is local to the project lead's repository; it points at the commit that adds this file, on top of `484f58c`. Do not edit any file under `06_audit_preparation/simulation/v2_normal_support/` or `tools/simulation/` (except recording results in step 5): any change voids the authorization.

## Requirements

- MATLAB **R2025a or later** (the models were saved in R2025a, 25.1.0.2943329), with **Simulink** and **Simscape**.
- Python 3.12 with `pandas`, `numpy`, `pyyaml`.
- About 1 GB of free disk space.
- `data/generated/` must not exist.

## Steps (stop at the first failure; see "Stop conditions")

**0 (shell).** Check the gate and the release:

```bash
python tools/simulation/v2_normal_authorization.py
sha256sum data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets/Normal_HNetwork_gest_*.slx
```

Expected:
- `ACTIVE: Ahmed Zayed (project lead) 2026-11-13`;
- center `710711f41e33adb9…`, down `2fcf47dfe91adf54…`, up `5c3c76e9866dcbbe…` (full values in `EXECUTION_CHECKLIST.md` §1).

**A (MATLAB, repository root, read-only).** Check the environment and the active gas specification:

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

Write down the products and `spec`.

**1 (MATLAB).** Preflight: no simulation, no signals.

```matlab
generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support_preflight', 'preflight')
```

Expected: `data/generated/v2_normal_support_preflight/PREFLIGHT_REPORT.json` with `"n_ok": 27`, `"n_failed": 0`, and no `*_FAILED.json`.

**2 (MATLAB).** The authorized run:

```matlab
generate_v2_normal_support(rel, des, 'data/generated/v2_normal_support', 'run')
```

Expected: returns without error. Then:
- `development/` holds 18 × `<run>_clean_solver_grid.csv` and 18 × `<run>_provenance.json`;
- `confirmation/` holds 9 + 9 of the same.

**3 (shell).** Post-process:

```bash
python tools/simulation/postprocess_v2_normal_runs.py data/generated/v2_normal_support
```

Expected: exit 0. Each run gets `<run>_clean.csv` and `<run>_noise_added.csv`, with 20,000 rows, t = 0…19,999 s.

**4 (shell).** Validate and seal:

```bash
python tools/simulation/validate_v2_normal_outputs.py data/generated/v2_normal_support
```

Expected: prints `ACCEPTED_AND_SEALED: 0 problem(s)` and writes:
- `VALIDATION_REPORT.json`;
- `CONFIRMATION_PARTITION.sha256` (36 hash lines plus `# aggregate …`);
- `DEVELOPMENT_MANIFEST.csv` (18 rows).

**5 (record).**

1. Copy `PREFLIGHT_REPORT.json`, `VALIDATION_REPORT.json`, `CONFIRMATION_PARTITION.sha256`, `DEVELOPMENT_MANIFEST.csv` and the 27 `*_provenance.json` into `06_audit_preparation/simulation/v2_normal_support/results/`.
2. Add `results/EXECUTION_NOTE.md` containing:
   - your name and acceptance;
   - the date and time;
   - the MATLAB products;
   - `spec`;
   - this sentence, verbatim: *"Exploratory NORMAL-support simulations of the released H2-SimNet network models, using the released gas definition (air-like R = 0.287 kJ/kg/K; perfect-gas constants that are physically inconsistent, γ ≈ 5.75). Not hydrogen-specific, not a physical validation, and not an evaluation of any method."*
3. Set the v2 row of `AUTHORIZATION_HISTORY.csv` to `EXECUTED`.
4. Commit locally. Signal files stay in the git-ignored `data/generated/`.

## Stop conditions (any one: stop; do not continue, retry, post-process or seal)

- Step 0 is not `ACTIVE`, or a model hash differs.
- Step A fails (release, licence), or `spec` is not `perfect`. In the second case, report it: the disclosure must be revised before use.
- Preflight: `n_failed > 0` or any `*_FAILED.json`.
- The run raises an error, or any `*_FAILED.json`, or "released model changed".
- Post-processing exits non-zero.
- The validator prints `REJECTED_NOT_SEALED`.

**After a stop:**

1. Rename `data/generated/v2_normal_support*` to `data/generated/_quarantine_<UTC>/`.
2. Do **not** open anything under `confirmation/`.
3. Report the `*_FAILED.json` files and the validator's problem list.
4. Set the history row to `EXECUTION_FAILED`.

**This attempt is then consumed.** By the conservative rule in force, that includes a failed preflight unless the project lead has confirmed in writing that preflight does not consume. Any retry needs a new authorization record.

## Never

- Open, summarise or plot the confirmation partition.
- Train or evaluate anything.
- Modify RC1 or activate Protocol 2.0.
- Generate event scenarios.
- Describe the results as hydrogen-specific.
