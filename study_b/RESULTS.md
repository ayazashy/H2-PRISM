# Study B results

## Experimental scope and qualification

Study B asked whether causal pressure–flow operating references characterize measured hydrogen-compressor dynamics across recorded runs and operating conditions. The official MHC v1.2 ZIP matched the published byte count and MD5 and the prior SHA-256. Of 29 documented workbooks, 21 fell outside the physical task: two hydrogen-free thermal runs (1–2), five capacity measurements (3–7), and 14 single-stage compression runs (8–21). The eight remaining runs used dual-stage compression with common P-2 Stage II gauge pressure (barg) and MFC-3 outlet hydrogen flow (ln/min). Eligibility followed the documented experiment type and target comparability before model scoring. [Source manifest](source_manifest.json) · [Table 1](tables/table_1_eligibility.csv) · [Figure 1](figures/figure_1_design.svg)

Development runs were 22, 23, 25, 26, and 27. Held-out runs were 24, 28, and 29. The design grouped recordings by day, kept the continuous 26–27 sequence together, and retained both first-stage material designations at the held-out 180 bar outlet setting. Run 25 inherited Stage I charge from excluded capacity run 5. The source does not establish independent generating families across dates. [Frozen protocol](PROTOCOL.md) · [Split manifest](split_manifest.csv)

## Temporal coverage

The three test workbooks contain 15,890 finite paired-channel observation rows. After dropping the first row of each workbook from target candidacy, 15,887 adjacent pairs were possible. The two rejected intervals were 0.002 s in run 28 and 0.003 s in run 29. Neither exclusion came from target missingness. Both models scored the same 15,885 pairs per channel (99.9874% of candidate pairs). The scored wall-clock intervals span 0.992–1.008 s, within the prespecified 0.8–1.2 s tolerance. [Table 1](tables/table_1_eligibility.csv) · [Table 2](tables/table_2_performance.csv) · [Read-only verifier](verify_publication.py)

## Held-out comparison

B0 is causal persistence. B1 adds a regularized linear estimate of the change from the current pressure and flow. Errors are in the source units. MAE is the mean absolute error within a run and RMSE is the square root of its mean squared error. The aggregate is the arithmetic mean of the three run-level metrics. Relative change is 100 × (B1 − B0) / B0. Positive values indicate greater Ridge error. [Exact saved metrics](metrics.json) · [Table 2](tables/table_2_performance.csv)

| Target | Run | Pairs | B0 MAE | B1 MAE | MAE change | B0 RMSE | B1 RMSE | RMSE change |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P-2 (barg) | 24 | 4,940 | 0.127328 | 0.147208 | +15.613% | 0.381506 | 0.380735 | −0.202% |
| P-2 (barg) | 28 | 5,002 | 0.150460 | 0.163492 | +8.662% | 0.317137 | 0.316424 | −0.225% |
| P-2 (barg) | 29 | 5,943 | 0.199192 | 0.210281 | +5.567% | 0.444360 | 0.439834 | −1.019% |
| **P-2 (barg)** | **Run mean** | **15,885** | **0.158993** | **0.173660** | **+9.225%** | **0.381001** | **0.378997** | **−0.526%** |
| MFC-3 (ln/min) | 24 | 4,940 | 0.017004 | 0.031061 | +82.671% | 0.217643 | 0.217759 | +0.053% |
| MFC-3 (ln/min) | 28 | 5,002 | 0.037713 | 0.046271 | +22.693% | 0.295198 | 0.294761 | −0.148% |
| MFC-3 (ln/min) | 29 | 5,943 | 0.040231 | 0.049900 | +24.036% | 0.350092 | 0.349710 | −0.109% |
| **MFC-3 (ln/min)** | **Run mean** | **15,885** | **0.031649** | **0.042411** | **+34.004%** | **0.287644** | **0.287410** | **−0.082%** |

## Figure captions

**Figure 1.** Workbook eligibility, recording groups, and the decision-time input and evaluation boundary. Recording dates are grouping proxies on shared apparatus. [Experimental design](figures/figure_1_design.svg)

**Figure 2.** Full saved scored-response traces for runs 24 and 29, preselected to compare the first-stage materials at the 180 bar outlet setting. The elapsed axes begin at the first scored target and end at 82.3169 and 99.0337 min, respectively. Points are nominal one-second targets. There is no temporal smoothing or favorable window selection. The original styling and line paths are retained because observation-level Ridge predictions were not preserved. The overlap shows the scale of one-step corrections relative to compressor trajectories, while Figure 3 gives the metric differences. [Frozen responses](figures/figure_2_responses.svg) · [Protocol](PROTOCOL.md) · [Read-only verifier](verify_publication.py)

**Figure 3.** Per-run MAE for the two channels, equally weighted run means, and run-mean relative changes in MAE and RMSE. The run mean is a summary of three workbooks. [Performance comparison](figures/figure_3_performance.svg) · [Table 2](tables/table_2_performance.csv)

[Discussion](DISCUSSION.md) · [Evidence boundaries](claims.csv) · [Reproduction](REPRODUCE.md)
