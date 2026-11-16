# H₂-SimNet source study

This is a simulation study. The executable preflight checks the pinned V03 manifest, clean assets, stored clocks, binary annotations, event onset and delay offset. It reuses the Center sensor trace and evidence engine. Archive integrity and consistent labels do not establish a physically reproduced event. The historical LOTO splits cross the declared dependency groups. They are not admissible for independent scoring under this protocol.

## Source-first handoff

The last isolated MATLAB attempt failed at startup with 5202. After an authorized restart if needed, open MATLAB normally and confirm Simulink and Simscape entitlement and library load. If 5202 persists, use the license administrator or MathWorks Service Host support path. Repeat no unattended startup attempts before successful checkout. [MathWorks startup guidance](https://www.mathworks.com/matlabcentral/answers/1815390-why-do-i-receive-error-5202-unable-to-access-services-required-to-run-matlab)

Only after that gate, from the repository root, create a new scratch directory outside the archive and run the following with an absolute directory path. This follows the archived launcher solver configuration while preserving the original model stop time. It captures configured solver and gas settings, logged physical controls, states, the Simscape log and raw sensor clocks. Inspect the raw logs for effective values and unresolved inputs. Any reduced-duration diagnostic run is not a release reproduction. Full-model logging needs adequate memory and disk. The MATLAB code was not run in this phase. [Simscape logging](https://es.mathworks.com/help/sps/ug/examine-the-configuration-for-simulation-data-logging.html) · [Simulink state logging](https://www.mathworks.com/help/simulink/ug/save-state-information.html)

```powershell
$run = '<absolute-new-scratch-directory>'
New-Item -ItemType Directory -Path $run -ErrorAction Stop | Out-Null
$slx = 'data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/normality_scenarios/normality_datasets/Normal_HNetwork_gest_center.slx'
$expected = '710711F41E33ADB9EA54220580ADEFD0065EEB9A8A376727DD045FC474ED7B1E'
if ((Get-FileHash -LiteralPath $slx).Hash -ne $expected) { throw 'Center source hash mismatch' }
Copy-Item -LiteralPath $slx -Destination $run
$copy = Join-Path $run 'Normal_HNetwork_gest_center.slx'
if ((Get-FileHash -LiteralPath $copy).Hash -ne $expected) { throw 'Isolated copy hash mismatch' }
$tools = (Resolve-Path tools/simulation).Path
matlab.exe -wait -logfile "$run/console.log" -batch "addpath('$tools'); h2prism_center_source_capture('$run')"
if ($LASTEXITCODE -ne 0) { throw 'Center capture failed' }
if ((Get-FileHash -LiteralPath $copy).Hash -ne $expected) { throw 'Isolated copy changed' }
```

Reconcile the reproduced source against the released Center windows. Establish the effective gas configuration and absolute pressure reference, signed physical sensor roles, boundary and inventory histories, and the generating-run lineage. Then qualify one matched leak with an independently traced mechanism, region and onset. Compressor-fault and delay require recovered actuator controls, interventions and response. Until those exist, a reduced NORMAL/LEAK study requires explicit scope approval and both source-compatible hypotheses.

## Center input-discovery preflight

The SLX serializes library links as Reference records. Runtime MATLAB can expose a linked masked converter as a SubSystem. The capture resolves the checksum-pinned SIDs and checks the library link, connected Simulink drivers, tags, units and pressure-source mode instead of filtering by archive block type.

| Role | Pinned input route | Capture |
| --- | --- | --- |
| Reservoir temperature | Reservoir Inputs output 2 ? T1 Goto 10 / From 3 ? converter 5 ? controlled reservoir 1 | Simulink command, K. The subsystem uses Constant 13 with declared value 288. |
| Reservoir pressure | Reservoir Inputs output 1 ? P1 Goto 9 / From 2 ? converter 6 ? controlled reservoir 1 | Simulink command, bar. The subsystem combines Ramp blocks 14, 15 and 439. |
| Controlled pressure-difference input | PS Step 59 ? Pressure Source 55 | Native Simscape connection. Save mask settings and the full Simscape log. |
| Controlled pressure-difference input | PS Ramp 241 ? Pressure Source 239 | Native Simscape connection. Save mask settings and the full Simscape log. |

The native physical inputs have no Simulink signal port to mark for logging. Their logged time histories must be checked in the raw Simscape output; a mask expression is not a measured trajectory. The atmospheric reservoir boundaries, restriction areas and gas block values are configured fields rather than additional traced control signals. No From Workspace blocks were found in the two traced diagrams. Runtime dependency resolution, gas validity and actual boundary flows still require the isolated run.

Run the offline checker with `python tools/simulation/verify_center_input_plan.py <Center-copy.slx>`. In the authorized MATLAB session, use `[inputMap, physicalInputs, centerGuard] = h2prism_center_open_inputs(runDir)` to verify and inspect the live mapping without simulation. Display the two maps and run `clear centerGuard` before calling the capture. The guard closes the loaded copy without saving and restores the working directory. Use a copy outside the repository. [MathWorks linked blocks](https://www.mathworks.com/help/simulink/slref/libinfo.html)

## Executable evaluation gate

Generate the source requirements and actual archive preflight from the repository root.

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m h2prism.simnet_study --output simnet-preflight.json
.venv/Scripts/python.exe -m pytest -q tests/test_simnet_study.py tests/test_phase6.py tests/test_experimental_data.py tests/test_phase4.py tests/test_certified_evidence.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```

For a qualified run, use `archive_observation` with the reviewed sensor map and predeclared row window. It preserves native units, signs, channels and time grid. The window must stay within the verified archived event interval. Use `adapter_spec` to pin the reviewed source-adapter configuration. The approval binds the original observation, model configuration, physical and sensor bounds, ontology and protocol. The adapter implementation and evidence still require independent review.

The held-out input JSON requires `study_version`, `manifest_sha256`, `partitions`, `event_ontology`, `observation_digests`, and optional `localization_cases`. Lock it before held-out outcome inspection. `evaluate_heldout` requires an observation and reviewed source qualification for every held-out scenario, with one decision per independent group, and rejects cross-partition family or asset reuse. The matched conventional baseline receives the same checked joint results. It is not a separate solver benchmark. Spatial scoring is predeclared and needs verified region truth and a separately pinned spatial model. The spatial pass runs only after specific LEAK evidence and retains every non-leak rival. Abstentions remain in the eligible analysis denominator.

Use the same windows, families and ground-truth rules for all methods. Predeclare robustness comparisons for paired noise-added and clean runs, sensor removal, independently justified uncertainty widening, and topology/family sensitivity. The implemented scoring entry point is clean-only. Robustness execution remains pending source qualification and frozen arm-specific observations, bounds and adapter reviews. No physical certificates, held-out scores or robustness results were produced in this phase.
