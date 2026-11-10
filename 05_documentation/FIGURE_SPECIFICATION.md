# Research Figure Specification (A5), v2, 2026-11-11

- **Replaces:** the 2026-10-30 version, which is in Git history. It listed figures 3–6 and a KPI dashboard built from invented numbers as "approved".
- **Status:** SPECIFICATION ONLY. **No research figure exists yet.** Ahmed's approval NOT_RECORDED.

## Quarantined illustrative files (not results)

`03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/` holds fig3–fig6 and `dashboard_ILLUSTRATIVE.html`. They come from hard-coded or random values via `scripts/visualize.py --demo`, must never be cited, and carry the label "ILLUSTRATIVE ONLY".

`03_results/figures/fig1_family_distribution.png` and `fig2_pipeline_telemetry.png` are historical descriptive plots built from the superseded family map. They are not evidence for the current folds.

## Planned figures (built only by `tools/reporting/build_research_figures.py` from authorized runner outputs)

| ID | Question | Content | Input (runner output) | Units / symbols | Status |
| --- | --- | --- | --- | --- | --- |
| fig_rq1_risk_coverage | RQ1 | selective risk vs coverage for s_C, s_C−D and confidence at the rank-matched targets (primary policy) | `03_results/primary_protocol/PRIMARY/coverage_risk.csv` | coverage, risk ∈ [0, 1] | PENDING |
| fig_f6_reliability | supporting (F6) | top-label reliability of calibrated outer-test probabilities, 10 bins with counts | `.../calibration_reliability.csv` | confidence, accuracy | PENDING |
| fig_rq1_effects | RQ1 | Δ risk with 95% family-bootstrap interval per comparison and target | `.../rq1.csv` | Δ (risk units) | PENDING |
| fig_rq2_outcomes | RQ2 | stacked SPECIFIC / AMBIGUITY / UNRESOLVED shares per class | `.../rq2.csv` | shares | PENDING |
| fig_data_composition (optional) | data | runs and families per class and topology | manifest v0.2 | counts | SPECIFIED (table T0 provides the same counts) |

## Rules

- Every figure carries its source file, experiment ID and config hash (FIGURE_BUILD_MANIFEST).
- Inputs with `artifact_class` SYNTHETIC_TEST or PREFLIGHT_ONLY are routed to `illustrative/` with a watermark.
- Only owner-raised `evidence_status` VALIDATED/FROZEN routes to `final/`.
- Risk is never plotted without coverage. NOT_ESTIMABLE targets are omitted from curves, and the caption names them.
- No decorative figures; each figure maps to RQ1, RQ2 or a method-validation item. Register: `FIGURE_PROVENANCE_REGISTER.csv`.
