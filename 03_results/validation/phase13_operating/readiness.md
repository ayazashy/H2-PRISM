# Phase 13 Center competing hypotheses

Four isolated Center source copies match SHA-256 `710711f41e33adb9ea54220580adefd0065eeb9a8a376727dd045fc474ed7b1e`. All 42 capture-file hashes for the six accepted Phase 12 runs were rechecked locally. No Phase 13 model has been compiled or simulated.

| Pair | Control | Intervention | Evidence status |
|---|---|---|---|
| Internal pressure command | Native SID 59 step and constant 0.001 m2 outlet area | SID 55 drops from 6.4 to 6.23 MPa at 1,000 s; outlet remains constant | Source trace and designs verified; runtime pending |
| Alternate boundary profile | Both twins add 5 kPa through SID 6 to reservoir SID 1 at 500 s. Outlet holds 0.001 m2 | Same boundary trajectory; SID 213 increases to 0.0011 m2 at 1,000 s | Source trace and designs verified; runtime pending |

The original SID 59 step raises the SID 55 differential from 3 to 6.4 MPa at 25 s. SID 55 is an internal controlled Pressure Source (G) with isentropic power addition and 1.1340 m2 at each conserving port. Its saved 4 MPa constant field is inactive in controlled mode. Its positive input means pressure at B exceeds pressure at A. Signed mass flow at A and B determines the actual gas-flow direction, which the new capture requires. See [MathWorks Pressure Source (G)](https://www.mathworks.com/help/simscape/ref/pressuresourceg.html).

The pressure intervention magnitude is 5% of the native step span. The alternate profile holds the archived initial policy and allows 500 s of shared evolution before the opening. At 500 s the reservoir command moves from 720 to 725 kPa; the observed nominal maximum over the full run was 740 kPa. The command envelopes qualify the proposed intervention settings for this software study. Equilibrium, equipment ratings, pure hydrogen validation, and independent experimental accuracy remain unverified.

## Run in the working MATLAB Command Window

```matlab
addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
h2prism_run_phase13('C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase13_02', ...
    'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_sdi_retry_01', ...
    'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase11_cases/step_0.2');
```

All four preflights and both pair approvals must complete before simulation. Each completed control must pass the Python capture audit before its intervention starts. The pressure pair uses the existing runner's `outlet_opening` directory key for its treatment, with no outlet opening. If the runner stops, preserve its partial files and inspect the last stage. A missing required physical series fails extraction.

## Analyze after all four captures pass

From the repository in PowerShell with its existing Python environment:

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m h2prism.phase13 analyze 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase13_02' 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_sdi_retry_01' --reference 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase11_cases/step_0.2' --rivals 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/final_research_matrix' --output 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/outputs/phase13/results'
```

The analysis recomputes acceptance, summarizes signed responses and event-aware conservation, compares normalized and native sensor differences, and runs the formal consistency engine with currently unknown prediction enclosures. It requires a fresh results directory. Existing Phase 12 separations, including SID 213 versus SID 312 at 30 s (all sensors 0.0408506, pressure only 0.0000837896), are descriptive Center simulations. Existing formal results are INDETERMINATE, UNRESOLVED, and L0. Diagnostic accuracy, coverage-risk comparisons, and calibration require eligible independent families and evidence that is currently unavailable.

**CONFIRMATORY ACCURACY AND ADDED VALUE: NOT ESTABLISHED**
