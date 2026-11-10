# Ahmed: Scientific Review Dossier (decisions A-D01 … A-D11)

**Status:** every decision is `PENDING_HUMAN_APPROVAL`. Nothing here is an experimental result.

## A-D01 / A-D02: Research-question feasibility

| Aspect | Classification | Reason |
| --- | --- | --- |
| RQ1: does D add decision value beyond C, M, H at matched coverage (pooled, C vs C−D, family-paired) | **TESTABLE_WITH_RESTRICTIONS** | Leakage-safe design exists. The pooled population is dominated by LEAK (39 of 51 runs). There are 39 primary families for paired resampling, and 3 outer folds |
| RQ1 per class | DESCRIPTIVE_ONLY (NORMAL, FAULT, DELAY); RESTRICTED (LEAK) | 1 test run per thin class per fold |
| RQ1 across topologies | NOT_SUPPORTED as inference | n = 3 topologies |
| RQ2: rates of SPECIFIC / AMBIGUITY_SET / UNRESOLVED and their reproducibility | **TESTABLE_WITH_RESTRICTIONS** | Policy implemented; thresholds come from development only |
| RQ2: whether ambiguity sets are "meaningful" | EXPLORATORY | Needs an interpretation criterion fixed before the run (inclusion together with size) |

The RQs need no rewording. The restrictions belong in the methodology and limitations sections, and negative or inconclusive results must be reportable.

## A-D03: Scope of generalisation

| Claim scope | Supported by this design? |
| --- | --- |
| Performance on a held-out withdrawal topology of the H₂-SimNet simulated network | Yes (estimand of the LOTO design) |
| Cross-scenario generalisation within a topology | Not tested by the primary design |
| Performance on the available simulated networks overall | Pooled, descriptive across 3 topologies |
| Unseen industrial networks | **No** |
| Field validation | **No** (simulated data only) |

## A-D04 / A-D05: Statistical limits and class definitions

- Windows are repeated measures; the independence unit is the family (39 primary / 32 extended among eligible runs).
- Report coverage with every selective risk. Report family-level tables alongside pooled metrics.
- Uncertainty: paired family bootstrap (Faisal F-D13). With 3 topologies, between-fold variation must not be read as sampling uncertainty.
- Practical significance: recommend **effect sizes only**, unless you and Faisal approve a justified threshold *before* any outer-test run.
- Class definitions are pending, jointly with Yazan and Faisal:
  - a multi-location leak counts as LEAK (Y-D05d);
  - post-delay rows are excluded rather than relabelled (Y-D06a);
  - compound events are exploratory only (Y-D05c).

## A-D06: Dataset description, corrections to adopt

| Topic | Correct statement | Evidence |
| --- | --- | --- |
| Files vs runs | 264 archive files, 242 tabular files, **57 simulated runs**, 51 eligible | `evidence/INVENTORY_RECONCILIATION.csv` |
| Realizations | each run has a clean simulation and a noise-added release (white Gaussian noise per the ReadME, numerically verified); 3 runs also have a `_noisy` variant; 3 normal runs have raw solver exports | `pre_experiment_review/DATASET_RECONCILIATION_REPORT.md` |
| Sampling | 1 s, verified from the stored `Timestamp` index of every Parquet file; solver exports 0.8–0.9 s | `raw_verification/TIME_AXIS_AUDIT.csv` |
| Origin | MATLAB R2025a Simscape Gas Fluids (REPORTED, dataset ReadME); three withdrawal topologies of one network | ReadME |
| Composition | "hydrogen blend" per the Zenodo title; **10% H₂ / 90% CH₄ is UNVERIFIED** (not in the ReadME, scripts or model XML) | `RAW_DATASET_VERIFICATION_REPORT.md` §5 |
| Labels | row-level binary step labels; documented conflicts L1 and L2; delay labelled 25–1000 s | `pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md` |
| Exclusions | 6 runs (3 compound, 3 annotation conflict) | manifest |
| "Peer-reviewed dataset" (README) | UNVERIFIED: the ReadME cites two 2025 papers, but no peer-review status was checked | — |

## A-D07: Mathematical consistency (code vs register; reviewed by reading the code and confirmed by closed-form tests)

| Quantity | Register | Code | Consistent? |
| --- | --- | --- | --- |
| p(x) | classifier probability, simplex | `baseline._aligned_proba` (absent classes get 0); `comparators.validate_probabilities` | ✔ |
| ŷ(x) | argmax p | `argmax`, ties go to the lower class index (baseline, policy) | ✔ (tie rule must be documented) |
| q(x) | class support among k nearest reference windows | **tie-inclusive** neighbourhood (k_eff ≥ k when distances tie) | ⚠ Intentional deviation: makes q order-invariant. State it in the methodology |
| D(x) | q₍₁₎ − q₍₂₎ | same; D = q₍₁₎ if K = 1; NaN only for invalid input or no reference | ✔ |
| C, M, H | max p; p₍₁₎ − p₍₂₎; −Σ p log p | same; **natural log**; 0 log 0 = 0 | ✔ (state the log base) |
| Coverage, selective risk | N_SPECIFIC / N_eligible; errors / N_SPECIFIC | `metrics.coverage_and_risk`; risk undefined (flagged) if N_SPECIFIC = 0 | ✔ |
| Ambiguity set | 2 ≤ \|S\| ≤ K−1, from a mass rule | `policy.apply_policy`; all-class sets prevented | ✔ |
| Prediction vs diagnosis | separate | ŷ in prediction tables; g(x) in policy output | ✔ |
| Thresholds | development only | `PolicyConfig.threshold_source == "development"` enforced | ✔ |
| s_C, s_{C−D} | LR on logit C, M, −H (± D) | **not implemented** | ✘ open (F-D10) |

## A-D08 … A-D11

- Adopt `SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md`.
- Reconcile documentation:
  - README §2: says "23 passing tests"; the suite now has 159 tests.
  - README §6: describes the quarantined illustrative figures as research figures.
  - README §7: "zero leakage" and the 3-fold claim; the original folds leak.
  - `05_documentation/FIGURE_SPECIFICATION.md`.
  - Rewrite these yourself; no edit was applied to approved or team-owned text.
- Re-record Gates 1–3.
- Add the "New Plan 2" PDFs to `assets/`.

## A-D08 gate package: what must exist before the final freeze

1. Yazan approvals Y-D01…Y-D08, plus manifest v0.2 hash.
2. Faisal approvals F-D01…F-D18, plus frozen config hash.
3. Your decisions A-D01…A-D05 and A-D10.

**Reopening conditions:** any change to the manifest, label mapping, family map, folds or config hash reopens every dependent decision listed in `APPROVAL_DEPENDENCY_GRAPH.md`.
