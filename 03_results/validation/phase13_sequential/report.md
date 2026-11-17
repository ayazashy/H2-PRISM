# Sequential detection and timing-aware evidence

## Methods
Replay used 51 checksum-verified clean archives, nine conservative dependency components, 48 annotated events and 65.6283 inactive archive hours. Both detector statistics consume each 1 Hz telemetry row once. The five-knot buffer measures max absolute four-second channel change divided by max(0.5% of the initial reading, 0.001 MPa for pressure or 0.005 kg/s for flow). EWMA uses 0.25 new and 0.75 old score. Alarm starts when score exceeds 5 and resets at 2 or below. All settings were fixed for this exploratory contrast; no labels tuned them. The first four samples warm up the buffer. Alarm decisions use fixed 1, 2, 5, 10, 30 and 120 s cadences from the first eligible knot and share the same final observed knot. Archive truth enters episode scoring only. The earlier frozen RF/SVM results are 120 s references. Their fold estimators were not refitted or evaluated at new cadences.

Input validation checks finite, correctly ordered sensor values and contiguous 1 Hz timestamps before changing state. Sensor roles and native units are fixed for this archive; the existing named-unit adapter is needed for differently named or converted external sensors. Invalid data must be handled as an invalid stream, not a confident prediction. Detector update time includes local validation, buffering and arithmetic, averaging 18.45 microseconds per row across clean cases; acquisition latency was unmeasured. History is four seconds first-to-last, followed by cadence effects and actual event-to-alarm delay. There is no subsecond sampling claim.

## Detection results

| EWMA decision cadence | New detections / 48 | Within 5 / 10 / 30 / 60 / 120 s | False episodes | False episodes / inactive hour | Median delay |
|---|---:|---|---:|---:|---:|
| 1 s | 39 | 30 / 31 / 31 / 31 / 31 | 42 | 0.640 | 0 s |
| 2 s | 39 | 30 / 31 / 31 / 31 / 31 | 42 | 0.640 | 0 s |
| 5 s | 35 | 30 / 30 / 30 / 30 / 30 | 45 | 0.686 | 4 s |
| 10 s | 35 | 24 / 30 / 30 / 30 / 30 | 45 | 0.686 | 4 s |
| 30 s | 34 | 0 / 6 / 29 / 29 / 29 | 45 | 0.686 | 24 s |
| 120 s | 21 | 0 / 0 / 9 / 12 / 15 | 0 | 0 | 44 s |

The change threshold and EWMA at 1 s both detected 39 and 31 within 10 s. Direct threshold yielded one more detection within 5 s, but 93 false episodes versus EWMA's 42. EWMA at 1 and 2 s tied on the tabulated counts, with maximum delays of 19,507 and 19,508 s. The 1 s distribution (min, quartiles, median, p90 and max in the delay table) has a long tail: p90 is 1,500 s. Zero-second detections are exact annotation/decision knot coincidences. Nine of 39 LEAK events were missed; all six archived FAULT and all three archived DELAY annotations had an eventual alert, without class recognition. With fixed EWMA, cadence variation changes sampling of short excursions; at the same cadence, the frozen forest and SVM differ in statistics/model behavior. Existing forest at 120 s detected 48/48 with 16 false episodes; linear SVM detected 37/48 with 2. No best operating point is qualified without alarm budgets and independent evaluation.

The assumed white and correlated noise each left the 1 s EWMA alarm open about 99.97% or 99.98% of observed time, leading to 51 false starts and zero new event detections. This is a persistent false state, even without repeated false starts. PS1 bias, stuck and delay and the MFS1 drift stress had the same aggregate 1 s EWMA counts as clean here. This is limited to the tested realization and sensors. Bias is a 1% PS1 offset from mid-run, drift is a 2% terminal MFS1 ramp relative to each initial reading; PS1 is stuck at the initial reading or delayed by two seconds. White innovations use max(1% initial magnitude, the engineering floor), with AR(1) coefficient 0.8 for the correlated mode. These are hypothetical stress scales. Missing inputs, wrong channel order and invalid clocks are rejected; there is no fallback classification or field robustness claim.

## Time and location geometry
Sensor templates are accepted treatment-minus-control trajectories scaled by each sensor's nominal Center RMS before 1,000 s. The 30 s distance uses 151 knots at 0.2 s. Hold one template fixed and shift the other by integer knots within ±0, 0.2, 0.6, 1 or 2 s, then report minimum and maximum RMS. The offset is a hypothetical nuisance variable and cannot certify clock error or exclusion. The clock-versus-event alignment for SID 59 remains a separate descriptive contrast.

The accepted 13-channel runs also had a 1 Hz causal alert replay. The first alerts for timing control and intervention were 25 and 26 s, matching onset on those saved knots. SID 213, SID 312 and alternate SID 213 had fresh alerts at 1,000 s, pressure rival at 1,002 s, and SID 215 had no new alert within 120 s. The reference nominal transient also produced alerts at 25 s in the other pairs. For the timing pair, alert alignment and retrospective event alignment therefore use the same knots. An alert can be absent or correspond to a nominal command; it does not independently identify a mechanism.

Allowing ±2 s gives minimum all-sensor pairwise RMS 0.040145 (213/312), 0.028431 (213/215), and 0.029388 (312/215). Pressure-only minima span 0.0000761–0.000366; flow-only span 0.05918–0.08357. Location ranks did not reverse over the tested offset bounds within each tested subset for the three comparison observations. The alternate SID 213 matched nominal SID 213 best across all these subsets, but its second-ranked rival flips between pressure and flow subsets. Omitting MFS1 also changes the second-ranked rival from SID 215 to SID 312 in the full-sensor derivative. Per-channel and leave-one-out tables identify evidence leverage on these cases; they cannot optimize physical sensor placement. Candidate sets retain all three regions. Pressure and timing observations are competing explanations; a nearest outlet template is not an inferred leak.

## Hierarchy and evidence limits
The streaming alert and formal result have separate interfaces. An alert can be issued while diagnosis remains UNRESOLVED. Retrospective candidate ranks require paired source templates and controlled anchors and are not a deployed provisional classifier. There are zero verified independent generating families. Qualified specific decision latency, risk–coverage, independent mechanism or location recognition, and model transfer are unestablished. The 12 formal outcomes stay UNRESOLVED, with zero qualified exclusions and L0. Exact joint set-membership equivalence under matched evidence remains the baseline. No added formal decision value was measured. Pressure-command change is an operational rival; equipment FAULT needs a verified failure state and mechanism. Timing issuance is not actuator DELAY, which needs a synchronized command/response record and nominal lag. The existing independent manifest gate remains the route to admitting future roots; source qualification and independent partitions precede a new simulation campaign.

**Poster result.** One- or two-second EWMA decisions detected 31 of 48 archived events within 10 s, with 42 false starts versus 16 for the frozen 120 s forest which detected more events overall. Hypothetical noise caused persistent alarms. Flow channels supplied much of the controlled three-location contrast. Formal diagnosis still abstained on all 12 accepted captures.

## Reproduction
From the repository set PYTHONPATH to src, then run:
```powershell
.\.venv\Scripts\python.exe -m h2prism.sequential_replay '<workspace>' '<fresh-output>'
.\.venv\Scripts\python.exe -m h2prism.sequential_figures '<fresh-output>'
```
