# V2 NORMAL-support simulation package (authorized 2026-11-13; not yet executed)

- **Scope:** `SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION`.
- **Authorization record:** `AUTH_SIMULATION_GENERATION.yaml` (project lead). It is void if any bound file changes.
- **Purpose:** hypothesis H-R1 in `02_methodology/DISTINGUISHABILITY_V2.md`. NORMAL needs at least 4 independent development groups and 3 confirmation groups before v2's separability and detectability can be defined.

| Item | Content |
| --- | --- |
| `DESIGN.csv` (hash in `DESIGN.sha256`) | 9 operating points × 3 models = 27 runs |
| Factors | supply set-point 6.1 / 6.4 / 6.7 MPa; ramp 0 / −1e-5 / −2e-5 MPa/s; withdrawal area (G3–G6) 0.75 / 1.0 / 1.25 × 1e-3 m² |
| Design | 3³⁻¹ fraction that excludes the released NORMAL point |
| Development | 6 points (each level twice) |
| Confirmation | 3 points (each level once), fixed by level codes before any run |
| Groups | each point is one new independence group; noise seeds are not groups |

**Run (MATLAB R2023b or later with Simscape; the released models were saved with library version 25.1):**

1. From the repository root, run in MATLAB:

   ```matlab
   addpath('06_audit_preparation/simulation/v2_normal_support')
   generate_v2_normal_support( ...
       'data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets', ...
       '06_audit_preparation/simulation/v2_normal_support/DESIGN.csv', ...
       'data/generated/v2_normal_support')
   ```

   The generator works on copies, never saves a model, and asserts afterwards that the released files are byte-identical.

2. Add measurement noise:

   ```bash
   python tools/simulation/add_measurement_noise.py data/generated/v2_normal_support
   ```

3. Validate and seal the confirmation partition:

   ```bash
   python tools/simulation/validate_v2_normal_outputs.py data/generated/v2_normal_support
   ```

   This checks every provenance field and hash. It reads development signals but only hashes the confirmation files, then writes `CONFIRMATION_PARTITION.sha256`.

4. Copy into this folder and commit: `VALIDATION_REPORT.json`, `CONFIRMATION_PARTITION.sha256`, `DEVELOPMENT_MANIFEST.csv`, and the 27 `*_provenance.json` files. The signal files stay out of git.

**Do not** train, evaluate or plot anything from the confirmation folder. Its use requires a frozen protocol and a separate authorization.
