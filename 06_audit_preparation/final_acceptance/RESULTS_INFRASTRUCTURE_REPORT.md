# Results Infrastructure Report (Phases 11–12)

**Date:** 2026-11-11. **Branch:** `audit/preparation-integration`. **Config:** `f788b6d870183303b4478b2852858e270074cd1d716398e6058b6c650b234aae` (unchanged).

## Verdicts (each verified independently)

| Stage | Verdict | Evidence |
| --- | --- | --- |
| RESULTS_INFRASTRUCTURE_READY | **YES** | runner outputs and schemas, figure/table builders, provenance and tests (below) |
| PRIMARY_EXPERIMENTS_AUTHORIZED | **NO** | no authorization file exists; F-D15, F-D16, A-D10 and PA-1 have no recorded attestation or waiver (sign-off sheets blank). `--execute-primary` → `REFUSED: AuthorizationError`, nothing written (re-checked) |
| PRIMARY_EXPERIMENTS_COMPLETED | **NO** | `03_results/primary_protocol/` does not exist; no real-data model was trained |
| SCIENTIFIC_RESULTS_VALIDATED | **NO** | no results to validate |
| PUBLICATION_FIGURES_READY | **PARTIAL** | Fig. 1 and tables T1–T3 are genuine (verified structural data). Figs. 2–6 and T4–T8 are implemented and validated on synthetic fixtures only; they build automatically from an authorized run |

## 1. Existing infrastructure reviewed and reused

| Existing component | Use |
| --- | --- |
| `src/h2prism/visualization/theme.py` (`apply_publication_theme`, `METHOD_COLORS`, `CLASS_COLORS`, `COLORS`) | Single source of the visual identity. `tools/reporting/_style.py` maps runner method names onto it and adds line-style, marker and hatch redundancy. No new palette |
| A13 builders `tools/reporting/build_research_figures.py`, `build_research_tables.py`, `_common.py` (routing final/preliminary/illustrative, input loading, hashing) | Extended in place, with one manifest mechanism for figures and tables. No parallel framework |
| `h2prism.visualization` demo functions (array inputs, invented values) | Not reused for results: they plot arrays, not recorded tables. They stay the quarantined demo path (`03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/`) |
| Runner `src/h2prism/experiments/primary_protocol.py` | Extended with the result tables the figures need (below) |

## 2. Missing workflow links fixed (verified data → … → provenance)

