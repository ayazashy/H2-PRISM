# Results Table Specification (A5)

- **Status:** T1–T3 BUILT from verified structural data (`03_results/tables/dataset_design/final/`); T4–T8 SPECIFIED, pending an authorized run. Tables are built by `tools/reporting/build_research_tables.py` from runner outputs (`configs/reporting_figures.yaml`). **No results exist yet.**

| Table | Question | Source | Columns (units) | Rules |
| --- | --- | --- | --- | --- |
| T1_dataset_support (+T2 eligibility, T3 folds) | data | manifest v0.2, preflight | topology × class: runs, families, windows | counts only (VERIFIED) |
| T4_matched_coverage | RQ1 | coverage_risk.csv (primary, rank_matched) | method; target_coverage; coverage; selective_risk; n_specific; n_eligible; n_families; folds_estimable | risk only with coverage; NOT_ESTIMABLE targets listed with empty values |
| T5_rq1_effects | RQ1 | rq1.csv (primary) | comparison_b; role; target; mode; status; realized_coverage_a/b; Δ; 95% CI; n_units | PRIMARY row (s_C vs s_C−D, 0.80) first; secondaries labelled |
| (runner output, shown in Fig. 3c) | RQ1 robustness | tie_sensitivity.csv | target; salt_index; Δ per salt; primary Δ | secondary; never selects a result |
| T6_rq2_outcomes | RQ2 | rq2.csv | target; class; n; SPECIFIC / AMBIGUITY / UNRESOLVED shares; reporting role | LEAK "restricted", others "descriptive_only" |
| (runner output, shown in Fig. 4b) | RQ2 | coverage_risk.csv ambiguity_*; rq2.csv ambiguity_inclusion | inclusion rate; mean / median size; broad rate | always reported with the count |
| T7_estimability | RQ1 / RQ2 | estimability.csv | fold; method; target; status; requested and realized counts; ties | complete; nothing omitted |
| (runner output, shown in Figs. 2b–d, 3b) | descriptive | rq1_by_topology.csv; risk_coverage_curve.csv scope | per held-out topology | descriptive only |
| (runner output, shown in Fig. 5c) | F6 | calibration_records.json, fold calibration_selection.csv, calibration_reliability.csv | selected method; log loss; Brier; reliability bins | development selection vs outer reliability kept apart |
| T8_robustness | robustness | each `SENSITIVITY_EXPERIMENT` run | the primary contrast per analysis with its population note | next to the primary result, never replacing it |

**Conventions:**
- Proportions are shown to 3 decimals.
- Intervals are 95% family-bootstrap, conditional on 3 topologies.
- In Markdown renderings, "n.e." marks a NOT_ESTIMABLE row and "—" an undefined value (e.g. risk with no SPECIFIC decision); never 0. The CSV keeps empty cells.
- Every table states artifact_class, config hash and run_key.
