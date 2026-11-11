# Dataset Limitations (A3)

- **Status:** updated after primary execution (2026-11-11; L12 added from R2 diagnostics). Ahmed's approval NOT_RECORDED.
- Each limitation cites its evidence.
- These limitations bound every future claim; they are not results.

| # | Limitation | Consequence for claims | Evidence |
| --- | --- | --- | --- |
| L1 | **Only three topologies** (one held-out topology per fold) | Results are conditional on these three simulated configurations. Intervals are not generalisation intervals; no claim about other networks | manifest v0.2; STATISTICAL_ANALYSIS_PLAN |
| L2 | **Simulation only** | No field, industrial or deployment claim | dataset ReadME |
| L3 | Thin classes: 1 NORMAL, 1 DELAY and 2 FAULT runs per topology | NORMAL/FAULT/DELAY per-class results descriptive only; SPECIFIC is blocked when the top class rests on fewer than 2 families | CLASS_FAMILY_COUNTS.csv; D_STATISTIC_EDGE_CASES |
| L4 | Class imbalance: LEAK 78.3% of windows | Coverage targets 0.80/0.90 expected NOT_ESTIMABLE under the primary policy; pooled metrics are LEAK-dominated | preflight class shares |
| L5 | **Run fingerprint:** absolute-level features nearly identify each run within a topology (median η² 0.99) | The classifier may learn run operating levels instead of event signatures. No physical-signature interpretation without the `offset_invariant_features` sensitivity | SCIENTIFIC_LIMITATIONS_AND_CLAIMS item 10 |
| L6 | **COMPRESSOR_DELAY / start-up confounding:** all DELAY windows lie in the start-up segment (median start 480 s vs about 10,000 s) | DELAY detection cannot be attributed to the delay event; descriptive only | item 11 |
| L7 | Unknown simulation ancestry of 19 run pairs | Family-bootstrap intervals may understate dependence; `extended_family_map` sensitivity | Y-D03 |
| L8 | Annotation anomalies (G5G6 location labels, `brokenC1G5_weak`, delay label ending at row 1000) | Excluded runs or rows; no location analysis | LABEL_CONSISTENCY.csv |
| L9 | Windows are dependent (50% overlap within runs) | Inference uses families, never windows, as units | SAP |
| L10 | Gas composition and simulator version unverified | No blend-percentage claim | Y1 amendment |
| L11 | Noise-added release: noise process documented only as white noise | Clean realization reported separately as robustness | RAW_DATASET_VERIFICATION_REPORT |
| L12 | **Source-dataset topology inconsistency (found after execution; attribution corrected by the forensic audit, 2026-11-11):** the released event folders `anom_gestcent` and `anom_gestdown` carry each other's simulation model (36 of 57 manifest runs, 32 eligible). The source models show that only the `down` model logs PS11/PS12/MFS4. `anom_gestcent` runs have these sensors active; `anom_gestdown` runs have them as padding with the center-model signature. The NORMAL files and all Upstream runs are consistent. *Correction note: the first version of L12 attributed the inconsistency to the two NORMAL files; both readings give the same two groups of runs, so R2 numbers are unaffected, but the physical attribution was wrong.* Related: absent sensors are released as zero-variance constants (24 padded features) | Center and Downstream folds each mix two sensor configurations, so their results are not interpretable as genuine cross-topology generalisation (99.5% of R2 errors follow this mechanism). RQ1/RQ2 are conditional on the release attribution. The manifest is unchanged pending the dataset owner's decision (`01_dataset_audit/YAZAN_TOPOLOGY_DECISION_PACKAGE.md`, R-18) | `03_results/diagnostics/forensics/{source_model_attribution,simulation_model_sensors,padded_channel_evidence}.csv` |

## Supported, exploratory and unsupported analyses

| Analysis | Status |
| --- | --- |
| Pooled RQ1 at matched coverage (s_C vs s_C−D) | supported (conditional, effect sizes) |
| RQ2 outcome shares | supported for LEAK (restricted); descriptive for the other classes |
| C vs B and other indicators; threshold transfer; sensitivity analyses | exploratory / secondary |
| Per-topology results | descriptive (one fold each) |
| Leak location, metric localisation | unsupported |
| DELAY as a separable event | unsupported |
| Generalisation beyond the three topologies; field validity; pure hydrogen | unsupported |
