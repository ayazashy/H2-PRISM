# Results Table Specification (A5)

- **Status:** SPECIFICATION. Tables are built by `tools/reporting/build_research_tables.py` from runner outputs (`configs/reporting_figures.yaml`). **No results exist yet.**

| Table | Question | Source | Columns (units) | Rules |
| --- | --- | --- | --- | --- |
| T0 Data composition | data | manifest v0.2, preflight | topology × class: runs, families, windows | counts only (VERIFIED) |
| T_RQ1_matched_coverage | RQ1 | coverage_risk.csv (primary, rank_matched) | method; target_coverage; coverage; selective_risk; n_specific; n_eligible; n_families; folds_estimable | risk only with coverage; NOT_ESTIMABLE targets listed with empty values |
| T_RQ1_paired_effects | RQ1 | rq1.csv (primary) | comparison_b; role; target; mode; status; realized_coverage_a/b; Δ; 95% CI; n_units | PRIMARY row (s_C vs s_C−D, 0.80) first; secondaries labelled |
| T_RQ1_tie_sensitivity | RQ1 robustness | tie_sensitivity.csv | target; salt_index; Δ per salt; primary Δ | secondary; never selects a result |
| T_RQ2_outcomes | RQ2 | rq2.csv | target; class; n; SPECIFIC / AMBIGUITY / UNRESOLVED shares; reporting role | LEAK "restricted", others "descriptive_only" |
| T_ambiguity | RQ2 | coverage_risk.csv ambiguity_* | inclusion rate; mean / median size; broad rate | always reported with the count |
| T_estimability | RQ1 / RQ2 | estimability.csv | fold; method; target; status; requested and realized counts; ties | complete; nothing omitted |
| T_per_topology | descriptive | fold-level outputs | per held-out topology | descriptive only |
| T_calibration | F6 | calibration_records.json, fold calibration_selection.csv, calibration_reliability.csv | selected method; log loss; Brier; reliability bins | development selection vs outer reliability kept apart |
| T_sensitivity | robustness | each `SENSITIVITY_EXPERIMENT` run | the primary rows of T_RQ1 per analysis | next to the primary result, never replacing it |

**Conventions:**
- Proportions are shown to 3 decimals.
- Intervals are 95% family-bootstrap, conditional on 3 topologies.
- "—" marks NOT_ESTIMABLE (never 0).
- Every table states artifact_class, config hash and run_key.
