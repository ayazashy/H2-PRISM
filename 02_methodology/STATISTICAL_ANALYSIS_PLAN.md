# Statistical Analysis Plan (F11), fixed before any outer-test evaluation

- **Status:** SPECIFIED from config `evaluation` and `uncertainty.paired_stratified_bootstrap`; IMPLEMENTED and TESTED.
- **Results:** POST_EXPERIMENT.

| Item | Specification |
| --- | --- |
| Estimand (RQ1, primary) | Pooled selective-risk difference Δ = risk(s_C) − risk(s_C−D) at matched coverage (rank-matched, PA-1), primary policy, target 0.80. Negative Δ means lower risk with D |
| Secondary RQ1 | the same Δ at targets 0.60 and 0.90; the warning-only variant; threshold-transfer mode; C vs B (confidence), margin, −H, D-only |
| RQ2 | per-class shares of SPECIFIC / AMBIGUITY_SET / UNRESOLVED; ambiguity inclusion and size; LEAK "restricted", other classes "descriptive_only" |
| Selective risk | errors among SPECIFIC / n_specific; NaN (undefined, not 0) if n_specific = 0 |
| Coverage | n_specific / n_eligible |
| Independence unit | Scenario_Family_ID (39 primary families) |
| Uncertainty | paired, topology-stratified family bootstrap: resample families within each topology with replacement, 2,000 replicates, seed 20261104, 95% percentile interval. A stratum with one unit is held fixed (warning) |
| Pooling | a pooled RQ1 result exists only if both methods are estimable in **every** fold; otherwise NOT_ESTIMABLE (with folds_estimable) |
| Inference | effect sizes with intervals only. No p-values, no significance claims, no practical-significance threshold (the 25% candidate was never approved) |
| Interpretation | conditional on the three simulated topologies; not a generalisation interval |
| Multiplicity | one primary estimand; all secondaries are labelled and not used for confirmation |
| Sensitivity | 9 registered analyses (`SENSITIVITY_ANALYSIS_SPEC.md`) plus tie-order sensitivity; reported descriptively next to the primary result |
| Negative or null results | valid and reported (`outcomes_accepted`: positive, null, negative, mixed, not_estimable) |

**Limitations:**
- 13 families per stratum.
- Windows are dependent within runs.
- Thin classes (1–2 runs per topology).
- LEAK dominance (78.3%).
- Run fingerprint (limitation 10) and DELAY/start-up confounding (limitation 11).
