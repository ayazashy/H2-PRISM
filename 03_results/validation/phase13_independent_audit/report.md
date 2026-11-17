# Independent audit of the frozen Phase 13 benchmark

## Findings and verdicts

| Check | Verdict | Evidence |
|---|---|---|
| Frozen prediction replay | PASS | All 702 rows matched across models and variants. Settings, versions, seed, inputs and folds also matched. |
| Known partition links | PASS | Zero scenario/component overlaps and zero crossing edges in the reconstructed graph across all 10 folds. It checked 57 clean trajectories and 57 paired noisy assets. |
| Full trajectories and actual evaluation windows | PASS for the stated screen | Across 1,143 distinct cross-component pairs, neither exact duplicates nor distances at or below 0.1% were found. Minimum full/window distances were 0.568% and 0.655%. |
| Shared pre-event history | INCONCLUSIVE | Eight distinct pairs crossed components below 0.1%. Two LEAK pairs (Center G4 strong/weak against G6) shared 2,500 near-identical pre-event samples and crossed scored folds. This is new evidence of possible dependence; original producing state is unavailable. |
| Train-only learned preprocessing | PASS | Scalers fitted on training partitions, with explicit holdout perturbation tests. No evidence of test observations entering fitted transformations. |
| Genuine real-time event detection | FAIL | Ground-truth onset chooses the event window; its final sample is four seconds later. This is demonstrated oracle information use for a real-time claim. |
| Confirmatory multiclass performance | FAIL | All 39 scored test cases are LEAK; the test folds already informed repeated exploratory analyses. |
| Demonstrated overfitting | INCONCLUSIVE | Removal sensitivity and some in-sample gaps show instability. No independent multiclass comparison establishes overfitting. |

The always-LEAK rule scored 39/39. The onset-only logistic control scored 30/39, exactly the same aggregate recall as sensor-feature logistic regression. That demonstrates a useful proxy on this restricted test; it does not establish per-case agreement or that the sensor models directly consumed the anchor. Block-permutation runs retained 30–34/39 hits for XGBoost, 26–30 for random forest, 19–24 for logistic regression, 18–21 for linear SVM and 16–24 for RBF SVM. Some draws left many labels unmoved; the three draws changed 102–144 training labels summed across folds. High control recall shows why these scores cannot separate learning from class prevalence.

Random forest had 100% in-sample accuracy averaged over folds and 36/39 held-out LEAK recall. This compares different class mixtures, and the like-for-like LEAK comparison also has limited test support. A single added component removal drove linear SVM fold recall down to 0%; other valid removals yielded up to 100%. XGBoost retained 100% on all 56 valid removals, which is also attainable by a constant LEAK rule. The two newly flagged long-prefix pairs should be held together in any further retrospective sensitivity work until source provenance resolves them. The frozen benchmark and reported scores are preserved.

## Preprocessing and information boundary

The archived event class and onset determine the extraction window. For NORMAL the anchor is fixed at 1,000 s. The feature vector has five one-second observations from onset through onset + 4 s and contains means, standard deviations, slopes, and endpoint differences. Any prediction timestamped at onset would therefore use four future observations. The valid interpretation is retrospective oracle-onset recognition with a decision no earlier than the last sample. The benchmark provides no detection latency, false-alarm, or continuous monitoring estimate.

Scenario and group IDs and the anchor are absent from the ordinary feature columns. Archive filenames and event annotations enter source lookup and eligibility. The shared pressure/flow channel list came from intersecting schema availability across the complete candidate archive. That is global schema discovery, with no evidence that it used held-out values or labels to optimize the channel list. An independent evaluation should freeze the sensor schema prospectively. Per-window calculations and finite-value exclusion use only that case. Scaling for logistic regression and both SVMs is fitted on each training fold. Tree models use the unscaled inputs. Class weights are training-only. Imputation, dimensionality reduction, learned feature selection, and probability calibration are absent. The settings and ablations are predefined. Valid inner group holdouts support only LEAK, so no nested four-class tuning is justified.

## Scope of negative controls

The constant control exposes the class-support limitation. The metadata control uses the window start alone and tests an available proxy for the extraction policy. Its score has no false-positive denominator. Label permutation exchanges ordered class-label blocks only among equal-sized training components, preserving training class counts and excluding test labels. The archive has few exchangeable heterogeneous blocks, and repeated draws can be partly unchanged. The permutation runs are stress tests and do not imply a valid significance test. Component removal retains the frozen test fold and omits results when an additional removal eliminates a training class.

Exact and near-trajectory checks compare the 16 model channels at matching archived clocks. Distance is RMS of pointwise differences divided by the larger full-trajectory RMS for each channel. The 0.1% threshold is a descriptive screen. Whole-series, aligned event windows and common pre-event prefixes are distinct checks. Different clocks, unobserved state, time-shifted histories, and unknown producing-run ancestry limit the inference. Clean and noisy variants are checked by asset digest and documented links. No noisy file was used as a separate scored observation.

## Minimal fixes for a new evaluation

Use scenario-independent event detection or a prospective fixed observation schedule. Freeze sensors, decision timestamp and evaluation rules before opening the test set. Obtain producing-run ancestry and independently generated components with every class supported across train, calibration and test. Treat the repeatedly inspected Phase 13 folds as development evidence. Keep a constant predictor and group-wise negative controls. Do not interpret in-sample fit or LEAK-only recall as four-class performance.

## Reproduction

From the repository, with the same versions recorded in the benchmark JSON and the isolated XGBoost dependency on PYTHONPATH:

```powershell
.\.venv\Scripts\python.exe -m h2prism.phase13_benchmark '<previous-ml-output>' '<new-replay>'
.\.venv\Scripts\python.exe -m h2prism.phase13_audit '<previous-ml-output>' '<original-benchmark>' '<new-replay>' '<new-audit>'
```
