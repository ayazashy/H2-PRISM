# Center controlled atmospheric-outlet experiment

**Archived anomaly: BLOCKED. New engineered pair: CONDITIONAL.** Both isolated source copies and parameter specifications are prepared. No MATLAB compilation or simulation has been run for this phase.

## Source findings

| Evidence | Archived comparison |
|---|---|
| Source identity | The pinned NORMAL and anomalous SLX hashes are recorded in source_difference.json. They establish local archive identity. The clean-release generating run remains unidentified. |
| Topology and location | SID 213 joins the PS1 junction (SIDs 47, 48 and 50) to MFS3 (SID 218) and then atmospheric reservoir SID 200. The only added root block is PS Step SID 563. Its only added physical wire goes to the restriction area input. Three child-system XML records are byte-identical. |
| Restriction physics | NORMAL uses a fixed 0.001 m^2 area. The anomalous model makes that restriction variable and drives it with 1e-10 m^2 both before and after a nominal 1 s step. The observed design change represents a nominal outlet held nearly closed, with no timed opening. |
| Boundaries and compressor proxy | Six existing reservoir configurations and both native pressure-source commands have unchanged root parameters. The compared controls actuate pressure-source blocks; this comparison does not establish a compressor-specific fault. |
| Gas, sensing, initialization | Gas Properties SID 4, the 13 sensor blocks and eight storage components have unchanged root parameters, including saved initialization targets. This comparison does not recover the anomalous run's actual initialized state or runtime lineage. |
| Solver | The anomalous archive stores ode14x/0.8 s in place of NORMAL's saved auto solver and 1 s field. The original audited NORMAL launcher also used ode14x/0.8 s; the controlled pair both use 0.2 s. |

SID 200 is an atmospheric sink. Its inactive specified-pressure field is 0.101325 MPa. The verified NORMAL capture recorded 0.100 MPa and 293.15 K internally. A variable gas restriction uses a pressure-dependent flow relation and saturates its area command at the configured limits. The outlet is bidirectional as a model component. Signed measured outflow and pressure direction must establish the actual event response. [MathWorks Local Restriction (G)](https://www.mathworks.com/help/simscape/ref/localrestrictiong.html) and [MathWorks Reservoir (G)](https://www.mathworks.com/help/simscape/ref/reservoirg.html)

## Matched design

Both twins use the original NORMAL model as the parent. Both convert SID 213 to variable and add one PS Step physical signal connected from O to area_in. The nominal pre-event area stays at 0.001 m^2 in both twins. The NORMAL control then stays at 0.001 m^2. The intervention increases to 0.0011 m^2 at 1,000 s. This is an engineered 10% change in the conductance control area of an existing atmospheric outlet. It does not add a separate rupture aperture and does not predict a calibrated leak rate. The archived limits are 1e-10 to 0.01 m^2 and the original discharge coefficient is 0.64. The experiment changes neither limit nor coefficient.

Both twins retain the same gas configuration, solver family, 0.2 s step, 20,000 s horizon, original initialization policy, sensor mapping, and unrelated controls. The 1,000 s event lies on the 0.2 s clock and is separate from the original 25 s pressure step. The Phase 11 refinement results motivate 0.2 s without providing a certified error bound. Changing the restriction realization is common to both twins. Any effect it has on the derived control must be measured against the completed original 0.2 s NORMAL case.

The source gas settings and runtime equation of state support a configured perfect-gas representation with R = 0.287 kJ/(kg K) and Z = 0.998386. The experiment concerns this model. No hydrogen composition or physical validation is established.

## Preflight and execution

The preflight loads only the checksum-pinned isolated parent, verifies gas-branch endpoints and the exact area command, compiles without running a trajectory, checks the existing links/parameters/wiring and saves the derived model in the case folder under a fresh name. The Python pair check requires all saved system and solver XML to agree after removing the single intended final-area delta. It writes a hash-bound approval record for the exact derived files. No successful MATLAB preflight or execution is claimed here.

Start in the existing MATLAB Command Window with both model names closed.

    addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
    pair = 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_cases';
    h2prism_center_outlet_case('preflight',fullfile(pair,'normal'));
    h2prism_center_outlet_case('preflight',fullfile(pair,'outlet_opening'));

After both preflights complete, run this from the repository root in PowerShell.

    $env:PYTHONPATH = 'src'
    .\.venv\Scripts\python.exe -m h2prism.phase12 approve 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_cases'

Return to the same MATLAB session and execute each approved twin separately. Run the intervention only after the control completes.

    h2prism_center_outlet_case('execute',fullfile(pair,'normal'));
    h2prism_center_outlet_case('execute',fullfile(pair,'outlet_opening'));

Each case preserves its solver diary and raw MAT output before checking the received area, signed outlet/sink flow, upstream/downstream pressures and sink state. The extraction includes 13 sensors and native physical records. Programmatic agreement gates for command and flow consistency are numerical checks rather than calibration tolerances.

Once both finish, analyze from the repository root with the completed original 0.2 s NORMAL case as the reference.

    .\.venv\Scripts\python.exe -m h2prism.phase12 analyze 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_cases' --reference 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase11_cases/step_0.2' --output 'C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_cases/paired_result.json'

The analysis compares derived NORMAL against original NORMAL, pre-event matching and post-event sensor response on the native saved grid. Eligibility requires review of those observations and the actual timed increment in atmospheric outflow. The configured SID is intervention ground truth for this model; it does not establish physical identifiability or independent localization performance.
