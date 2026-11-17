# H₂-PRISM Study B — Experimental cross-run reference consistency

## Objective and scope

Can causal references characterize measured pressure–flow behavior consistently across separated runs and operating conditions? We tested nominal one-second-ahead prediction on the dual-stage subset of the verified MHC v1.2 release. The shared apparatus and incompletely established initial-state independence make this a descriptive held-out study. [Source verification](source_manifest.json) · [Measurement audit](AUDIT.md)

## Layer I — Causal signal representation

The audit inspected all 29 workbooks and retained 8 dual-stage experiments with common P-2 Stage II gauge pressure (barg) and MFC-3 outlet hydrogen flow (ln/min). The latter is a normalized volumetric reading. The study retained the recorded units and made no mass-flow conversion. The other workbooks cover thermal, capacity or single-stage operation. [Table 1 · experiment and measurement inventory](experiment_registry.csv) · [Figure 1 · experimental design](figure_1_design.svg)

## Layer II — Held-out reference evidence

The frozen split used development runs 22, 23, 25, 26 and 27 and test runs 24, 28 and 29. Same-day runs and the recorded 26–27 continuation were kept together. A separate capacity run supplied the initial charge for run 25 and was outside the benchmark. Both models predict from the same current row on identical eligible targets. B0 carries the current observation forward. B1 adds a regularized linear prediction of the next change from current pressure and flow. Standardization and coefficients were fitted on 25,757 development pairs. [Frozen protocol](PROTOCOL.md) · [Split manifest](split_manifest.csv) · [Metrics](metrics.json)

The table averages the per-run metrics equally over 3 held-out workbooks. Each channel has 15,885 scored pairs out of 15,887 possible adjacent pairs. Counts are observation pairs, with temporal dependence within each workbook. Positive ΔMAE denotes higher ridge error. [Table 2 · complete held-out results](per_run_metrics.csv) · [Aggregated metrics](metrics.json)

| Channel | Pairs | B0 MAE | B1 MAE | B0 RMSE | B1 RMSE | ΔMAE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P-2 (barg) | 15,885 | 0.158993 | 0.173660 | 0.381001 | 0.378997 | +0.014667 |
| MFC-3 (ln/min) | 15,885 | 0.031649 | 0.042411 | 0.287644 | 0.287410 | +0.010762 |

For P-2, persistence MAE ranged from 0.127328 to 0.199192 barg. Ridge lowered MAE in 0 of 3 held-out runs. [Per-run metrics](per_run_metrics.csv)
For MFC-3, persistence MAE ranged from 0.017004 to 0.040231 ln/min. Ridge lowered MAE in 0 of 3 held-out runs. [Per-run metrics](per_run_metrics.csv)

Persistence had lower MAE in every held-out run for both channels. The ridge correction slightly reduced run-mean RMSE on both channels. With opposite directions across the two loss functions, the evidence does not support a consistent improvement over persistence. Of 15,887 possible adjacent pairs, two were excluded by the timing criterion and none for missing target readings. [Per-run metrics](per_run_metrics.csv) · [Experiment registry](experiment_registry.csv)

Run comparisons span the documented inlet/outlet settings, material choices and cycle times. These factors, initial state, and recording histories vary together, so the per-run error spread cannot identify the effect of any single condition. Figures show the full held-out error distribution and illustrate two preselected runs at the same nominal outlet setting with different Stage I materials. Higher RMSE than MAE reflects the unequal magnitudes of errors across samples, including transitions. [Figure 2 · held-out responses](figure_2_responses.svg) · [Figure 3 · per-run error](figure_3_performance.svg) · [Operating metadata](experiment_registry.csv)

## Layer III — Qualified decision

The short-horizon residuals are valid descriptive evidence for consistency of the two recorded channels under the stated eligibility rules. The small number of test recording groups, unknown cross-day carryover, and absence of independent calibration and a decision threshold limit stronger adequacy claims. Fault detection, localization, formal D(Y) outcomes, and industrial transfer are outside the qualified evidence. [Table 3 · claims and evidence](claims.csv)

## Reproduce

From the MHC worktree using Python 3.12:

```powershell
python -m pip install -r study_b/requirements.txt
python study_b/test_benchmark.py
python study_b/benchmark.py "<path-to-official-MHC-v1.2.zip>"
```

The benchmark verifies the archive, reads the source workbooks without extraction, regenerates the audit tables and fixed split, and writes metrics and the three figures in SVG, PDF and 360 dpi PNG. All values above refer to the checked-in outputs. [Source attribution](SOURCE.md)
