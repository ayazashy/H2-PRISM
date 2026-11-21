# Phase 12 paired Center results

Both approved captures passed. This is one source-derived controlled simulation pair on a common 0.2 s fixed-step ode14x clock, from 0 to 20,000 s with 100,001 samples per channel. Both captures recorded ReachedStopTime and zero warnings/errors. The paired audit verified all 13 sensors and 101 required physical histories per run, array and clock integrity, the six signed external flows and eight storage components, the independent outlet evidence, and the approved source, model, configuration and capture hashes. The active ConfigSet and unrelated commands agree across the approved twins.

## Measured intervention

The control received 0.0010 m^2 throughout. Both twins recorded 0.0010 m^2 at 999.8 s. At 1,000.0 s the opening command and received area reached 0.0011 m^2, and outlet flow was 0.691269 kg/s higher on the same saved knot. Timing below the saved 0.2 s step is unresolved. The positive sign is toward the atmospheric reservoir SID 200.

| Outlet measure | Opening minus control |
|---|---:|
| Pre-event maximum absolute difference | 9.37436e-5 kg/s |
| At 1,000 s | +0.691269 kg/s (9.99535% of control) |
| Peak, at 17,000 s | +0.694549 kg/s |
| Mean over last 1,000 s | +0.614754 kg/s |
| Final | +0.588247 kg/s (9.91531% of control) |
| Extra outlet mass over 1,000 to 20,000 s | +13,064.834 kg |

The last-window mean describes a sustained effect while the operating commands continue changing. The measured flow increments and the area increment are distinct quantities.

## Sensor evidence

All pre-event differences fell within the observed NORMAL-to-historical-reference comparison scale or the 1e-11 native-unit reporting floor. Largest pre-event maxima were 1.80073e-4 MPa at PS1 and 9.37436e-5 kg/s at MFS3. The results support close numerical matching and carry no validated tolerance. Post-event peak magnitudes were 6.04902e-4 MPa at PS1 and 0.694549 kg/s at MFS3. PS5 and PS7 stayed below 2.2e-13 MPa. The CSV contains all 13 sensors, signed peaks, pre/post RMSE, the final change, late-window means, and descriptive onset.

The exploratory screen requires five consecutive absolute paired differences above each channel's own pre-event maximum or the reporting floor. Two channels cross the envelope at 1,000 s, and PS1 and MFS3 satisfy the five-sample screen in the first second. Five channels satisfy it within 5 s and eleven within 30 s. Five samples at 0.2 s cadence require at least 0.8 s of observed persistence from the first crossing. This screen uses both completed trajectories and provides retrospective separation evidence. It does not estimate detector accuracy or a deployment detection delay. The pressure and mass-flow overview plots display every tenth sample; numerical results use the original saved timestamps.

## Conservation and formal claims

The final event-aware Simpson residuals are -0.939 kg for NORMAL and -1.306 kg for opening. Plain trapezoid gives -114.467 and -114.684 kg. The event-aware method integrates smooth pieces separately and left-holds only the recorded discontinuity brackets. Final storage is 434.001 kg lower in the intervention, with event-aware integrated net inflow 433.633 kg lower. Per-boundary increments are in the JSON. Both pointwise flow-accounting residuals are 4.55e-13 kg/s. No certified conservation error bound is established.

The existing H2-PRISM engine takes the 13 native channels of the first 5 s, with unqualified uncertainty explicitly absent. It reports INVALID_UNCERTAINTY, every hypothesis INDETERMINATE, and external UNRESOLVED. The numerical envelope is excluded from the certified measurement contract. The current localization function yields L0. SID 213 identifies the engineered intervention ground truth, while the sensor evidence does not uniquely localize it against alternative outlets.

## Short remaining experimental matrix

1. At the same operating profile, add a metered alternative outlet at restriction SID 312 through MFS1 SID 311 to reservoir SID 316, and an unmetered alternative at restriction SID 215 to reservoir SID 217. Use the traced existing restriction mechanisms, an explicit area intervention, a matched no-opening control and identical logging for each implementation. Verify configuration and correct pre-event agreement before comparing. This adds the minimum contrasting metered and unmetered candidates; SID 222 to reservoir SID 224 is a subsequent unresolved alternative.
2. Add one separately specified operating-event rival using the traced native pressure command at pressure-source SID 55. Set its intervention within a reviewed model operating range, maintain the matched unaffected controls, and record the actual command and response. This supplies a non-outlet alternative without assigning a compressor-fault label.
3. Repeat the SID 213 control/opening pair under one separately source-traced boundary profile and repeat one exact run to assess numerical reproducibility. All these cases retain the Center source family. Independent confirmation and calibrated confidence-abstention comparison require eligible disjoint families, justified uncertainty, and separate calibration and evaluation evidence. The current collection cannot support that claim.

The archived LEAK case remains blocked. Hydrogen fidelity, field deployment readiness, and independent diagnostic performance remain unverified.

## Reproduce

From the repository root, point to the approved retry, original approval and Phase 11 0.2 s reference directories, and choose a fresh output directory. The command only reads existing captures.

    $env:PYTHONPATH = 'src'
    .\.venv\Scripts\python.exe -m h2prism.phase12_pair $retryRoot $priorRoot $reference $newResults
