# Phase 6 source reproduction and validation gate

The isolated R2026b attempt used a checksum-verified Center NORMAL SLX copy and writable preferences. MATLAB exited with code 1 and error 5202 before model load, Simulink/Simscape checkout, or export. The recorded solver settings are planned settings derived from the archive launcher. Runtime settings, initialization, and boundary trajectories remain absent. No system or licensing changes were made. A licensed operator should open MATLAB normally and verify Simulink and Simscape checkout before repeating the probe once. Persistent 5202 requires the administrator or MathWorks Service Host support path. [MathWorks 5202 guidance](https://www.mathworks.com/matlabcentral/answers/1815390-why-do-i-receive-error-5202-unable-to-access-services-required-to-run-matlab)

## What was reconciled

The only paired data in this run are the original archived Center solver CSV and the clean release Parquet. The two solver CSV paths have identical hashes and represent one archived observation sequence. All residuals are release minus solver at exactly equal stored decimal timestamps. The figure and residual artifact omit interpolation. Pressure units trace to the source converter. The release documents kg/s for MFS, but the solver converters inherit units and runtime resolution remains open.

The authors describe 1 s linear interpolation and a variable-step simulation with relative tolerance 1e-3. The archived Center launcher specifies fixed-step ode14x at 0.8 s. At shared knots, interpolation of the archived CSV would leave the CSV values unchanged. The observed residuals at those knots disprove that interpolation of this CSV alone gives the released Center values. Other differences in run configuration or processing remain hypotheses. The publication's blend claim does not identify the effective Center gas configuration. [Author methods](https://www.mdpi.com/2227-9717/14/16/2636) · [Author repository](https://github.com/andysinx/H2-SimNet) · [Pinned release](https://zenodo.org/records/17871393)

The static gas-net graph maps MFS1 and MFS3 to reservoir-connected branches and MFS2 to the chamber-connected branch. Recorded sign counts are in the report. The sign convention relative to a complete control volume remains unresolved. The pressure-source blocks are internal transfers. Neither the clocks nor the signals close the signed external flow and storage balance. Rounded residuals and a published solver tolerance do not supply deterministic instrument, clock, boundary, parameter, gas-property, discrepancy, or numerical bounds.

No matched LEAK case was admitted. Required evidence includes a reproduced NORMAL, a comparable independently traceable run with a verified leak block and location, a mechanism and magnitude, an onset, signed histories, and matched operating conditions. The archive eligibility screen carries forward zero confirmatory families. The historical joint set-membership comparator and its equivalence finding were preserved.

## Independent route

Ibrahim et al. is the closest documented experimental alternative. The primary paper reports inline pressure and flow with two controlled locations, and offers raw data on request. Confirm data rights, calibration, clock alignment, run identities, and event records before qualification. The air/water multiphase archive offers a potential process-measurement check after model adaptation. The PE pressure-decay archive offers a narrower component check. Their repository metadata were inspected; raw measurements and dataset reuse terms were not verified here. [Ibrahim et al.](https://doi.org/10.1016/j.jlp.2024.105452) · [Multiphase archive](https://zenodo.org/records/16978349) · [PE pressure-decay archive](https://zenodo.org/records/20582921)

## Reproduce the recorded blocked run

From the repository root, set `$env:PYTHONPATH='src'`. Use fresh output paths. The report stores the console hash and sanitized failure. It does not publish the raw diagnostic console.

```powershell
.venv/Scripts/python.exe -m h2prism.phase6 --probe-log <isolated-console.txt> --exit-code 1 --output phase6.json --residuals aligned-residuals.json --figure phase6.png
.venv/Scripts/python.exe -m pytest -q tests/test_phase6.py tests/test_phase5.py tests/test_phase4.py tests/test_network_reference.py tests/test_physical_reference.py tests/test_certified_evidence.py tests/test_data_contracts.py tests/test_gas_physics.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```

The reporting command requires evidence of the recorded 5202 failure. A successful future source run requires a new runtime record, a raw export, and reconciliation with verified units and effective configuration before any source or physical validation finding.
