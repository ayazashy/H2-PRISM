# H₂-PRISM baseline freeze and external validation readiness

## What is frozen

The controlled baseline is **B3 time-aligned matched residual distance**. Keep the full competing-mechanism library as an exploratory comparator. NRES is retained as an equivalent decision baseline in this experiment, with no incremental rank improvement. Its different weighting is not algebraically identical to B3. The additional mechanism eligibility gate is **not adopted** following REVISE_OR_REJECT. Its failures, all failed-run evidence and the untracked MATLAB backup are preserved.

The freeze checked all 12 accepted Center runs against their receipts (**84 capture-file checks**). Derived model, design and preflight hashes, approval records, pinned source copies, archived clean/noisy assets, benchmark implementation files and the selected output bundles are linked in the **410-file** checksum inventory. The clean/noisy archive counterparts are provenance, not separate independent samples. The **12 runs share one Center source family**. Verified independent generating families remain **zero**.

## Strongest quantitative findings

- **Controlled source physics.** The timing pair retains the 3.0 to 6.4 MPa command and its outlet setting. Emitted and received events land at 25 and 26 s. Clock-aligned 30 s RMS **0.027781** fell to **0.000121924** after retrospective event alignment, about **228×**. B3 and NRES selected the same shift in the fixed-window experiment.
- **Detector trade-offs.** Frozen 120 s causal playback recorded forest **48/48** new detected events and **16** false starts, versus linear SVM **37/48** and **2**. Both used **65.6283 inactive archive hours**. At 1 Hz, reference EWMA detected **39/48**, with **30/48** by five seconds and **42** false starts. Under assumed white noise, capped CUSUM recovered **35/48** with **45** false starts while reference EWMA had **0/48** and **51**, remaining open over 99.9% of observed time. CUSUM generated **226** false starts under correlated noise. No field operating point was selected.
- **Historical ML.** XGBoost's **39/39** LEAK recall tied a constant LEAK rule. Every held-out case in that benchmark was LEAK. The causal binary benchmark avoids oracle-onset feature selection, but archived ancestors are unresolved. Diagnostic accuracy across four classes is unestablished.
- **Location and mechanism.** B3 and NRES both ranked nominal SID 213 first in **560/560** settings on one examined alternate-profile observation. Removing MFS3 reduced the full-library margin **0.028358 → 0.000141**. A full mechanism library prevented forced-location interpretations in the focal comparison, but **164/1,792** non-withdrawal sensitivity settings still routed the same timing observation. The extra gate prevented only one wrong route beyond full-library nearest-mechanism ranking. These settings are not independent evaluation units.
- **Formal outcome.** **12/12 UNRESOLVED, zero qualified exclusions, L0.** Exact joint set-membership equivalence under matched evidence is unchanged. Incremental distinguishability benefit, independent localization accuracy and matched-coverage selective risk remain unestablished.

## External adapter and claims gate

The example is a **synthetic second-schema portability fixture**. It converts a separately named kPa pressure column, g/s signed flow with defined polarity, and ms clock to MPa, kg/s and seconds. Its first reading is **0.21 MPa and −0.02 kg/s**. The adapter returns ordered telemetry and timestamps only; event and ancestry annotations stay in the scoring manifest. It supports optional topology metadata and explicit missing values. Declared clock step and unit/role mappings are checked rather than inferred. Declared column names do not prove physical semantics. Near-duplicates and producing-run independence still require source review.

Development, calibration, and untouched test are separate read interfaces. The untouched test interface is sealed by default; unsealing is an explicit steward action, not filesystem access control. Run qualification under the steward, separately from learner access. The checker verifies raw hashes, canonical manifest binding, reviewed label receipts, root/family/checkpoint/duplicate-history partition separation, and reviewed class/location minima. A passing claim means eligible for external scientific review only. It does not establish the claim. An out-of-band pinned review registry is required for admission. The fixture blocks **multiclass, localization, calibration, formal and incremental value**.

A deployment reference must be available prospectively through a qualified nominal model or past-only data with valid operating context. The matched experimental control is never substituted by the operational reference interface. Status remains **BLOCKED_REFERENCE / UNRESOLVED**. Preserve the baseline while obtaining independent evidence.

## External acceptance before fit or test

Collect traceable independent producing families, with separately identified development, calibration and untouched test roots. Review source lineage, shared checkpoints, scenario history and reported mechanisms. Require class support for NORMAL, LEAK, FAULT and DELAY in all relevant partitions. A FAULT needs observable equipment state and source-qualified intervention and response. DELAY needs a synchronized issued command, actual actuator response and justified nominal lag. Location evaluation must predeclare candidate regions and independently substantiate actual leak sites. Fix acquisition clock, causal windows, alarm definitions, uncertainty method and paired comparisons before unlocking evaluation. Derive independent family counts from prospectively agreed precision and operating targets; the fixture's tiny row count establishes no minimum.

For incremental distinguishability, compare the same observations and hypothesis universe with classifier alone, eligibility-calibrated abstention and the formal method. Require attained **nonzero matched specific coverage**, denominators, paired uncertainty, false alarms, event-delay and class/site errors. Formal exclusion needs defensible simultaneous observation and prediction enclosures, including measurement, clock, initial/boundary, parameter, numerical and independently assessed model discrepancy. External topology transfer requires its own untouched topology and qualified mapping. No field deployment claim follows from software portability.

**Poster Methods.** Freeze matched residual comparators and test event timing, sensor ablation and operational rivals in one source-derived gas-network family. Keep historical causal replay separate and count alarms as episodes.

**Poster Results.** Time alignment explained the large command-shift contrast. Mechanism screening prevented some forced location assignments and failed on timing-sensitive conditions. Exactly 12 of 12 formal outcomes remained unresolved. Separate independent calibration and test evidence is required for scientific transfer.

## Figures

![Timing and baseline comparison](timing_and_baselines.png)

![Mechanism routing and reference feasibility](routing_and_reference.png)

![Detector trade-off under clean and correlated-noise replay](tradeoffs.png)

## Reproduction

From the repository with PYTHONPATH=src. Replace the paths in angle brackets. Use a fresh file for qualification, which exits nonzero on blocked claims.

```powershell
.\.venv\Scripts\python.exe -m h2prism.baseline_freeze '<repo>' '<workspace>' '<baseline_manifest.json>' --verify
.\.venv\Scripts\python.exe -m h2prism.external_readiness '<second-dataset-root>' '<dataset-manifest.json>' '<fresh-result.json>' --review-registry '<reviewed.json>' --registry-sha256 '<independently-pinned-digest>'
```

For the synthetic fixture omit the review registry options. A blocked report is the expected result. See external_acceptance.json for the specific evidence categories and partition requirements.
