# Center NORMAL source reproduction

The isolated Center NORMAL capture reached the configured 20,000 s stop time in MATLAB R2026b Update 1. Its saved simulation metadata records fixed-step `ode14x` at 0.8 s, normal simulation mode, no simulation error, and zero recorded warnings. The setup records the original SLX solver as VariableStepAuto, the archived launcher configuration applied at capture, and initial-state and external-input loading disabled. The audit read the saved SimulationOutput without simulating or reopening the source model.

## Comparisons

The 13 raw exports contain 25,001 samples each over 0?20,000 s. All clocks are strictly increasing, and every timestamp and value round-trips exactly to the saved MAT arrays. No missing, NaN, infinite, or nonpositive absolute-pressure samples were found. The Simscape log validates the pressure conversion from Pa to MPa and the signed flow scale in kg/s.

The archive comparison uses 6,925 exact decimal pairs and 16,634 equal binary64 pairs. Separately, all 25,001 archived solver ticks pair with capture ticks after verifying the 0.8 s grid within binary64 roundoff. Their largest time difference is 3.638 ? 10??? s. This yields maximum errors of 2.380 ? 10?? MPa for pressure and 2.532 ? 10?? kg/s for mass flow. There is no evidence of a clock offset on this grid. The clean CSV and Parquet agree exactly for all 13 mapped channels and 20,000 release times. They share 5,000 exact timestamps with the capture, ending at 19,996 s.

| At 28 s | Capture | Archived solver | Both clean releases | Release minus archive |
|---|---:|---:|---:|---:|
| PS1 (MPa) | 4.089159670115 | 4.089159653589 | 4.178862610056 | +0.089702956467 |
| MFS3 (kg/s) | 5.039656353399 | 5.039656165937 | 5.092684381600 | +0.053028215663 |

Linear interpolation of the archived CSV would retain values at the shared knots. An exploratory fit to the shared knots from 24 to 160 s evaluates the capture at approximately t + 0.601 s for PS1 and t + 0.597 s for MFS3. The fitted leads change in later windows and do not establish a clock correction. The exact clean-release generation chain remains unverified.

## Physical evidence and decision

The controlled reservoir follows 7.4 to 2.94 bar and 288 K. Five atmospheric reservoirs log 0.100 MPa and 293.15 K for their internal settings. The stored 0.101325 MPa specified-pressure fields are inactive. The pressure-source step and ramp are pressure differences. The step is configured for 3 to 6.4 MPa at 25 s, with the new plateau first logged at 25.6 s. The ramp starts at 10 s from ?0.3 MPa at ?10?? MPa/s and ends at ?0.4999 MPa. All 245 saved state entries include a time-zero sample. As one example, the chamber logs a different time-zero pressure and temperature from its stored targets. Per-component runtime ranges and initial values are in the report.

All six external signed reservoir flows and storage densities in seven compressible pipes and one one-port chamber are available. The pointwise signed boundary sum agrees with the sum of storage-component port rates within 2.28 ? 10??? kg/s. Storage increases by 8,421.39 kg, while trapezoidal integration of the boundary net flow gives 8,877.35 kg. The final residual is ?455.95 kg, or 0.0108% of gross boundary throughput and 5.41% of the observed storage gain. This is partial numerical balance evidence. Temporal quadrature and solver contributions have not been separated. [MathWorks Pipe (G)](https://www.mathworks.com/help/simscape/ref/pipeg.html), [MathWorks Constant Volume Chamber (G)](https://www.mathworks.com/help/simscape/ref/constantvolumechamberg.html), [MathWorks Flow Rate Sensor (G)](https://www.mathworks.com/help/simscape/ref/flowratesensorg.html)

Logged storage states satisfy the configured constant-property equation with `R = 0.287 kJ/(kg?K)` and `Z = 0.998386`. Logged local gas temperatures reach 3,744 K. These are properties of the modeled run. Gas composition and physical calibration remain unverified. [MathWorks Gas Properties (G)](https://www.mathworks.com/help/simscape/ref/gaspropertiesg.html)

The run is eligible as an archived-solver NORMAL reference. It is ineligible as a release-matched NORMAL/LEAK baseline, a physically certified diagnosis, or independent confirmation. The next source experiment holds the model, gas settings, commands and initialization policy fixed, and repeats NORMAL at 0.4 s and 0.2 s with ode14x on isolated copies. Compare mass-balance residuals and sensor values at the original 0.8 s knots, inspect the interval around the 25 s step separately, and record cumulative signed boundary mass and total storage over 0?20,000 s. In parallel, qualify the pinned archived anomalous Center candidate by tracing the leak mechanism, location, onset and magnitude and comparing unrelated boundary histories and initialization. A paired LEAK run requires both results.

## Reproduce the audit

In interactive MATLAB with the documented existing capture directory stored in `runDir`, extract plain arrays from the saved model output into a fresh MAT file. This operation reads the raw capture and verifies its hash.

```matlab
addpath('tools/simulation');
h2prism_center_extract_capture(runDir, fullfile(fileparts(runDir), 'center_audit_extract.mat'));
```

From the repository root, set the capture, extraction, and fresh output paths.

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m h2prism.phase10 $runDir $extractionPath $newOutputDir
```

`comparison.json` contains the source and capture hashes, execution metadata, per-sensor metrics, physical evidence, and claim statuses. `per_sensor.csv` includes matched counts, maxima, MAE, RMSE, and RMSE normalized by the reference RMS when nonzero. `discrepancies.json` records the shared-knot findings and scientific limitations. `shared_knot_discrepancies.png` plots the 20?40 s window without aligning through interpolation.
