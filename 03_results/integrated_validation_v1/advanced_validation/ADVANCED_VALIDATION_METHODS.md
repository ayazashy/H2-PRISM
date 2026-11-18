# Advanced validation — Methods

Results are in `ADVANCED_VALIDATION_RESULTS.md`. The protocol was fixed before any computation (`protocols/AV_PROTOCOL.md`).

## Inputs (all frozen, hash-verified, read-only)

- **R2 window predictions and decisions:** SHA-256 `4338c8c9…` and `1f457927…`, pinned in the R2 diagnostics manifest.
- **Configuration:** `FINAL_EXPERIMENT_CONFIG.yaml` (`f788b6d8…`).
- **Forensics:** `03_results/diagnostics/forensics/*`.
- **Center captures:** loaded through `h2prism.nres.load_pairs`, which refuses any capture whose raw SHA-256 differs from its receipt. Templates, hypotheses, bound ladder, eps split and adapter come from `h2prism.center_enhancement` (accepted, unmodified).
- **Formal engine:** `h2prism.certified_evidence.diagnose` (unmodified).
- **Gas properties:** `06_audit_preparation/simulation/h2net_v1/properties/V1_REPORT.json` and the H2–CH4 feasibility probe.

## Definitions

These extend `../h1_validation/H1_METHODS.md`.

**Classifier and selective-risk quantities**

| Quantity | Definition |
|---|---|
| Coverage | C = N_specific / N_population. N_population is 27,993 R2 windows or 24/42 Center decisions. |
| Wrong-specific risk | N_wrong_specific / N_specific. Undefined when N_specific = 0; zero errors are never reported as zero population risk. |
| Confident error | Wrong SPECIFIC with calibrated confidence ≥ 0.9. |
| Disputed run | Source model inconsistent with the manifest topology (forensic table). Used as a stratifier only. |
| Template (ancestor) | Scenario identity with the topology token removed. 17 in total. |

**Formal-evidence quantities**

- **Formal status transitions:** FEASIBLE, EXCLUDED and INDETERMINATE per hypothesis. When information is removed or bounds widen, the only allowed transitions are F→F, E→{F, E, I} and I→{I, F}.
- **Pairwise isolability (template level):** hypotheses i and j are separable at total bounds ε_k if, for every admissible shift pair (s, s′), max over coordinates of (|h_i,s − h_j,s′| − 2ε_kind) > 0. Under that condition no observation can be consistent with both.
- **Minimum sensor set:** the smallest channel subset (exhaustive over 2¹³ − 1) that keeps every pair that is separable with all channels.

**Evidence states (interpretation of formal outcomes, not new validation)**

| State | Formal outcome |
|---|---|
| (1) Sufficient for one hypothesis | SPECIFIC |
| (2) Consistent with several | AMBIGUOUS |
| (3) Outside the modelled space | UNRESOLVED/MODEL_MISMATCH (every supported hypothesis excluded) or UNRESOLVED/INDETERMINATE_HYPOTHESES (declared hypotheses without adapter) |
| (4) Invalid evidence | UNRESOLVED/INVALID_MEASUREMENT (contract issues such as gaps, misaligned timestamps or invalid uncertainty) |

## Procedures

| Script | Content |
|---|---|
| `scripts/av_r2.py` | Accounting, class breakdown, negative control, eligibility matrix, template sharing and train/test gap. Reuses the hash-verified H1 loader and the registered selection. |
| `scripts/av_dy_experiments.py` | 2,376 formal decisions in experiments E1–E4, with independent certificate re-verification. Run in parallel (7 workers). |
| `scripts/av_dy_analysis.py` | Invariants, summaries, localization, counterfactuals, isolability and minimum sets. |
| `scripts/av_benchmarks.py` | Timing with one dimension varied at a time. 2 warm-up runs plus 15 (D(Y)) or 5 (D(x)) repetitions. Peak memory from tracemalloc. D(x) is timed on synthetic arrays only. |
| `scripts/av_tables.py`, `fig_av.py`, `av_report.py` | Tables, figures and Results. Same Q1 figure system and automated QA as the publication package. |

## Inference

- No p-values.
- R2 intervals come from the H1 analysis (family and template bootstrap).
- Center results are counts over repeated views of six captures under declared conditions. No rate or interval is computed from them.
