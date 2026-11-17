# Center NORMAL convergence stage

The completed baseline is the sole executed case in this record. The 0.4 s and 0.2 s cases are prepared as separate checksum-verified copies of the pinned source. No LEAK case was run.

## Conservation audit

The seven compressible pipes and one single-port chamber supply internal density in kg/m^3. Multiplying by each fixed volume yields total stored mass. The six external reservoirs use port A and are excluded from storage. Their logged port mass flow is positive into the reservoir, so the network boundary sum is its negative. The sum agrees with the storage-component port-flow sum to 2.28e-13 kg/s. Baseline integration uses all 25,001 saved timestamps from 0 to 20,000 s. No duplicate times were found. The network has enough recorded terms to perform the numerical integral check.

| Baseline method | Integrated net flow (kg) | Storage change minus flow (kg) |
|---|---:|---:|
| Trapezoid on saved timestamps | 8,877.345 | -455.953 |
| Simpson across the entire series | 8,728.735 | -307.343 |
| Trapezoid, left hold on the event bracket only | 8,410.762 | +10.630 |
| Simpson split at event bracket, left hold inside bracket | 8,417.667 | +3.725 |

Storage increased by 8,421.392 kg. On 24.8 to 25.6 s, boundary flow jumped from -7.967 to +1,158.492 kg/s at the first logged post-step sample. The stored mass decreased by 6.336 kg in that interval. Trapezoidal integration instead assigned +460.210 kg, shifting the signed residual by approximately -466.546 kg. A left-held calculation gives -6.373 kg for that interval. The effect is a consequence of how the coarse quadrature spans the observed jump. Both split methods are sensitivity calculations. They leave a remaining residual and cannot establish numerical convergence or the exact flow between the saved samples. The ramp's 9.6 to 10.4 s bracket is recorded separately.

## Release and LEAK

On shared knots from 25 to less than 160 s, PS1 contributes 99.83% and MFS3 92.19% of their full-trajectory squared release discrepancy. At exactly 28 s the release differs from the archived CSV by +0.089702956 MPa and +0.053028216 kg/s. The transient timing fit from Phase 10 cannot identify a global offset or the generating run. A source-bound raw release precursor and its full preprocessing records are required.

The archived candidate is Anomalous_HNetwork_gest_center.slx, SHA-256 e6caa8cf6558f7a524fd2a4e53ecb0530cf84479cbdf06c7dde4a02ef29acf33. SID 213 was changed from a fixed 0.001 m^2 restriction to a variable restriction and connected to PS Step SID 563. It sits on the outlet branch from the PS1 junction to MFS3 and reservoir SID 200. Both step area values are 1e-10 m^2 at a nominal step time of 1 s, so the saved command has no opening event. The candidate also pins ode14x/0.8 s in its saved solver settings. The remaining common block parameters, gas topology, and three child XML files show no substantive differences in the comparisons recorded here. The file-to-release generating lineage and a valid timed leak mechanism are both unverified. Eligibility is **BLOCKED**.

## Run and analyze

Prepare copies from the repository root with the existing Python environment. Use a fresh destination and leave the 0.8 s capture intact.

    $env:PYTHONPATH = 'src'
    .\.venv\Scripts\python.exe -m h2prism.phase11 prepare $baselineDir $casesDir

In the working interactive MATLAB session, keep the source model closed and set absolute baseline and case-root paths. Run 0.4 s first. Run 0.2 s after the first reports completion. Each case writes an independent diary, solver delta, setup, raw capture, and plain extraction.

    addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
    h2prism_center_convergence_case(fullfile(casesDir,'step_0.4'), fullfile(baselineDir,'center_setup.mat'), 0.4);
    h2prism_center_convergence_case(fullfile(casesDir,'step_0.2'), fullfile(baselineDir,'center_setup.mat'), 0.2);

Analyze after both case diaries record completion.

    .\.venv\Scripts\python.exe -m h2prism.phase11 analyze $baselineDir $freshOutputDir --extraction $baselineExtractionMat --cases $casesDir

The maintained analyzer requires both fine runs and checks their raw capture hashes, execution metadata, step deltas, and sensor-clock correspondence before generating comparisons. Physics fidelity and diagnostic or localization readiness are outside what the baseline establishes.
