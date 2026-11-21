# H₂-PRISM decisive exploratory study

## Triage and methods
Executable now: reproduce event-level reference results, validate alarm state transitions, and recheck the existing source and provenance gates. Exploratory only: detector comparison, alternate alarm policies, sensor ablation, causal-prefix templates, timing sensitivity and physical plausibility. Blocked by evidence: independent diagnosis or localization, calibrated selective risk, qualified formal bounds, and external transfer. New supervised mechanism training is ineligible with one controlled source family and zero verified independent generating families. The frozen oracle-onset and causal ML outputs retain their previous scope.

All new scores use only canonical 1 Hz sensor observations and four seconds of history. At each time, an innovation is the signed four-second change divided by the larger of the existing engineering reference scale and four times the median absolute one-second increment over the preceding 31 samples. This quantifies recent noise rather than fitting a nominal physical trajectory. It can adapt during an event and could absorb persistent changes. No adaptation-freeze variant was evaluated. No global scaler, archive event label, intervention ID or hidden command enters inference.

The bounded accumulator clips each standardized magnitude above one to the range 0–3 and EWMA-smooths each channel separately (new weight 0.25). It sums the three strongest channel memories so evidence need not arrive simultaneously. It opens above 2.5, resets at or below 0.6. A two-stage variant requires two consecutive opening decisions and three consecutive reset decisions. Suspicion and confirmed alarm are separately scored. The capped CUSUM uses the maximum-channel standardized innovation, reflected at zero, caps each input at 4, subtracts fixed drift 1.5 and caps accumulated evidence at 20. It opens above 8 and resets at or below 2. These are fixed, engineering exploration settings. No reference distribution or IID false-alarm guarantee is asserted. Invalid scores reset the state, return SENSOR_INVALID and require fresh confirmation. The existing sensor interface rejects missing fields and discontinuous clocks before scoring. No fallback inference, field unit qualification or numeric performance under invalid schemas is claimed.

The comparison uses 51 archive runs, 48 annotated events, nine conservative components and 65.6283 inactive archive hours. The event denominator includes missed events. A new confirmed alarm must begin inside an annotated interval; already-open alarms receive no credit. Delay quantiles condition on detections. Open episodes end at the last observed knot for duration accounting. Noise, bias, drift, a stuck PS1 and delayed PS1 retain the previous hypothetical realizations. Sensor dropout and timing jitter have validity checks rather than inferred event outcomes. Frozen forest and SVM and trivial rules are comparators at 120 s and are not treated as equally sampled latency experiments.

## Evidence sufficiency and localization
The alternate-profile SID 213 query is omitted from the template library. Its first eligible late-scope causal alert is at 1,000 s. The timing experiment delays the ranking anchor by 0, 1 or 2 s from that alert. Templates can shift by 0, ±0.2, ±0.4, ±1 or ±2 s on the 0.2 s grid. ±0.4 s is the largest integer-knot shift within ±0.5 s; there is no interpolation. Observed prefixes end at the reported decision time. Reference subtraction requires the contemporaneous matched control and is a research-only resource. Source anchors apply to library templates, never query onset. Self-template rows are flagged and supply no validation.

Nominal SID 213 ranked first in all 1,440 alternate-profile comparisons, including sensor removal, timing tolerance and delayed alert. At a 30 s prefix and ±1 s tolerance, the normalized all-sensor margin is 0.028358; removing MFS3 reduces it to 0.00014104. The pressure-only and flow-only margins are 0.00002314 and 0.059032. At the initial knot, the pressure runner-up changes from SID 215 to the timing rival and then the pressure rival as alert delay goes from 0 to 1 to 2 seconds under ±0.4 s tolerance. The controlled timing pair's earlier 228-fold contrast reduction after event alignment shows why time can dominate apparent difference. SID 215 had no eligible late alert, so no late prefix was manufactured. The pressure rival is retained and near matches are not interpreted as leaked gas. These results identify MFS3 as a useful measurement for this contrast, not an optimal new placement or a certified margin. All three locations remain in the candidate set.

Signed boundary-flow and storage consistency are verified offline in the accepted simulator captures. Those quantities are not available as deployed inference features. No arbitrary plausibility cutoff or certification was added. The existing qualified engine and exact joint set-membership comparator remain unchanged. Formal counts are 0 Specific, 0 Ambiguous, 12 Unresolved, no qualified exclusions, and L0. **NO DEMONSTRATED FORMAL DECISION IMPROVEMENT.** Calibration and matched-coverage selective-risk comparison remain blocked.

