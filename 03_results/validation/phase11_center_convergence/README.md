# Center NORMAL numerical convergence report

## Decision

All three saved Center NORMAL captures are usable for source-model numerical comparison. The evidence supports empirical refinement for most sensor channels and identifies the pressure-step quadrature as the dominant integrated mass discrepancy. It does not establish a uniform sensor convergence rate, exact mass closure, physical hydrogen fidelity, or a matched timed LEAK case.

| Claim | Classification |
|---|---|
| Three-case execution integrity | VERIFIED |
| Numerical sensor convergence | PARTIALLY VERIFIED |
| Integrated mass conservation | PARTIALLY VERIFIED |
| Archived source-model reproduction | VERIFIED for the source execution and the Phase 10 close archive match |
| Exact clean-release reproduction | CONTRADICTED |
| Physical hydrogen fidelity | UNVERIFIED |
| Controlled NORMAL/LEAK eligibility | UNVERIFIED, candidate remains BLOCKED |

## Capture and alignment

The original and both isolated SLX copies match the same pinned SHA-256 beginning 710711f41e33. The run metadata gives ode14x, fixed steps of 0.8, 0.4, and 0.2 s, a common 0 to 20,000 s interval, ReachedStopTime, and zero saved warnings or errors in each case. Each of the 13 channels contains respectively 25,001, 50,001, and 100,001 strictly increasing samples. There are no duplicate or near-colliding knots, missing or nonfinite values, or nonpositive absolute pressures. MATLAB extraction and round-trip CSV parsing give exact equality for all values and timestamps. All six boundary rate histories and eight storage densities are complete on each solver clock. File checksums and execution telemetry are in convergence.json.

The saved original configuration, initialized setup outside FixedStep, input mappings and definitions, gas settings, MATLAB/toolbox version, and model hash are identical. Each solver delta records FixedStep as the only change among enumerated parameters. The solver was also independently verified from runtime metadata. Two solver options, AlgebraicLoopSolver and InsertRTBMode, were unavailable to the runtime enumeration. The model bytes and original settings remain pinned. The Simscape local solver was disabled for both fine runs.

Comparisons use binary64 values at the coarser saved grid of each pair, with no interpolation. The gate allows at most eight floating-point spacings at each clock magnitude, and all observed paired timestamps agree exactly. Relative RMSE uses the reference RMS when nonzero.

## Sensor differences

| Fixed steps (s) | Shared knots | Maximum pressure (MPa), PS1 | Maximum flow (kg/s), MFS3 |
|---|---:|---:|---:|
| 0.8 vs 0.4 | 25,001 | 0.0683514 | 0.0410142 |
| 0.4 vs 0.2 | 50,001 | 0.0344479 | 0.0182231 |
| 0.8 vs 0.2 | 25,001 | 0.1020121 | 0.0585652 |

These maxima occur at the first shared post-step knot, 25.2 s for the fine pair and 25.6 s for pairs with the 0.8 s case. Outside 20 to 40 s the 0.4 vs 0.2 maxima are 0.0186565 MPa and 0.00974325 kg/s at 4.8 s. At 20,000 s the same pair's maxima are 6.842e-6 MPa and 5.452e-5 kg/s.

On the common 0.8 s grid, successive RMSE decreases for 10 of 11 channels with differences above the reporting floor. PS1's ratio is 0.482 and MFS3's is 0.803. MFS1's ratio is 1.425 even though its maximum difference decreases. PS5 and PS7 stay below 6e-13 MPa and are omitted from the ratios. The reporting floor is 1e-11 native units. It is a numerical reporting rule and carries no physical acceptance implication. The solver quantizes the step differently across resolutions and no formal order is inferred.

## Mass balance and event timing

| Step (s) | Final storage (kg) | Storage gain (kg) | Trapezoid net flow (kg) | Trapezoid residual (kg) | Left-held event bracket (kg) | Split Simpson residual (kg) |
|---|---:|---:|---:|---:|---:|---:|
| 0.8 | 1,000,107.354 | 8,421.392 | 8,877.345 | -455.953 | +10.630 | +3.725 |
| 0.4 | 1,000,107.341 | 8,421.379 | 8,655.596 | -234.217 | -0.927 | -3.286 |
| 0.2 | 1,000,092.281 | 8,406.319 | 8,521.067 | -114.749 | +1.850 | -1.304 |

All cases start at 991,685.962 kg. Residual is storage gain minus integrated signed boundary flow. At 0.2 s, the absolute raw trapezoid residual is 1.365% of storage gain. Split Simpson reduces this to 0.0155%. A left-held event bracket with trapezoidal integration elsewhere gives a smaller discrepancy than raw trapezoid in every case, but its absolute residual grows from 0.927 kg at 0.4 s to 1.850 kg at 0.2 s. Simpson across the jump without splitting gives -307.343, -315.235, and -156.992 kg respectively.

The configured switch is at 25 s. The last stored pre-step point is 24.8 s for every case. The first stored post-step points are 25.6, 25.2, and 25.0 s respectively. Boundary flow goes from about -8 kg/s to about +1,158 kg/s. Neither side of the discontinuity is logged twice at the same timestamp. The internal switch time between stored points cannot be recovered for the 0.8 and 0.4 s runs from these captures alone. Across the three brackets the trapezoidal residual jumps by -466.546, -233.281, and -116.596 kg. The event-aware calculation holds the prior rate only on this bracket, then applies the indicated rule elsewhere. The corresponding bracket masses closely match the observed decreases in storage. This convergence pattern supports coarse integration across the event as the dominant discrepancy. The remaining kilogram-scale error has no validated uncertainty bound.

## Reproduce without MATLAB simulation

From the repository root, point to the audited baseline directory, its saved extraction, the root of the two fine cases, and a fresh output directory.

    $env:PYTHONPATH = 'src'
    .\.venv\Scripts\python.exe -m h2prism.phase11 analyze $baselineDir $newOutputDir --extraction $baselineExtractionMat --cases $caseRoot

The detailed output includes complete compressed residual histories for all three resolutions. The proposed leak comparison remains blocked until an independently traceable archived Center case establishes a nonzero timed opening, location and magnitude under matched unrelated settings. The current candidate's identical area commands still provide no timed leak. The unresolved clean-release generating run and preprocessing chain, gas composition, and physical validation remain separate gaps.