| Link | Fix |
| --- | --- |
| Runner → risk–coverage figure | `risk_coverage_curve.csv` (descriptive PA-1 grid 0.05–1.00; pooled only where attainable in every held-out topology; per-topology scopes) |
| Runner → per-topology RQ1 | `rq1_by_topology.csv` (single-fold point estimates, labelled descriptive) |
| Runner → classifier error structure | `confusion_matrix.csv` (pooled and per topology), `class_metrics.csv` (with runs and families) |
| Runner → RQ2 depth | `rq2.csv` + `n_families`, `specific_correct`, `ambiguity_inclusion`; `decision_reasons.csv`; `ambiguity_sizes.csv`; `support_flags_summary.csv` |
| Runner → window-level archive | `predictions.parquet`, `decisions.parquet` (local; not committed) |
| Runs → robustness figure | `tools/reporting/build_sensitivity_summary.py` (copies each run's primary contrast; real execution classes only; population notes; NOT_RUN listed) |
| Verified data → design figure | `tools/reporting/build_dataset_design_tables.py` (pinned manifest, folds, runner window table; preflight 28/28; no fitting) |
| Builder robustness | multi-input figures; the primary input comes from the figure kind, not YAML order; empty selections of an existing run render "not estimable"; synthetic inputs refused inside `03_results/`; PNG/PDF/SVG |
| Cross-platform hashes | `.gitattributes` forces LF for `03_results/**/*.{csv,json,md,svg}`; PNG/PDF binary |

The contract `configs/interface_contracts.yaml` lists every new output, and `tests/test_interface_contract.py` checks it.

## 3. Selected figures (selection register: `05_documentation/FIGURE_SPECIFICATION.md`)

| Fig. | Scientific necessity | Data |
| --- | --- | --- |
| 1 Data support and design (4 panels) | Explains every later restriction: windows vs independent families, DELAY/start-up confounding, LOTO design | **genuine**, `03_results/figures/dataset_design/final/` |
| 2 Risk–coverage, pooled + per topology | RQ1 trade-off, attainable range, registered targets at realized coverage, heterogeneity | pending authorized run |
| 3 Incremental value of D(x) | RQ1 paired effects with intervals for all comparators/targets, per-topology direction, PA-1 tie sensitivity | pending |
| 4 Three-outcome behaviour | RQ2 outcomes, correctness vs inclusion, reasons, D(x) flags | pending |
| 5 Error structure | classifier confusion with independent support and calibration | pending |
| 6 Robustness | primary contrast across registered analyses; different populations marked, not ranked | pending |

Six single-metric dataset charts and the per-metric result figures of the previous draft were consolidated into these six.

## 4. Tables

- **T1–T3 (genuine):** dataset support, eligibility/exclusions, outer folds. Location: `03_results/tables/dataset_design/final/`.
- **T4–T8 (pending):** matched coverage, RQ1 effects, RQ2 outcomes, estimability, robustness.
- **Format:** CSV is authoritative (values unchanged). The Markdown rendering shows "n.e." for NOT_ESTIMABLE and "—" for undefined values, with captions. `TABLE_MANIFEST.csv` gives the run provenance.

## 5. Regeneration

```
python tools/reporting/build_dataset_design_tables.py
python tools/reporting/build_research_figures.py --config configs/reporting_dataset_figures.yaml --out-dir 03_results/figures/dataset_design
python tools/reporting/build_research_tables.py  --config configs/reporting_dataset_figures.yaml --out-dir 03_results/tables/dataset_design
# after an authorized PRIMARY run (and any authorized sensitivity runs):
python tools/reporting/build_sensitivity_summary.py
python tools/reporting/build_research_figures.py --config configs/reporting_figures.yaml --out-dir 03_results/figures/primary
python tools/reporting/build_research_tables.py  --config configs/reporting_figures.yaml --out-dir 03_results/tables/primary
```

Numerical values are exactly reproducible. Export bytes are deterministic for the recorded environment (`environment` column in the manifests); other Matplotlib versions may differ in bytes only.

## 6. Validation

- **`tests/test_figure_system.py` (16 tests):** plotted values are extracted from the Matplotlib artists and compared with the source CSVs:
  - risk–coverage curves equal the pooled attainable points, and nothing is extrapolated;
  - target markers only where estimable in every fold;
  - forest points equal `rq1.difference` and every non-estimable row is labelled;
  - outcome bars equal `rq2` shares and sum to 1;
  - confusion annotations equal the counts;
  - all registered analyses appear in Fig. 6;
  - dataset bars equal the source counts.
- **The same suite also checks:** provenance completeness; source-hash correspondence; synthetic refusal in the official tree; reproducible exports; table value preservation; the official Fig. 1/T1–T3 manifests match their current inputs and outputs.
- **Visual review:** all six figures were inspected and corrected:
  - glyph fallback;
  - label and legend collisions;
  - a partial-fold target marker that implied a pooled operating point.
- **Full suite:** see `SESSION_CHECKPOINT.md` (final run before commit).

## 7. Scientific limitations carried into every figure and caption

- Three simulated topologies.
- One independent family per thin class per topology.
- Run fingerprint of absolute-level features.
- COMPRESSOR_DELAY confounded with start-up.
- Unknown ancestry of 19 run pairs.
- Effect sizes only, with intervals conditional on the observed topologies.
- Matched-coverage targets may be not estimable under the safeguards.

## 8. Remaining blockers and next action

**Blockers:**
- F-D15: Faisal code acceptance.
- F-D16: Faisal contract acceptance.
- A-D10: Ahmed/Yazan Gate 1–3 attestation.
- PA-1: Faisal or project-lead acceptance.
- The project lead's authorization file (`NEXT_PHASE_EXECUTION_HANDOFF.md`).

**Next action:** record those clearances or written waivers. Then run `--execute-primary --out 03_results/primary_protocol/PRIMARY`, validate the run (`PRIMARY_RESULTS_VALIDATION`), raise `evidence_status` and run the commands in §5.

## 9. Refinement and engineering-phase closure (2026-11-11, follow-up)

**Visual refinements.** Every refined figure was re-rendered on synthetic QA fixtures in scratch, outside `03_results/`, and inspected. Plotted values are unchanged: all correspondence tests pass.

| Fig. | Weakness found | Refinement |
| --- | --- | --- |
| all | Light spines and dashed grid were weak in print | Theme tokens: gray-medium spines, dark ticks and labels, quiet solid grid (palette unchanged, from `h2prism.visualization.theme`) |
| 2 | Target lines came from a hard-coded list (an estimable target could be unlabelled); a legend covered the curves; per-panel text collided with the target lines | Targets taken from the run's recorded table, each labelled "target t" or "target t / not estimable". Pooled markers only where estimable in every held-out fold (true fold count). Legend below, with explicit "registered target" and "not attainable" keys. Per-panel n eligible windows |
| 3 | Comparator rows hard to separate; primary contrast not distinguished | Alternating bands per comparator; bold primary-contrast labels; key for filled (primary) vs open (secondary) markers |
| 4 | Display-target note inside the title; the reason colour duplicated the AMBIGUITY_SET colour and hatch | Separate subtitle; reason colours exclude the three outcome colours |
| 5 | Confusion matrix left white space; colour bar crowded panel (b) | Matrix fills its panel; wider spacing; colour bar labelled "row share of windows" |
| 6 | Populations stated only in a footnote | Every row now states "same windows", "different population" or "different units" in-panel |
| 1 | — (already strong) | Re-rendered with the refined tokens; source tables byte-identical |

**Lifecycle completed with one small command.** `tools/reporting/build_results.py`:
- discovers runs and validates each one: COMPLETED; execution class with a recorded authorization; pinned config hash; contracted columns; RQ2 shares sum to 1; matched coverage; unique window ids;
- writes `03_results/validation/` and a run registry `03_results/RESULTS_INDEX.csv`;
- builds the sensitivity summary from validated runs only;
- writes tables and figures into versioned directories `03_results/{tables,figures}/primary/<run_key12>/`, never overwriting an existing version.

**Related changes:**
- The runner now records the authorization (scope, authorizer, date, clearances, file hash) in `run_manifest.json`.
- Both builders refuse incomplete or unauthorized runs for official outputs.

**Regeneration after an authorized run (one command):**

```
python tools/reporting/build_results.py
```

**Synthetic QA (never in `03_results/`):**

```
python tools/reporting/build_results.py --root <scratch tree> --out-root <scratch>/qa --allow-synthetic
```

**Execution gate (re-checked):**
- no authorization file exists;
- F-D15, F-D16, A-D10 and PA-1 are unrecorded;
- `--execute-primary` → `REFUSED: AuthorizationError`.

No training was run.
