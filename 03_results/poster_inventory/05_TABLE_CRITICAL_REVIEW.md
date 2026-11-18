# 05 — Table critical review

## Scope

`02_COMPLETE_TABLE_INVENTORY.csv` lists 529 logical tables (CSV and Markdown twins merged). By role:

| Role | Count | Examples |
|---|---|---|
| Publication tables | 147 | Q1 T01–T10; H1-T01–T08; A01–A20; V2-T01–T10; Center TAB_01–14 and TAB_C01–C08; HY2RES TABLE_1–2 and TAB_H*; MHC TAB_B*; R2 figure-system T4–T9 (approved) and their preliminary variants |
| Analysis outputs | 91 | v2 `04_results/analysis/*`, v1 analysis and benchmarks |
| Registers and audits | 291 | Leakage register, hypothesis registry, acceptance criteria, dataset-audit and governance registers |

## Poster-scale legibility rule of thumb

In an 840 × 600 area, a table set in 8–9 px text holds about 25–30 text rows at full height and roughly 8–10 short columns at half width. Tables above 10 rows or 8 columns need a faithful subset. Every subset below keeps whole rows and named columns; none drops a row that would change a conclusion.

## Candidate tables

| Table (path) | Size | Scientific value | Traceable | Redundant with | Poster suitability |
|---|---|---|---|---|---|
| `03_results/integrated_validation_v2/02_design/HYPOTHESIS_REGISTRY.csv` | 10 × 21 | Highest: all H1–H10 statuses | Yes; generated from cited files | V2-F06 | **Subset**: id, name, status, direction (10 × 4) |
| `03_results/integrated_validation_v2/06_reports/ACCEPTANCE_CRITERIA.csv` | 10 × 13 | Why each claim is or is not confirmatory | Yes | V2-F06 (same content) | Figure V2-F06 is the better form |
| `03_results/integrated_validation_v1/advanced_validation/tables/A04a.csv` | 5 × 5 | Formal integrity counts (0 violations) | Yes | AV-F05 (partial) | **Full**, compact; strongest formal evidence |
| `03_results/integrated_validation_v1/publication_q1/tables/T07b_dy_decision_reasons.csv` | 4 × 4 | D(Y) decisions by reason (all sensors, ±1 s) | Yes | Q1_C15 | Full; use if Q1_C15 is not shown |
| `03_results/validation/center_evidence_enhancement/tables/TAB_C06.csv` | 84 × 14 | All decisions by universe and bound scenario | Yes | Q1_C14, Q1_C15 | Too large; Q1_C15 is its summary |
| `03_results/integrated_validation_v1/publication_q1/tables/T07a_dy_conditional_decisions.csv` | 16 × 9 | Decisions by universe, sensor group, clock bound | Yes | AV-F08 (partly) | Source of the "48 correct / 11 wrong" pooled counts; repeated views, not trials |
| `03_results/integrated_validation_v1/advanced_validation/tables/A05.csv` | 4 × 17 | Library completeness | Yes | AV-F04 | Subset: variant, correct, wrong, ambiguous (truth in/out), mismatch |
| `03_results/integrated_validation_v1/advanced_validation/tables/A08.csv` | 22 × 17 | Sensor masks | Yes | AV-F08 | Figure preferred; table for exact counts |
| `03_results/integrated_validation_v1/advanced_validation/tables/A09.csv` | 13 × 17 | Timing | Yes | AV-F09 | Figure preferred |
| `03_results/integrated_validation_v1/advanced_validation/tables/A16b.csv` | 4 × 7 | Minimum sensor sets for isolability | Yes | AV-F07 | **Full**, compact; "MFS1 + MFS3 at REF" |
| `03_results/integrated_validation_v2/04_results/tables/V2-T04_isolability_onset.csv` | 45 × 8 | λ* per pair and channel set | Yes | V2-F03 | Figure preferred; subset of the 8 BOUND_LIMITED rows = `analysis/i3_unidentifiable_pair_register_REF.csv` (8 × 11) |
| `03_results/integrated_validation_v2/04_results/tables/V2-T03_dy_synthetic_sensor_faults.csv` | 30 × 7 | Synthetic fault outcomes | Yes | V2-F02 | Figure preferred |
| `03_results/integrated_validation_v2/04_results/tables/V2-T01_dx_incremental_utility.csv` | 4 × 7 | D(x) out-of-template log-loss | Yes | V2-F01 (per-template view) | **Full** (4 rows); subset columns model, log-loss, AUROC |
| `03_results/integrated_validation_v1/h1_validation/tables/H1-T02.csv` | 4 × 11 | Registered feasibility (targets vs attainable) | Yes | H1-F01 | Subset |
| `03_results/integrated_validation_v1/h1_validation/tables/H1-T04.csv` | 15 × 16 | Exploratory selective risk with intervals | Yes | H1-F02a/b | Subset at coverage 0.25 (6 comparators) |
| `03_results/integrated_validation_v1/advanced_validation/tables/A02a.csv` | 36 × 18 | Wrong-specific accounting by attribution | Yes | AV-F02 | Figure preferred |
| `03_results/integrated_validation_v2/04_results/tables/V2-T09_r2_run_level.csv` | 3 × 10 | Run accuracy, disputed vs undisputed | Yes | none | **Full**, compact; strong label-defect evidence |
| `03_results/integrated_validation_v2/04_results/tables/V2-T08_r2_class_metrics.csv` | 25 × 12 | Class metrics by scope and topology | Yes | Q1_I05 | Subset: the two ALL rows (all windows vs undisputed) |
| `03_results/integrated_validation_v1/publication_q1/tables/T09b_rq3_three_outcome.csv` | 4 × 9 | Registered RQ3 shares | Yes | Q1_I08 | Only with the Center-excluded note |
| `03_results/integrated_validation_v1/advanced_validation/tables/A11a.csv` | 15 × 7 | Negative control | Yes | AV-F11 | Subset at 0.25; one NORMAL template |
| `03_results/integrated_validation_v2/04_results/tables/V2-T06_hy2res_certified_port.csv` | 7 × 8 | Frozen vs certified HY2RES | Yes | V2-F05 | Figure preferred |
| `03_results/integrated_validation_v1/advanced_validation/tables/A13.csv` | 4 × 6 | Gas qualification | Yes | AV-F14 | Either; the figure is more compact |
| `03_results/integrated_validation_v1/advanced_validation/tables/A14b.csv` | 6 × 6 | Scaling exponents | Yes | AV-F12 | **Table preferred** (6 numbers vs six panels) |
| `03_results/integrated_validation_v1/advanced_validation/tables/A14a.csv` | 37 × 9 | Raw runtimes | Yes | AV-F12 | Too large |
| `03_results/integrated_validation_v1/advanced_validation/tables/A18.csv` | 17 × 4 | Traceability fields (H10) | Yes | none | Subset (the TRACE COVERAGE row) or text |
| `03_results/integrated_validation_v2/04_results/tables/V2-T10_cost_categories.csv` | 6 × 4 | Cost categories (no prices) | Yes | none | Compact; negative statement |
| `03_results/integrated_validation_v2/04_results/tables/V2-T07_hypothetical_cost_scenarios.csv` | 57 × 9 | Hypothetical relative costs | Yes | AV-F13 | Not for the poster: hypothetical units invite savings misreading |
| `03_results/integrated_validation_v2/01_audit/LEAKAGE_REGISTER_V2.csv` | 22 × 10 | Integrity defects | Yes | none | Methods or limitations, not Results |
| `03_results/integrated_validation_v1/publication_q1/tables/T10_claim_evidence.csv` | 44 × 6 | v1 claim matrix | Yes | Q1_I09 | Superseded in part by the v2 registry |
| `03_results/tables/primary/a10530f1fcf2_s4228b6c8_b200fcdac/final/T4–T9` | 6–54 rows | Approved R2 run tables | Yes (PUBLICATION_MANIFEST) | H1/AV tables | Archival; the v1/v2 tables are the analysed form |
| `03_results/hy2res_external_validation/publication/TABLE_2_HELD_OUT.csv` | 20 × 14 | HY2RES prediction metrics | Yes | Q1_H05 | Context only |
| `study_b/RESULTS.md` (MHC benchmark table) | 8 rows | MHC prediction metrics | Yes | Q1_B05/B06 | Context only |

## Tables not to use on the poster

- **Large raw or derived tables:** TAB_07 (640 rows), TAB_08 (560), TS01 (4,816), SEGMENT_ERRORS (1,227), A14a, dy_decision_runtime_from_experiments (2,376).
- **Preliminary or superseded R2 run tables** in `03_results/tables/primary/*/preliminary`.
- **Hypothetical cost tables** with relative units, unless explicitly labelled.

## Traceability

Every candidate table above is written by a script that reads verified outputs:
- v1: `publication_q1/scripts/build_tables.py`, `h1_validation/scripts/h1_tables.py`, `advanced_validation/scripts/av_tables.py`;
- v2: `03_execution/scripts/build_v2_tables.py`;
- Center: `h2prism.center_enhancement`;
- HY2RES: `publication/build_publication.py`.

Checksums are in each package's `SHA256SUMS.csv` and pass their verifiers (v1 275/275, AV 57/57, v2 35/35).
