# Phase 12 NORMAL capture acceptance

**ACCEPTED as the Phase 12 derived control. Execute only the approved Outlet Opening twin next.**

## Evidence and timing

The saved execution reached 20,000 s at 0.2 s fixed-step ode14x, with no recorded warning or error. Each of 13 sensors and 101 required physical series is finite and aligned with the same 100,001-point clock from 0 to 20,000 s. No duplicate clocks or missing histories were found. The pressure sensors use absolute MPa and span 0.294 to 7.120 MPa, above the pinned perfect-gas configuration's 0.1 MPa lower limit. The signed mass-flow sensors use kg/s. Each exported sensor was independently matched to its Simscape log signal in native units.

Raw and extracted MAT values match throughout after removing the extraction's raw-file SHA-256 field. The sensor checkpoint's execution and sensor fields are identical. The outlet evidence matches the independently stored native signals after pressure conversion from MPa to Pa. The phase retained the two reservoir commands, native pressure-source commands, six signed external rates, eight storage density/pressure/temperature histories, and 34 physical time-zero records. Signal, solver-state and root output datasets were disabled in memory. These Dataset objects are outside the required Phase 12 scientific set.

Both case preflights and SLX files match their approvals. The existing and retry approval receipts match. The active ConfigSet JSON and subsystem XML match across both saved twins except for the intended final area command in the root system XML. The logging policy agrees with the approved model, the documented defaults for omitted settings, and the output model hash. The observed policy file's SHA-256 is recorded in the audit. There was no separately pre-recorded digest of that runtime-generated file.

## Commands and physical response

The reservoir pressure command fell from 740,000 to 294,000 Pa, with temperature constant at 288 K. These command histories match the original reference exactly. The pressure-source step and ramp agree with the reference to at most 4.98e-8 Pa. The outlet command and the restriction's received area are each exactly 0.001 m^2 for all 5,000 samples before 1,000 s and all 95,001 samples at or after it. No opening timestamp was recorded.

The measured outlet flow spans +4.80549 to +6.95262 kg/s. Positive flow goes from restriction port A toward atmospheric reservoir SID 200. The restriction, MFS3 and reservoir port measurements corroborate this direction. Upstream pressure stays above downstream pressure, and the sink is at 100,000 Pa and 293.15 K. The pointwise boundary versus storage-port rate discrepancy is 4.55e-13 kg/s. The integrated residual is -114.467 kg using raw trapezoidal integration and -0.939 kg with the Phase 11 event-aware split Simpson rule. Neither estimate is a certified error bound.

## Historical NORMAL comparison

All 100,001 saved timestamps match the audited original 0.2 s NORMAL reference exactly. The derived control has a small, measurable baseline difference even with a constant area.

| Scope | Maximum pressure difference | Maximum flow difference |
|---|---:|---:|
| Before 1,000 s | PS1, 1.80219e-4 MPa | MFS3, 9.38196e-5 kg/s |
| At or after 1,000 s | PS9, 8.25390e-7 MPa | MFS3, 1.33037e-5 kg/s |

Both pre-event maxima occur at 4.8 s. The pre-event RMSE for the same sensors is 6.52449e-6 MPa and 1.81134e-5 kg/s. These observations capture the combined differences of the derived implementation and logging pathway and do not isolate their individual effects. The engineered opening should be compared to this Phase 12 control. Reference offsets, hydrogen fidelity, and any physical uncertainty or certification claims remain unresolved.

## Reproduce

From the repository root, point to the retry root, the original approval root, the Phase 11 0.2 s reference and a fresh output directory. The command reads the captures and writes only the requested audit output.

    $env:PYTHONPATH = 'src'
    .\.venv\Scripts\python.exe -m h2prism.phase12_acceptance $retryRoot $priorRoot $reference $newReportDir

Run the approved opening in the authorized MATLAB session with Center_phase12 closed.

    addpath('C:/Users/ahmd1/Documents/H2-PRISM/tools/simulation');
    rehash;
    h2prism_center_outlet_case('execute','C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism/work/phase12_sdi_retry_01/outlet_opening');

No simulation was rerun during acceptance.
