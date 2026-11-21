# H₂-PRISM causal monitoring validation

The historical five-model benchmark remains frozen. Its 702 replayed prediction rows describe an oracle-onset recognition experiment. This run is a separate retrospective replay with a causal, fixed-clock schedule. It uses archived observations as available up to each decision and archived labels only to train or score the binary target. The first decision is at the first stored timestamp plus 4 s. The five 1 Hz samples end at the decision timestamp. Stride is 120 s. A brief event can start and end between decisions. All pre-event and other inactive decisions are scored as negatives. Event recall counts an event only when a predicted positive occurs at an active decision knot, including events with zero eligible positive knots in the denominator. Delay is reported for detected events only.

## Provenance and evaluation boundaries

The clean source bytes were checked against the archive manifest. Noisy counterparts remain graph provenance. Neither noisy counterparts nor the ten controlled Center captures enter training. The two 2,500-sample near-prefix links from the independent audit are merged conservatively. The graph identifies unknown producing ancestry explicitly. Group-disjoint replay is a retrospective component-level proxy; the number of confirmed independent external training and test families is zero. No operating-profile, topology-family, independent simulation-domain or industrial field transfer is established. Controlled SID 213 alternate-profile results remain within-family sensitivity.

All learner preprocessing is fitted inside each outer training split. Binary prevalence is evaluated with an always-event rule and the training-fold majority rule. The logistic, forest, XGBoost and SVM settings are predefined. There is no selection against the held-out scores and no calibration. Temporal and metadata leakage traps deliberately alter future values and label columns, introduce wrong channel names, inject clock jitter and remove input channels.

## Results

Nine held-out conservative components covered 51 archived scenarios and 8,517 decision knots, including 6,519 event knots and 1,998 inactive knots. Each fit used 39–48 scenarios in eight components. No generating-run independence is verified. Metrics below weight decision knots and do not treat them as independent replicates.

| Model | Balanced accuracy | Inactive false positives / 1,998 | Detected events / 48 |
|---|---:|---:|---:|
| Majority / always event | 50.00% | 1,998 | 48 |
| Logistic regression | 82.45% | 199 | 42 |
| Random forest | 87.89% | 214 | 48 |
| XGBoost | 77.40% | 495 | 42 |
| Linear SVM | 85.22% | 31 | 37 |
| RBF SVM | 80.21% | 67 | 30 |

Random forest captured 39/39 annotated LEAK events, 6/6 FAULT and 3/3 DELAY, with median delays of 84, 399 and 99 s among those detections. Linear SVM captured 28/39, 6/6 and 3/3, with median delays of 84, 99 and 99 s. This is binary event capture stratified by annotation; it does not measure recognition of each class. Random forest reduced false-positive decisions relative to the trivial rule while matching its event capture on these cases. Linear SVM traded fewer false positives for more missed events. These comparisons do not qualify a model for deployment or establish superiority in a new domain.

At the assumed white-noise scale, balanced accuracy fell from 87.89% to 69.68% for random forest and from 85.22% to 44.84% for linear SVM. Under correlated noise those values were 67.99% and 45.18%. These stress results show failure sensitivity and no evidence of safe abstention. Median observed batch prediction times ranged from approximately 2.6 ms for logistic regression to 299 ms for RBF SVM over variable-sized held-out components; this is not an online per-sample latency bound. Memory usage and field throughput were not qualified.

## Stress and interface scope

Held-out sensor perturbations test 1% white noise relative to the initial absolute reading, correlated noise with 0.8 lag coefficient, drift reaching 2% of the initial absolute reading, a stuck PS1, and PS1 arriving 2 s late. The reused seed defines a repeatable stress realization; the scales are hypothetical. Invalid-input gates reject missing channels, incompatible declared units, ambiguous mapping, nonfinite samples and unsupported sample clocks. Explicit conversion handles stated pressure and mass-flow units. Valid declared units do not prove that units supplied by callers are truthful. The mapping adapter can map another named sensor layout only when it provides equivalent observables. Changed physical sensor roles, sampling rates or unsupported domains require qualification and possibly retraining. OOD detection effectiveness and safe statistical abstention remain unestablished.

## Decision, localization and deployment gates

No model is selected for deployment. All are EXPLORATORY. The recorded formal decision result remains 10/10 UNRESOLVED with L0. Formal consistency uses qualified measurement and prediction evidence; classifier confidence cannot fill the gaps. Calibrated abstention and matched-coverage comparison require independent calibration and test populations. The archive and controlled studies supply no independent leak-location test families and no qualified rival-location exclusions.

A confirmatory study needs distinct producing-run identifiers and original initial states, boundary and event records; independent NORMAL, LEAK, FAULT and DELAY families represented in each required partition; adequate independent cases per localization candidate; a separately reserved external test set; traceable units, clocks and error bounds; operating regimes and sensor configurations relevant to the deployment envelope; and a documented invalid-input, drift, and fallback policy. Test industrial operating-hour false alarms, latency budgets and hardware capacity on independently logged representative streams. This package provides no field false-alarm guarantee, deployment claim or independent overfitting finding.

## Reproduction

From the repository, with the recorded dependencies and XGBoost available on PYTHONPATH:

```powershell
.\.venv\Scripts\python.exe -m h2prism.phase13_monitor '<phase13_independent_audit>' '<new-output-directory>'
```

Raw classification counts, per-case event summaries, split membership, timing, and provenance are in the associated CSV and JSON artifacts.
