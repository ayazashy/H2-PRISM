# Causal diagnosis intelligence and forensic replay

## Methods and evaluation scope

The 51 checksum-verified archived scenarios carry 48 annotated events and 65.6283 common inactive archive hours. The source history audit still identifies zero verified independent generating families. This study reused identical 1 Hz decision clocks, false-episode definitions and replay stress conditions. Onset is used after prediction for scoring. A positive starts an alarm, subject to the selected state rule, and an already-active alarm earns no event credit.

The reference is the previously frozen maximum four-second normalized sensor change with EWMA (new weight 0.25, opening above 5 and closing at 2 or below). The comparison computes a per-channel scale as max(reference floor, four times the median absolute one-second increment over the preceding 31 samples). The fourth-largest standardized four-second change replaces the single-channel maximum, requiring support from four channels before smoothing. This trailing nuisance estimator continues during alarm; it is not a learned NORMAL model and may absorb persistent changes. The stateful variant adds two consecutive opening and three consecutive reset decisions, with explicit suspect, active and recovery states. This joint normalization-and-corroboration comparison does not isolate the individual effects. No candidate was retuned against evaluation labels.

## Detection and failure mechanisms

| Clean, 1 Hz | Total / 48 | Within 1 / 2 / 5 / 10 / 30 / 60 / 120 s | False starts | Rate per inactive hour | Alarm duty |
|---|---:|---|---:|---:|---:|
| Reference EWMA | 39 | 29 / 29 / 30 / 31 / 31 / 31 / 31 | 42 | 0.640 | 2.325% |
| Robust scale + corroboration | 2 | 0 / 2 / 2 / 2 / 2 / 2 / 2 | 0 | 0 | 0.00492% |
| Robust stateful | 2 | 0 / 0 / 2 / 2 / 2 / 2 / 2 | 0 | 0 | 0.00512% |

The replay matched the reference false counts, new detections and first detection times on all 357 scenario-condition rows. The 30 fast clean detections were new starts within five seconds. Nine other events were detected later. Seven of those had an EWMA maximum below the opening threshold in the first five seconds; two were already in alarm at onset and did not restart until near the end. Of nine never detected, eight had no in-event threshold start and their maximum active score was at most 0.807. One was already in alarm and never restarted in-event. These findings identify weak response **for this statistic** and state masking. They do not establish physical blindness, a bad label or an exact sensor fault. The early instantaneous driver is logged separately from the multichannel EWMA memory.

The reference had 51 false starts with either white or correlated noise and was already open at all 48 annotated onsets, with duty over 99.9% and zero new detections. The robust stateful candidate had zero false starts in both modes but detected only 1/48 white and 2/48 correlated. Confirmation delayed clean detections from 2 s to 3 s. The clean robust count of 2/48 makes replacement scientifically indefensible. Tested PS1 bias, stick and delay and MFS1 drift left that count unchanged. Hypothetical stress is not field robustness. Forest and linear SVM remain frozen 120 s references with different decision schedules; no cross-cadence winner or operational threshold was selected.

## Causal prefix ranking and conditional location

The experimental ranker forms same-time residuals against an available matched reference and evaluates only samples already received by the decision deadline. Library templates use controlled simulator anchors; observation queries use the first causal alert in predefined startup (from 0 s) and late (from 200 s) monitoring scopes. Scores are normalized RMS over an observed prefix, minimized only over template offsets 0, ±1 or ±2 s on the 0.2 s grid. Per-subset ranks, margins, deadlines, self-template markers and candidate sets are saved. The paired reference is research-only and would need a prospective operating reference in deployment. These are RETROSPECTIVE_EXPLORATORY rankings.

All early alerts except the timing intervention began at the ordinary pressure transient at 25 s; timing began at 26 s. In the late scope the alternate profile, SID 213 and SID 312 alerted at 1,000 s, pressure rival at 1,002 s, and SID 215 did not alert. Ranking after a missing alert was not fabricated. The alternate-profile query was excluded from the template library. At its 1,000 s alert, nominal SID 213 ranked first with all, pressure or flow sensors and ±1 s timing tolerance, and remained first through 30 s. At the first knot the all/pressure/flow margins were 0.02836/0.00001151/0.05904. At 30 s they were 0.02836/0.00002314/0.05903. This illustrates greater flow leverage and timing/sensor dependence of rival order, without establishing location accuracy. Other rows include self-template checks and are explicitly marked; their top ranks are not validation. SID 213, 312 and 215 remain in the candidate set. The earlier 228-fold clock/event-alignment contrast remains the direct timing-uncertainty warning. An assumed offset tolerance or residual margin is not a qualified enclosure.

## Interface, formal evidence and next data

The versioned one-row runtime implementation matches the causal prefix-equivalent batch score and state transitions. Data checks cover ordered names, numeric shape, finite values and contiguous 1 Hz times. Invalid data returns SENSOR_INVALID and UNRESOLVED without advancing state; an interrupted stream requires explicit fresh warm-up. Unit conversion and named sensor mapping must be checked by the existing adapter before queuing canonical MPa/kg/s values. This study does not implement fallback inference on invalid or missing sensors. The bounded numeric history has five 16-channel samples and 31 increment rows plus the scale vector (4,736 bytes of numeric values, excluding object overhead and scratch allocations). A separate 20,000-row archived NORMAL run measured median/p90/p99 update times of 104.7/178.0/442.7 microseconds on this machine. Acquisition latency is unknown, feature span is four seconds, and confirmation adds one saved sample to a sustained crossing. The timing results do not establish subsecond detection.

Twelve accepted controlled captures still yield zero specific and zero ambiguous formal decisions, all UNRESOLVED/L0. No qualified exclusions, calibration, matched-coverage selective risk or added formal decision benefit is established. The formal engine retains its equivalence to exact joint set membership with identical evidence. Qualified multiclass training remains blocked: pressure command is an operational rival, and timing issuance is neither actuator lag nor compressor failure. The smallest next source qualification is a measurable equipment state with traceable failure intervention and synchronized nominal/altered actuator response. Independent four-class and per-location roots, disjoint calibration, untouched test, physical measurement/clock bounds and simultaneous predictive enclosures are required. No new MATLAB run or ML training was executed.

**Poster result.** Archive forensics separated weak detector response from persistent pre-event alarms. A robust four-channel policy broke noise saturation at the cost of detecting only 2/48 clean events. A held-template alternate-profile comparison favored nominal SID 213, while formal localization remained L0.

## Reproduction

Set PYTHONPATH to src from the repository. Use a fresh output directory for the first command and a second fresh directory for ranking. Copy the two rank CSVs into the replay directory before rendering.

```powershell
.\.venv\Scripts\python.exe -m h2prism.causal_intelligence '<workspace>' '<fresh-replay>'
.\.venv\Scripts\python.exe -m h2prism.causal_prefix_ranking '<workspace>' '<fresh-ranking>'
.\.venv\Scripts\python.exe -m h2prism.causal_intelligence_figures '<combined-results>'
```
