# Ahmed: Scientific Resolution (Phase 6)

All items are RECOMMENDED_FOR_APPROVAL or PROVISIONALLY_SELECTED, with signoff **PENDING_HUMAN_SIGNOFF**. No result exists.

## C1. RQ1 (incremental value of D beyond C, M, H)

| Aspect | Assessment |
| --- | --- |
| Testability | Testable: s_C vs s_{C−D} on identical windows, folds and thresholds |
| Inference strength | Limited: 3 held-out topologies; 39 primary families; LEAK is 39 of 51 eligible runs (76%), so pooled results are LEAK-dominated |
| Effect size | Primary output: difference in selective risk at matched coverage, with a topology-stratified family bootstrap interval |
| Class-specific claims | Not supported for NORMAL, FAULT and DELAY (descriptive) |
| Population generalisation | Not supported beyond held-out topologies of this simulated network |

## C2. RQ2 operational criteria (fixed before any experiment)

| Outcome | Criterion |
| --- | --- |
| Correct SPECIFIC | ŷ = y among SPECIFIC; report selective risk **with** coverage |
| Informative AMBIGUITY_SET | \|S\| = 2 (the max set size), y ∈ S; report the inclusion rate and the size distribution together; a set is *informative* only if inclusion ≥ the inclusion rate of the top-2 classes by prior frequency (fixed baseline) |
| UNRESOLVED | rate and reason codes, by class |
| Decision stability | agreement of outcomes between the noise-added and clean realizations of the same run (secondary) |
| Reproducibility | identical outputs on re-run (hash) |

## C3. Claim boundaries

See `SCIENTIFIC_LIMITATIONS_AND_CLAIMS.md`. Prohibited: deployment readiness, field validation, industrial generalisation, physical identifiability, metric localisation, pure-H₂, verified 10% blend, superiority of D. Software tests are not scientific evidence.

## C4. Mathematical consistency (code re-read in Phase 6)

- p, q, D, C, M, H, coverage, selective risk, sets and thresholds are as recorded in `phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md` (A-D07).
- New combined score: `combined_score.py` uses features [logit C, M, −H, (D)] → standardisation → logistic regression for P(correct). This **matches** the plan definition s_C = LR[logit C, M, −H, D]. Cross-fitted by group; development only.
- Document in the methodology:
  1. tie-inclusive k-neighbourhood;
  2. natural-log entropy;
  3. the s scores are calibrated *probabilities of correctness*, not class probabilities;
  4. the new `TOP_CLASS_FEW_INDEPENDENT_RUNS` flag.

## C5. Reviewable documentation changes (prepared, NOT applied to team-owned files)

| File | Replacement text |
| --- | --- |
| README §2 | replace "23 passing tests" with "test status: see `06_audit_preparation/phase6_resolution/IMPLEMENTATION_AND_TEST_REPORT.md`" |
| README §6 | "Figures 3–6 and the dashboard are illustrative mock-ups generated from invented values and are quarantined in `03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/`. No experimental figure exists yet." |
| README §7 | replace "zero leakage / 3-fold topology CV with all classes" with "Candidate leave-one-topology-out folds (pending sign-off) are family- and duplicate-disjoint; the original `01_dataset_audit/folds.csv` leaks and must not be used." State 57 runs / 51 eligible, H₂ fraction unverified |
| Dataset description | text from `phase4_approvals/AHMED_SCIENTIFIC_REVIEW_DOSSIER.md` A-D06 |
| `05_documentation/FIGURE_SPECIFICATION.md` | mark Figs 3–6 as placeholders bound to the F10 outputs listed in `configs/reporting_figures.yaml` |
| Gate records | re-record Gates 1–3 as CONDITIONAL / PENDING after Y-D08 |

## C6. Inference protocol (fixed now; no post-hoc RQ changes)

| Observed | Report as |
| --- | --- |
| C better than C−D, interval excludes 0 | "within the evaluated simulated topologies, adding D reduced selective risk by X (interval conditional on 3 topologies)", with no superiority or generality claim |
| No measurable difference / interval includes 0 | "no evidence of incremental value at this sample size" (inconclusive ≠ equivalence) |
| C worse | report as a negative finding with the same prominence |
| Effects differ by topology | report the per-topology estimates; no pooled claim beyond "heterogeneous" |
| Thin classes | descriptive only, whatever the pooled result |

## C7. Readiness recommendation

The scientific framing is consistent with the evidence once the restrictions above are adopted. Ahmed must sign A-D01–A-D10 (sheet: `phase5_decisions/AHMED_SIGNOFF.md`). The scientific freeze is **not** issued.
