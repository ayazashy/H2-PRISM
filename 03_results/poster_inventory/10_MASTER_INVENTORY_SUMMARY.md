# 10 — Master inventory summary (H₂-PRISM Results, poster preparation)

**Scope.** A read-only inventory of branch `research/integrated-validation` at commit 35c9e9a. No source figure, dataset or result was modified, regenerated or recomputed. All counts come from `01_…csv` and `02_…csv`, built by `scripts/`.

## 1. What exists

- **Figure files.** 408 tracked files (196 PNG, 167 SVG, 45 PDF), forming **204 logical figures**.

  | Lifecycle | Logical figures |
  |---|---|
  | Final (curated, QA approved: v1 Q1/H1/AV, v2) | 86 |
  | Final (R2 PUBLICATION_MANIFEST) | 3 |
  | Superseded by a redesign (original kept) | 59 |
  | Superseded | 36 |
  | Engineering verification | 8 |
  | Not results (planning PDFs) | 8 |
  | Obsolete (invented demo values) | 4 |

  | Category | Logical figures |
  |---|---|
  | Diagnostic scientific | 109 |
  | Reference prediction (HY2RES, MHC) | 44 |
  | Schematic or synthesis | 9 |
  | Superseded, working or poster exports | 20 |
  | Engineering QC | 8 |
  | Not results | 12 |
  | Design | 2 |

- **Tabular artifacts.** 529 logical tables: 147 publication tables, 91 analysis outputs, 291 registers and audits. Of the publication tables, 8 are approved R2 finals and 24 are preliminary or superseded R2 run tables.
- **Missing or inaccessible.**
  - 3 broken references: the superseded dataset-design manifest points to a moved `final/` path.
  - Raw data and frozen R2 predictions (Parquet) live outside the repository by design (`H2PRISM_R2_RUN`, the Center workspace, the HY2RES CSV); they are hash-verified, not tracked.

## 2. Evidence base: independent units

| Source | What was tested | Independent units | Notes |
|---|---|---|---|
| R2 | 27,993 dependent windows | 17 templates; 39 families | Labels disputed in 36/57 runs |
| Center | 12 captures | 1 air-like source family; 6 single-capture mechanism queries | |
| HY2RES | One pilot | — | Previously inspected test |
| MHC | 3 held-out runs | — | |

Nothing is independently validated.

## 3. Most defensible findings

| Class | Finding |
|---|---|
| Verified (H3) | Certificate-carrying, monotone formal D(Y): 0 forbidden transitions in 25,024 checks; 11,061/11,061 certificates and 1,552/1,552 witnesses re-verified; proof with stated assumptions |
| Conditional (Center, hypothetical bounds) | Decisions in the restricted universe: 8 correct, 2 wrong, 4 ambiguous, 28 model mismatch (42 cells); full universe 42/42 indeterminate; frozen 12/12 unresolved |
| Conditional | 14/15 template pairs separable at REF; Normal vs SID 215 bound-limited (λ* ≈ 0.08 × REF), explained by SID 215 exceeding 2 ε_REF on no channel |
| Conditional | Flow-only sensing doubles wrong SPECIFIC decisions (4 vs 2); losing MFS3 forces ambiguity; delay beyond the clock bound → abstention |
| Computational | About 0.36 s per 13-channel decision; near-linear in channels, hypotheses and window length |
| Negative | Registered H1 NOT_ESTIMABLE (max coverage 0.258 < 0.60) |
| Negative | D(x) adds no out-of-template information (log-loss 0.906 → 0.995) and tracks disputed labels |
| Negative | Library incompleteness → wrong SPECIFIC decisions (H9 CONTRADICTED); traceability 7/16 fields persisted (H10 CONTRADICTED) |
| Data defect | 7,347/8,012 R2 errors in disputed runs; run accuracy 0.947 undisputed vs 0.562 disputed |
| Blocked | Out-of-template generalization (data); hydrogen and blend transfer (physics); corrected replication (D1); monetary cost (no prices) |

## 4. Highest-priority figures

Priority A, all QA approved, PNG 3840 px plus SVG.

| Stage role | Figure | Path |
|---|---|---|
| Formal integrity | AV-F05 | `03_results/integrated_validation_v1/advanced_validation/figures/AV-F05_dy_status_transitions.png` |
| D(Y) decisions | Q1_C15 | `03_results/integrated_validation_v1/publication_q1/figures/Q1_C15_center_dy_evidence_breakdown.png` |
| D(Y) decision grid | Q1_C14 | `03_results/integrated_validation_v1/publication_q1/figures/Q1_C14_center_dy_restricted_decisions.png` |
| Limitation | AV-F04 | `03_results/integrated_validation_v1/advanced_validation/figures/AV-F04_library_completeness.png` |
| Isolability | V2-F03 | `03_results/integrated_validation_v2/05_figures/V2-F03_isolability_onset.png` |
| Robustness | AV-F08 | `03_results/integrated_validation_v1/advanced_validation/figures/AV-F08_missing_sensor_robustness.png` |
| Registered H1 | H1-F01 | `03_results/integrated_validation_v1/h1_validation/figures/H1-F01_attainable_coverage.png` |
| Label defect | AV-F02 | `03_results/integrated_validation_v1/advanced_validation/figures/AV-F02_false_specific_equal_coverage.png` |
| D(x) negative result | V2-F01 | `03_results/integrated_validation_v2/05_figures/V2-F01_dx_incremental_value.png` |

