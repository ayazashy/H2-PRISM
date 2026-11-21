# Center command-timing development pilot

The source trace resolves SID 59, PS Step, to SID 55, controlled Pressure Source (G), through its physical-signal pressure input P. Native command is 3.0 to 6.4 MPa at 25 s. Compare nominal command issuance with a one-second shift to 26 s. This is five fixed solver steps at 0.2 s, a development test point for observable timing, with unchanged pressure plateaus. It supplies no legitimate range for actual compressor timing or physical actuator lag. Emitted command and received pressure command are logged separately, with signed A/B flows and A/B pressure. Record sensor response on the same grid. It can include fluid transport delay; that delay is distinct from command issuance.

Both twins retain the same 0.001 m2 outlet command, zero pressure overlay, native reservoir histories, initialization policy and solver. Only SID 59 step_time may differ in the saved pair. The existing runner names its intervention folder outlet_opening; there is no opening in this experiment. Source SLX copies in both folders match the pinned Center hash. The one-second interval at the nominal step is the only expected mismatch in the commanded pressure trajectory relative to the old source. MATLAB preflight checks link identity, pressure plateaus, physical peers, logging writer uniqueness and solver. Python approval rejects any other saved model delta. Acceptance requires a complete 20,000 s trajectory, 13 finite sensors, recorded command and receipt timing, signed boundary histories, storage and numerical conservation accounting. No trajectory was executed for this pilot.

Fault remains blocked. The available controlled pressure source changes imposed differential but lacks a qualified compressor degradation or malfunction model with an independently observable device state and justified failure envelope. Recorded fault annotations cannot map released cases to verified actuator parameters and runtime truth. The delayed command is a controlled timing perturbation. Actuator-response DELAY labels remain blocked without paired commanded and actual actuation, qualified synchronization and baseline-lag evidence.

NORMAL and the three controlled atmospheric outlet mechanisms already have accepted development captures and were not rerun. The new timing pair has one development root ID, native initialization and no imported checkpoint. A root ID and a new execution directory do not attest independent generating histories. Use the existing structural admission validator for future independent NORMAL, LEAK, FAULT, DELAY and location coverage; disjoint development, calibration and untouched test roots remain absent. Reuse fixed-clock causal observation features, group-held-out development and training-only transformations. No confirmatory multiclass training or new metrics are justified. Statistical confidence cannot substitute for qualified physical bounds. Formal status remains INDETERMINATE / UNRESOLVED / L0.

## Interactive MATLAB compile-only preflight

```matlab
addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
pilot = 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase13_command_delay_01';
h2prism_center_outlet_case('preflight',fullfile(pilot,'normal'));
h2prism_center_outlet_case('preflight',fullfile(pilot,'outlet_opening'));
```

Once both compile receipts exist, the following command checks approval against the exact saved delta, runs the control, validates it, then runs the intervention. Start in a clean interactive session and preserve any failed directory. The runner refuses an existing approval or execution evidence. No standalone MATLAB startup is used.

```matlab
h2prism_run_command_delay(pilot,'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase11_cases/step_0.2');
```

To reproduce isolated preparation from PowerShell in the repository, set PYTHONPATH to src and run:

```powershell
.\.venv\Scripts\python.exe -m h2prism.phase13_command_delay prepare '<new-pilot-directory>'
```
