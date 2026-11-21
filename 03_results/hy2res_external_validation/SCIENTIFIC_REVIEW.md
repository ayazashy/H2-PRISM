# Study C scientific review

Reviewed Faisal's local GitHub tracking snapshot at `abed1c1c01fe0791edc19e1b3d0d7e0273859654`. Live GitHub HEAD could not be confirmed. Reviewed the bundled approved plan and replayed the notebook code cells in order in an isolated copy using Python 3.12.1, pandas 2.3.3, NumPy 2.3.1, scikit-learn 1.7.0 and Matplotlib 3.10.7. Replay matched the archived predictions, split, masks, segment IDs, selection and metrics within floating-point tolerance (absolute 1e-7, relative 1e-8 for numeric table values). Independent aggregation of the archived predictions and validity mask agreed with all 40 held-out metric rows, including undefined errors for empty strata.

## Approved-plan coverage

| Gate | Review |
|---|---|
| F1 — Source | Verified the file against Zenodo v1 DOI 10.5281/zenodo.15166733, CC BY 4.0. The 38,621,947-byte file matches official MD5 `9a3c3e3b1668596854b43bfd790d3e0e`. It contains 300,768 rows and 23 columns. Pressure is in bar, equipment power in W, and H₂ flow in NL/h. Electrolyzer flow is the normalized volumetric production rate over the preceding interval. Tank pressure is `pres_comp`. |
| F2 — Causal segments | All timestamps parsed and were nondecreasing, with timezone unspecified. Of 300,767 intervals, 297,975 were exactly 5 s, 21 were zero, 32 were positive and shorter than 5 s, and 2,739 exceeded 5 s (four exceeded 60 s). There were 20 paired OPEN/CLOSE markers. The 2,793-segment rule starts afresh at OPEN, after CLOSE, and at every irregular step. It preserves all rows and uses no interpolation. |
| F3 — Target and split | Five 5-second-ahead targets. Chronological development, validation, embargo and test contain 210,537, 44,396, 1,438 and 44,397 rows, respectively. The embargoes exclude target rows from fitting and scoring. Test forecasts can use earlier embargo measurements as causal context. The historical test-access seal and single-access claim lack independent verification. |
| F4 — Baseline and one extension | Persistence uses t−1. Per-target ridge (alpha 10) uses lags 1–3 of the five targets and three measured powers. Grouped shifts and explicit elapsed-time assertions constrain lags. Standardization and fitting use development for selection, then development plus validation for final fit. The fixed validation rule selected ridge at mean RMSE ratio 0.8784 across the three defined ratios. No future measurement enters the inspected features or fit. |
| F5 — Held-out comparison | Test spans April 12 12:13:56 to April 15 02:00:00, 2024, source clock. Both methods used the same 43,168 rows and 409 segments per target. Coverage is 97.234% of 44,396 observed rows for the two varying pressures and production flow, and 97.232% of 44,397 for the fuel-cell targets. Shared eligibility requires 24 finite lags and a finite target. |
| F6 — Evidence package | Committed source/schema/split records, archived predictions, masks and metrics, reports, and three figures in PNG/SVG/PDF. Inspected each original PNG at review size. The 300 dpi originals retain physical units and the fixed trace interval. F2 repeats constant traces, and F3 emphasizes RMSE and joins categorical states. The companion figure addresses the latter by displaying both error measures with unconnected markers and sample counts. |

## Held-out interpretation

| Target | MAE persistence → ridge | RMSE persistence → ridge | Assessment |
|---|---:|---:|---|
| Buffer pressure (bar) | 0.003964 → 0.005500 | 0.019909 → 0.017138 | MAE +38.8%, RMSE −13.9%. |
| Tank pressure (bar) | 0.025598 → 0.025141 | 0.050599 → 0.040698 | RMSE −19.6%, strongest aggregate gain. MAE improves by only 0.000456 bar (1.8%). |
| Electrolyzer H₂ flow (NL/h) | 0.032730 → 0.178005 | 1.256965 → 1.185259 | MAE 5.44× persistence, RMSE −5.7%. No uniform gain. |
| Fuel-cell pressure (bar) and flow (NL/h) | 0 → 0 | 0 → 0 | Constant zero throughout the source. No demonstrated skill under varying fuel-cell conditions. |

Electrolyzer-only power state accounts for 42,367 scored rows. Multiple-active state accounts for 801 rows in 12 segments. In that smaller state, ridge flow RMSE increases from 0.1347 to 0.6465 NL/h (4.80×) and MAE increases from 0.1036 to 0.5116 NL/h. Both pressure RMSEs improve there while both pressure MAEs worsen. State is determined by positive lagged power, so these are descriptive strata with serial dependence, limited support and no controlled transition or mechanism inference. Unknown-state rows contributed zero eligible forecasts.

The error comparison measures both methods on ridge's complete-case support. A standalone persistence reference could remain available with only a valid previous target and a continuous 5-second step. That wider availability is unmeasured by the frozen comparison. Missing targets or history yield unresolved reference evidence for scoring. An eligible row establishes forecast availability, with no calibrated uncertainty, residual validity bound, or alert policy. Low mean errors alone provide no evidence of alert performance or operational significance.

## Scientific scope and priorities

- **H₂-PRISM contribution.** The reference layer gains real-system evidence for causal one-step processing, coverage screening and descriptive prediction. The evidence layer gains explicit masks and exclusion reasons. The diagnostic and decision layers receive no validation of incident detection, fault or delay classification, certified D(Y) exclusions, or localization. There is no qualified incident truth or independent plant replication.
- **P0 — Test provenance.** The notebook writes the protocol before fitting, but parses and audits the entire record up front. The reviewed history provides no independently verifiable dated freeze or access seal establishing that earlier development never viewed held-out outcomes. Use “chronologically held out from fitting and selection” for this package. If independent evidence of prior test-driven tuning emerges, the affected held-out estimates require a documented corrective evaluation with a genuinely untouched partition. No numerical or feature-leakage P0 was identified in the reviewed implementation.
- **P1 — Reporting and reproducibility.** Interpret the paired MAE/RMSE and the flow degradation by state using the companion figure. The archived 97.2% is common-support coverage. Preserve the original plots and numeric records. Replay succeeded by executing code cells directly; the README's exact nbconvert invocation and an independent test-access seal remain unverified. The 38.6 MB source is tracked in Git despite the plan's preference for external storage of large raw files. Use the checksum-pinned source; preserve existing history.
- **P2 — Layout.** F2 could compress the two constant fuel-cell panels for page fit. The current traces retain the fixed selection and remain interpretable.

Accept Study C as an evidence package for within-record reference benchmarking and validity screening, with the test-provenance limitation recorded. The plan's core scientific objectives are met. Full procedural sign-off depends on evidence for its access-seal requirement. No additional HY2RES experiments are warranted for the approved question. The comparative result is a tradeoff, and the approved plan does not require a positive result.

The companion figure reads the committed metric table. From this folder run `python plot_review_comparison.py` to regenerate the SVG, PDF and 300 dpi PNG without model fitting or test scoring.
