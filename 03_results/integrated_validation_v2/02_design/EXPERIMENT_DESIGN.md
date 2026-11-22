# 02 — Experiment design

## Original versus revised protocols
- **Original (registered, unchanged).** R2 RQ1: s_C vs s_C − D at matched coverage 0.6, 0.8 and 0.9, using three held-out topologies. Status NOT_ESTIMABLE (12/12 PRIMARY rows).
- **Revised (this round, secondary).** No registered target was lowered. The new analyses do the following:
  1. Test D(x)'s incremental information with template-grouped cross-validation on frozen scores.
  2. Qualify the formal D(Y) with a proof, adversarial tests and SYNTHETIC stress.
  3. Separate structural from bound-limited isolability.
  4. Port one external rule to the engine (HY2RES Level A).
- None of these replaces H1.

## Hypothesis registry
`HYPOTHESIS_REGISTRY.csv`. Only H1 was registered before evaluation; H2–H10 are secondary.

## Independence rules and partitions
- R2: the independent unit is the scenario ancestor/template (17), then the family (39). Windows and runs are dependent.
- Template-grouped CV never places one template in both fit and evaluation.
- Center: one capture per mechanism (plus a near-duplicate replicate for SID 213). Results are counts over repeated views, not rates.
- HY2RES: chronological development/test split with zero shared segments. The test partition was inspected before (L18).

## Comparators
- H1: s_C − D (registered); confidence, margin, entropy and D-only with the evidence guard; unguarded confidence; no abstention.
- D(x) utility: [logit conf] and [logit conf, margin, −entropy].
- Localization: forced and top-k nearest template.

## Coverage definitions
- coverage = SPECIFIC / all decisions in the stated population.
- wrong-specific risk = wrong SPECIFIC / SPECIFIC.
- A candidate set without the truth is never counted as correct.

## Statistical analysis plan
- Report units and counts first; intervals only from ancestor/family bootstrap; no significance claims.
- Every comparison run is reported, including negative ones.
- Synthetic results are labelled and kept out of claims about the field.

## Experiment feasibility and status
`EXPERIMENT_STATUS.csv` (45 experiments). By status:
- EXECUTED: 15
- EXECUTED (v1): 9
- NOT_EXECUTED: 5
- EXECUTED (SYNTHETIC): 4
- BLOCKED_BY_DATA: 2
- EXECUTED (registered; NOT_ESTIMABLE): 2
- PARTIAL: 1
- BLOCKED_BY_PROVENANCE: 1
- EXECUTED (v1, reproduced by verify_av): 1
- EXECUTED (EXPLORATORY): 1
- NOT_ESTIMABLE: 1
- EXECUTED (v1) + hypothetical cost scenarios: 1
- BLOCKED_BY_PHYSICS: 1
- EXECUTED (no prices): 1