The source qualification still lacks an equipment failure state and traceable physical mechanism for FAULT, and a synchronized issued-command/actual-actuator response with nominal lag for DELAY. Independent root histories, separate calibration and untouched test partitions, qualified sensor and timing error, and simultaneous model enclosures remain necessary. No new simulation, training, or deployment selection is justified by this sprint.

## Detection results

| Clean 1 Hz detector | New alarms / 48 | Within 1/2/5/10/30/60/120 s | False episodes / h | Duty | Median / p90 / p95 / max delay (s) |
|---|---:|---|---:|---:|---|
| Frozen EWMA | 39 | 29/29/30/31/31/31/31 | 42 / 0.640 | 2.325% | 0 / 1500 / 3295.6 / 19507 |
| Bounded accumulator | 32 | 10/19/28/29/29/29/29 | 45 / 0.686 | 0.425% | 2 / 5.9 / 1503 / 1505 |
| Two-stage | 31 | 0/9/25/28/28/28/28 | 45 / 0.686 | 0.433% | 3 / 7 / 1504 / 1506 |
| Capped CUSUM | 34 | 0/0/31/31/31/31/31 | 96 / 1.463 | 0.682% | 3 / 4 / 1503 / 1503 |

All 357 reference scenario-condition rows reproduced the saved counts and delays. Under clean data, all three candidates missed all three archived DELAY annotations and none of the six FAULT annotations. Those are retrospective binary scores by annotation, not qualified mechanism diagnoses. The two-stage rule reduces rapid event starts without reducing clean false episodes relative to its one-stage score. Shorter delay quantiles on detected events are conditional on increased misses. The combined batch computation averages 29.38 microseconds per clean row across scenarios, excluding acquisition and intervention latency. This measures scoring and alarm calculations together, not a runtime guarantee.

Under hypothetical white noise, EWMA had 0/48 new starts, 51 false episodes and >99.9% duty. Capped CUSUM had **35/48**, 45 false episodes and **0.324%** duty. Under correlated noise CUSUM had 48 new starts with **226** false episodes and **10.845%** duty. The accumulator measured **31/48**, 52 false episodes and **0.178%** duty under correlation. Two-stage reduced this to 26/48 with 49 false episodes. It had 30 suspicions under correlation, illustrating the gap between suspicion and confirmation. A high event count alongside a high false count is insufficient evidence of acceptable detection or physical mechanism recognition.

The original noise failure is persistent alarm state, not rapid chattering: the EWMA was still open at the last knot in all 51 runs under each of the two noise stresses. Under correlation, CUSUM substantially reduced persistent occupation but introduced repeated starts. Episode and transition logs preserve durations and reset reasons. Evaluated variants jointly change scaling, accumulation and thresholds; effects are not isolated to a single cause. Per-event signed innovation peaks and simultaneous versus union channel counts are recorded without assigning physical causes from detector outcomes. Nominal operating commands can explain controlled-trace alerts where the commanded event is recorded, but no hidden command was used to label archived false starts as faults.

The frozen 120 s random forest remains the eventual-capture reference (48/48 and 16 false starts), and linear SVM remains the low-false-start reference (37/48 and 2). The majority and always-event controls are continuously positive during the events but score zero new in-event starts. Cross-cadence comparisons are explicitly marked in the matrix.

## Closure
**A justified exploratory detector improvement was observed** under the tested hypothetical white-noise replay. No overall operating point was established: no new candidate preserved the full clean recall and false-start trade-off, and correlation can turn saturation into repeated alarms. Freeze and close the current exploratory study. Any later qualification must start from new independently generated roots and qualified mechanisms rather than tune against this reused archive.

**Poster text.** At 1 Hz, a fixed capped CUSUM broke white-noise alarm saturation and recovered 35 of 48 annotated events. It incurred 226 false episodes under correlated noise. In a separate matched Center comparison, restoring MFS3 increased the alternate-profile outlet ranking margin substantially. Formal diagnosis abstained on all 12 captures.

## Reproduction

Set PYTHONPATH to src from the repository. Use fresh output paths. Copy the ranking run's prefix_ranks.csv into the sprint output as delayed_prefix_ranks.csv before rendering.

```powershell
.\.venv\Scripts\python.exe -m h2prism.decisive_sprint '<workspace>' '<fresh-output>'
.\.venv\Scripts\python.exe -m h2prism.causal_prefix_ranking '<workspace>' '<fresh-ranking>' --alert-delays 0 1 2 --offset-steps 0 1 2 5 10
.\.venv\Scripts\python.exe -m h2prism.decisive_figures '<workspace>' '<fresh-output>'
```
