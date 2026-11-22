# Independent pilot qualification

## Frozen reference

The archive causal replay remains exploratory. Random forest registered 48/48 new alarms, 16 false episodes and median/maximum delays of 84/7,764 s. Linear SVM registered 37/48 new alarms, 2 false episodes and a median delay of 84 s. Both used 65.6283 archive inactive hours. The ten accepted controlled Center captures and historical benchmark remain frozen. Verified independent families remain zero.

## Source qualification

The inventory hashes nine supplied SLX archives, examines their saved system XML and checks the pinned original and anomalous Center hashes. This is a static inspection. Candidate block names do not determine runtime class truth.

| Class | Established mechanism | Qualification |
|---|---|---|
| NORMAL | Pinned Center reservoir SID 1 receives its native boundary command. SID 59 changes the internal SID 55 pressure-source differential from 3.0 to 6.4 MPa at 25 s as part of the nominal schedule. | Reproduced reference trajectory. Preserve native initial-state policy and boundary commands. Neither the transient nor a fresh session establishes an independent NORMAL root. |
| LEAK candidate | Controlled atmospheric withdrawal through restrictions SID 213, 312 or 215. Accepted twins use 0.001 m² control and 0.0011 m² opening at 1,000 s. In the alternate SID 213 pair both twins receive +5 kPa at SID 1 from 500 s. | Qualified only as controlled outlet-opening simulations, with signed flow and stored pressure responses. The opening persists through the horizon; no closure time is established. Settings are tested intervention points. A certified physical range or independent genealogy is unavailable. |
| FAULT | SID 55 is a controlled Pressure Source (G). A late command changed 6.40 to 6.23 MPa in the accepted operational rival. | BLOCKED. A commanded differential change is not evidence of a compressor failure. Need source-traceable compressor or actuator model, fault injection interface, valid fault magnitudes and actual response, onset and clearing rules. |
| DELAY | Native SID 59 schedule is recorded. The archive contains delay annotations. | BLOCKED. A nominal scheduled pressure step or annotation does not isolate delayed actuation. Need a traceable command/response pair, nominal lag, time base, delay intervention and onset/end semantics. |

The Center anomalous archive's SID 563 step is 1e-10 at both endpoints. Its presence cannot qualify a timed leak generator. Sensor truth for supported controlled openings comes from received area and signed branch measurements; the 13 sensor values are model outputs and do not independently establish location. Unknown realistic magnitudes, pressure envelopes and gas fidelity remain open.

## Smallest admissible pilot

First qualify one new source-backed FAULT mechanism and one DELAY mechanism offline. For each require canonical block path/SID, verified input/received response, immutable nominal and treatment deltas, physical operating envelope and data provenance, including onset/end and any sustained response. Then use independently generated, in-domain roots with explicit representative event-free NORMAL periods and outlet location variants. Include baseline and one alternate profile plus a magnitude variation only once the model and range are qualified. A matched control and treatment may share a root within a partition. Neither may cross partitions.

Each root reserves its own generating initialization and seed where randomization is used. Do not import a saved state from another partition or duplicate a raw trajectory. Record root/parent, checkpoint hash, seed, command history, initial and boundary histories, model/topology/solver hashes, unit and sensor schema, labels, operating conditions, raw/export hashes and case acceptance. Same-topology roots support within-model validation only. Give development, calibration and untouched test separate roots and class/region support. Set precision targets and operational error budgets before deciding family counts. A pilot can estimate variability and identify missing evidence; it cannot guarantee power or generalization.

The pilot manifest intentionally has no approved records. The executable preflight ran and returned BLOCKED because no independent roots support classes and locations across the partitions. No MATLAB command is approved. Before a later compile/run, require accepted mechanism evidence, source/model-delta hashes, fresh directories, independent root receipts, and preflight proof that solver, logging, units, sensor mapping and initialization match the design. After execution require complete timestamps, finite 13-channel observations for these Center captures, correctly received commands, signed boundary/storage histories, event labels and conservation reporting, and independent review of deviations. Reuse the numeric capture pathway.

## Locked evaluation and uncertainty gates

- Detection uses a fixed five-sample 1 Hz causal window and a 120 s decision stride for the recorded reference protocol. Positive opens an alarm and first negative resets. Only new starts inside the verified event receive detection credit. Inactive exposure spans first to last decision, excluding true active time, warm-up and unsampled tail. A tighter deadline requires a specified operational budget and a separately frozen cadence before the test.
- Four-class training can reuse the existing five model families, with majority and always-event controls for binary detection. Lock candidate settings on development roots, calibrate separately and expose test roots once. Report per-class and per-root uncertainty only where there is class support. Compare event delay against predeclared operational deadlines and missed-event, inactive episode and robustness budgets. No operational deadline or budget has yet been supplied, so no model can pass a field performance gate.
- Qualify measurement units, bias/noise bounds, sensor synchronization and latency, initial/boundary admissible sets, parameters and gas settings, independent model discrepancy, and solver/numerical error. A source-compatible adapter must propagate these to simultaneous prediction enclosures for every hypothesis, including operational pressure and genuine fault rivals. Solver refinements and assumed perturbations remain numerical or hypothetical evidence.
- Location inference is conditional on a supported event and independent cases at every candidate region. Configured SID truth alone excludes no rival. Formal FEASIBLE or EXCLUDED requires qualified evidence. Current outcomes remain INDETERMINATE / UNRESOLVED / L0. Compare classifier, calibrated abstention and formal policy on the same observations at matched nonzero coverage only after evidence and calibration gates pass.
- External transfer needs a named sensor-role mapping with stated pressure/mass-flow units, validated timestamp and sampling conventions, known regime and faults, traceable labels and quantified instrument errors. Existing input validators support software mapping; a new topology, composition or role set needs separately qualified models and independent evidence.

## Reproduction

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m h2prism.phase13_pilot '<pilot_manifest.json>' '<fresh-source_preflight.json>'
```

The source inventory is a read-only qualification artifact. The preflight records the blocked disposition without starting MATLAB.
