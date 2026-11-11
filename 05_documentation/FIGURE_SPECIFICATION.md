# Research Figure Specification and Selection Register (A5), v3, 2026-11-11

- **Replaces:** v2, which listed one figure per metric. That version and the 2026-10-30 one are in Git history.
- **Status:** SPECIFICATION. Fig. 1 is built from verified structural data. **Figs. 2–6 have no data yet** (no authorized experiment) and are validated only on synthetic fixtures outside `03_results/`.
- Ahmed's approval NOT_RECORDED.

## Visual identity

- Colours: `h2prism.visualization.theme` (`apply_publication_theme`, `METHOD_COLORS`, `CLASS_COLORS`, `COLORS`), applied through `tools/reporting/_style.py`.
- Redundant encodings: every method also has a fixed line style and marker; every class a fixed hatch; every outcome a fixed colour and hatch.
- s_C (H₂-PRISM) is always navy solid with circles; s_C−D amber dashed with squares; confidence B grey dotted with triangles.
- Panels are lettered (a)–(d). Each figure carries its source line.

## Selection register (a figure only where it improves on a table)

| Fig. | ID | Question | What it reveals that a table cannot | Evidence (runner output) | Rejected alternatives |
| --- | --- | --- | --- | --- | --- |
| 1 | `fig1_dataset_and_design` | data support for RQ1/RQ2 | Shows together the scale gap between windows and independent families, the DELAY/start-up confounding in time, and the LOTO design. Each panel alone is weak; together they explain every later restriction | dataset-design tables (pinned manifest, folds, window table) | 6 single bar charts (redundant, one or two bars each) |
| 2 | `fig2_rq1_risk_coverage` | RQ1 | Shape of the risk–coverage trade-off; where safeguards cap attainable coverage; topology heterogeneity; registered targets at realized coverage | `risk_coverage_curve.csv` (pooled + per topology), `coverage_risk.csv` | separate per-target bars (lose the trade-off) |
| 3 | `fig3_rq1_incremental_value` | RQ1 | Paired effect sizes with intervals for all five comparisons and three targets (non-estimable ones listed), per-topology direction, and tie-order sensitivity in one view | `rq1.csv`, `rq1_by_topology.csv`, `tie_sensitivity.csv` | one plot per comparator |
| 4 | `fig4_rq2_three_outcome` | RQ2 | Class-specific SPECIFIC / AMBIGUITY / UNRESOLVED behaviour next to correctness vs inclusion, the reasons for withholding, and the D(x) safeguard flags | `rq2.csv`, `decision_reasons.csv`, `support_flags_summary.csv` | three-bar outcome chart; separate flag chart |
| 5 | `fig5_error_structure` | supporting (F5/F6) | Classifier error pattern next to the independent support behind each class and the calibration effect; window counts are never shown without family counts | `confusion_matrix.csv`, `class_metrics.csv`, `calibration_reliability.csv` | standalone confusion matrix (hides thin support) |
| 6 | `fig6_robustness` | RQ1 robustness | The primary contrast across all registered analyses. Different populations (60/60 windows, pre-event NORMAL) and different independence units are visually distinguished, so they are not ranked against the primary | `SENSITIVITY_SUMMARY/sensitivity_summary.csv` (copied from each run's `rq1.csv`) | one figure per sensitivity analysis |

**Not selected:**
- One figure per metric.
- Pie charts.
- A single-panel calibration figure (folded into Fig. 5).
- Per-sensitivity risk–coverage curves (Fig. 6 compares the registered estimand).
- A D(x) distribution plot: it would describe D(x), not its decision value; RQ1 tests the latter.

## Rules

- **Inputs:** values come only from recorded tables. Display transforms (row shares, flag rates) are declared in each manifest `metric_definition`.
- **Non-estimability:**
  - Pooled curves and markers exist only where the target is attainable in every held-out topology. Nothing is extrapolated into the shaded "not attainable" region.
  - Non-estimable comparisons are labelled "not estimable"; analyses that were not run are labelled "not run". Never 0.
- **Routing:** synthetic or preflight inputs go to `illustrative/` with a watermark and are refused inside `03_results/`. Model-output figures reach `final/` only with evidence_status VALIDATED/FROZEN, set by the owners after `PRIMARY_RESULTS_VALIDATION`.
- **Exports:** PNG (300 dpi), PDF and SVG.
- **Provenance:** recorded in `FIGURE_MANIFEST.csv` (inputs and hashes, run id, protocol/effective config hash, manifest hash, git commit, function, command, environment, units, metric definition, limitations, caption).

## Locations and commands

| Item | Path / command |
| --- | --- |
| Fig. 1 (built) | `03_results/figures/dataset_design/final/` ← `python tools/reporting/build_dataset_design_tables.py` then `python tools/reporting/build_research_figures.py --config configs/reporting_dataset_figures.yaml --out-dir 03_results/figures/dataset_design` |
| Figs. 2–6 (after an authorized run in `03_results/primary_protocol/PRIMARY/`) | `python tools/reporting/build_sensitivity_summary.py` then `python tools/reporting/build_research_figures.py --config configs/reporting_figures.yaml --out-dir 03_results/figures/primary` |
| Tables T1–T3 (built) / T4–T8 (pending) | `python tools/reporting/build_research_tables.py --config <same config> --out-dir 03_results/tables/<dataset_design or primary>` |
| Quarantined demo (never cite) | `03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/` (`scripts/visualize.py --demo`) |
| Historical | `03_results/figures/fig1_family_distribution.png`, `fig2_pipeline_telemetry.png` (superseded family map; not current evidence) |
