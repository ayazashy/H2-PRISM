# Frozen causal replay alarm validation

## Completed offline
Replayed the frozen 357,714 decision rows through one unchanged alarm policy for seven models and six conditions. Reopened and checksum-verified each of the 51 clean archives, checked contiguous source labels and matched every decision target against the annotated event interval. The 9 dependency components are retrospective split proxies. No estimator was fitted, tuned, or selected again.

Alarm policy: the first positive opens an episode, the first negative resets it. Carry open state across annotation boundaries. A distinct event detection requires a new alarm start in the active interval. Positive decisions within a pre-existing alarm are counted separately. Each scenario starts with no alarm. An episode starting inactive counts as false; an alarm already open when the event ends is not counted a second time. The exposure denominator is verified inactive time between the first and last decision, excluding warm-up and the unsampled tail. The active annotation covers one-second sample intervals through last-active plus one second. The rate describes retrospective, sampled archive replay, with no field-hours implication.

| Clean model | New detections / 48 | Missed LEAK / FAULT / DELAY | False episodes | False episodes per inactive hour | Median (range) new-alarm delay |
|---|---:|---:|---:|---:|---:|
| Random forest | 48 | 0 / 0 / 0 | 16 | 0.244 | 84 s (24–7,764) |
| Linear SVM | 37 | 11 / 0 / 0 | 2 | 0.0305 | 84 s (24–1,584) |
| Majority and always-event, each | 0 | 39 / 6 / 3 | 51 | 0.777 | undefined |

Each model saw 65.6283 verified inactive hours, over 51 scenario runs. The trivial controls were positive at active decision knots for 48/48 events while already in alarm. A false start after the annotated event cannot receive detection credit. See scenario, component, subtype, and quantile tables for the exact distributions.

## Exploratory stress
The frozen stress uses white noise at 1% of absolute initial per-channel readings, correlated noise using the same innovations with autoregressive coefficient 0.8, drift up to 2%, and PS1 stuck or delayed by 2 s. These settings are hypothetical. Correlated noise drove false episodes to 400 for forest and 230 for linear SVM; white noise drove them to 374 and 175. The largest recorded alarm-count degradation is repeated resets and new false starts under noise; the archived decisions do not identify hidden model mechanisms. Linear SVM reached 48/48 new starts under correlated noise while also generating 230 false starts. New starts alone are therefore unsafe to interpret. Stuck PS1 led to 43/48 new starts for forest and 18/48 for linear SVM, versus 48/48 and 37/48 clean. Delayed PS1 increased linear SVM false episodes from 2 to 17; forest counts stayed unchanged. Full-channel stress isolation, sampling-rate transfer and missing-sensor diagnostic performance were not measured by the frozen predictions; missing inputs are rejected by the existing input gate.

## Blocked and not established
Independently verified generating families: NORMAL 0, LEAK 0, FAULT 0, DELAY 0. Archive annotations have 3, 39, 6, and 3 scenarios respectively. Holding out the archive NORMAL component removes every NORMAL scenario from training; holding out the FAULT/DELAY component removes those classes. Causal binary grouped playback is admissible as exploratory, with ancestry unresolved. All ten controlled captures share one Center family. SID 213, 312 and 215 are configured candidates, with zero verified independent location families. Near-prefix links were conservatively merged for the causal benchmark. Independent multiclass performance, calibration, matched-coverage risk and topology transfer remain unestablished.

The experimental specification fixes source records, root grouping, partition roles, prerequisites, metrics and ordered experiments. Start with independent in-domain runs across the supported four classes and location regions; qualify instrument and model bounds in parallel. Hold new conditions and topologies for distinct transfer experiments. Coverage across classes is an admission requirement; determine precision and family counts prospectively using assumptions supported by an independent pilot. The admission script checks structural support and crossing identifiers; review the cited receipts and source evidence before scientific acceptance.

Formal readiness requires traceable observation and clock error, independently constrained initial and boundary states, source-compatible prediction enclosures including discrepancy and numerical error, and verification over the stated domain. Numerical convergence and hypothetical perturbations are useful for sensitivity only. Preserve INDETERMINATE, UNRESOLVED and L0. No new MATLAB simulation was run.

## Reproduction

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m h2prism.phase13_alarms '<frozen-causal-results>' '<new-alarm-output>'
.\.venv\Scripts\python.exe -m h2prism.phase13_independent_design '<candidate-manifest.json>'
```

The candidate manifest takes records and regions arrays. Use the experiment specification for record fields. The admission script returns nonzero for blocked manifests. No frozen output is overwritten.
