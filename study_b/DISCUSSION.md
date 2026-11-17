# Study B discussion

## Persistence and Ridge

Persistence achieved lower MAE in all six run–channel comparisons. Ridge reduced pressure RMSE in each run and flow RMSE in runs 28 and 29. Flow RMSE in run 24 increased slightly. Across equally weighted runs, the pressure and flow RMSE reductions were approximately 0.526% and 0.082%, with MAE increases of 9.225% and 34.004%. These results establish different rankings under absolute and squared loss. Practical significance of the small aggregate RMSE changes is unestablished. [Table 2](tables/table_2_performance.csv)

A post hoc squared-error accounting uses each run's scored count multiplied by the difference of squared RMSEs. Ridge minus persistence changes in total pressure squared error were −2.903, −2.259, and −23.785 barg² for runs 24, 28, and 29. Run 29 therefore contributed about 82% of the net pressure reduction by this observation-weighted accounting. For flow, changes were +0.249, −1.290, and −1.589 (ln/min)². This accounting is distinct from run-mean RMSE. The saved summaries cannot identify residual quantiles, extreme-error concentration, or the timing of individual Ridge corrections. [Saved per-run metrics](per_run_metrics.csv)

## Operating conditions

Run 24 was a TiZrMn/TiCrMn run at nominal 30/180 bar and a 15-min half-cycle. Runs 28 and 29 were MmNiFe/TiCrMn runs at 20/140 and 30/180 bar with 10-min half-cycles. Persistence MAE for both channels was lowest in run 24 and highest in run 29. The run comparisons confound settings, material, initial state and recording history. The thermofluid and separately logged temperature metadata do not give a controlled comparison of thermal effects. No transition or flow-regime residual analysis is supported by the saved Ridge summaries. [Tables 1](tables/table_1_eligibility.csv) · [Table 2](tables/table_2_performance.csv)

## Framework contribution

Layer I establishes the handling of recorded gauge pressure, normalized volumetric hydrogen flow, timestamp alignment, and causal observation pairs within these experimental recordings. Physical measurement calibration and conversion to mass-flow units remain unverified. Layer II establishes a held-out local reference comparison and near-complete scoring coverage under the eligibility rules. Performance varies by run and by loss. Layer III requires physical fault evidence, qualified bounds and decision criteria that these data do not provide. Fault diagnosis, leak localization, formal D(Y) exclusion, and independent industrial transfer remain unestablished. [Table 3](claims.csv)

## Conclusion

The measured dual-stage pressure and flow support a reproducible short-horizon operating-reference comparison on shared laboratory equipment. Persistence was more consistent under MAE. The small Ridge RMSE reductions establish metric sensitivity within this sample. The selected channels and the small number of held-out recording groups limit applicability to the observed conditions.