## 5. Highest-priority tables

| Table | Path | Size |
|---|---|---|
| Formal integrity | `03_results/integrated_validation_v1/advanced_validation/tables/A04a.csv` | 5 × 5 |
| Hypothesis statuses | `03_results/integrated_validation_v2/02_design/HYPOTHESIS_REGISTRY.csv` | 10 × 21; subset 10 × 4 |
| D(Y) decision reasons | `03_results/integrated_validation_v1/publication_q1/tables/T07b_dy_decision_reasons.csv` | 4 × 4 |
| D(x) out-of-template utility | `03_results/integrated_validation_v2/04_results/tables/V2-T01_dx_incremental_utility.csv` | 4 × 7 |
| Disputed vs undisputed runs | `03_results/integrated_validation_v2/04_results/tables/V2-T09_r2_run_level.csv` | 3 × 10 |
| Minimum sensor sets | `03_results/integrated_validation_v1/advanced_validation/tables/A16b.csv` | 4 × 7 |
| Scaling exponents | `03_results/integrated_validation_v1/advanced_validation/tables/A14b.csv` | 6 × 6 |

## 6. Duplicated or weak figures

- Duplicate pairs; choose one of each:
  - AV-F01 / H1-F02a;
  - AV-F04 / H1-F06;
  - AV-F07 / V2-F03;
  - Q1_C01 / V2-F04;
  - V2-F06 / AV-F16 / Q1_I09 / H1-F07.
- Superseded statement: AV-F15.
- Dense, avoid at reduced size: Q1_C12a–d, Q1_C13a/b, AV-F12.
- Do not feature:
  - the R2 figure-system finals (dense, < 3200 px);
  - every superseded or preliminary run key;
  - the Center atlas and its poster exports;
  - the Stage-2 `03_results/figures/fig1–6`;
  - engineering QC plots;
  - the four invented demo figures.

## 7. Proposed stage sequences

Full detail in `07_POSTER_STRUCTURE_ALTERNATIVES.md`; ranked A > B > C.

| Alternative | Stages |
|---|---|
| **A. Capability-first** (4) | Certified exclusions → What sensors can separate → How the engine decides and when it is wrong → Robustness and limits |
| **B. Question-first** (3) | Registered test not estimable, errors trace to labels → D(x) adds nothing → What remains defensible: certified decisions |
| **C. Claim ledger** (3) | Verified → Conditional → Negative/blocked |

## 8. Readability and aspect ratio

- Candidates are 16:9 (a few 1.55 or 1.33); the area is 7:5.
- Labels render at about 12 px at full width and 5.9 px at half width in an 840 × 600 area. Practical capacity is one dominant figure plus two or three compact items.
- Figures are white (#FFFFFF) on a #F4F4E9 poster.
  - The superseded Center (C), HY2RES (H) and MHC (B) enhancement originals already use #F4F4E9, but in sans-serif with footnotes inside the canvas. Choosing them trades consistency with the Q1 set for background match. Team decision.
- Panels must not be cropped in ways that remove evidence stamps or hatching (see `04_…`).

## 9. Missing evidence and assets

- **No figures for these results**, though tables exist:
  - per-class metrics on undisputed runs (V2-T08);
  - traceability (A18);
  - the D1 correction matrix.
- **No independent replicate captures.** Center has one family; only SID 213 has a second capture. So there is no uncertainty interval for any Center count.
- **No evidence at all** for:
  - out-of-template, localization-distance or field data;
  - a transient hydrogen or blend model;
  - price sources.

## 10. Deliverables

All in `03_results/poster_inventory/`:

| # | File |
|---|---|
| 01 | `01_COMPLETE_FIGURE_INVENTORY.csv` |
| 02 | `02_COMPLETE_TABLE_INVENTORY.csv` |
| 03 | `03_SCIENTIFIC_FINDINGS_CATALOG.md` |
| 04 | `04_FIGURE_CRITICAL_REVIEW.md` |
| 05 | `05_TABLE_CRITICAL_REVIEW.md` |
| 06 | `06_RESULTS_RELATIONSHIP_MAP.md` |
| 07 | `07_POSTER_STRUCTURE_ALTERNATIVES.md` |
| 08 | `08_FIGUREGUILD_ASSET_INDEX.csv` |
| 09 | `09_SCIENTIFIC_MISINTERPRETATION_REGISTER.md` |
| 10 | `10_MASTER_INVENTORY_SUMMARY.md` |

- Gallery: `gallery/GALLERY.html` and `gallery/CONTACT_*.png` (29 sheets of thumbnails; originals untouched).
- Raw discovery data: `data/figure_files_raw.csv`, `data/table_files_raw.csv`.
- Scripts: `scripts/discover_figures.py`, `discover_tables.py`, `build_inventory.py`, `build_asset_index.py`, `build_gallery.py`.
