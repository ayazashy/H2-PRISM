# Minimum requirements for a confirmatory H1 test (Pathway C)

The table with current status is `tables/H1-T08.csv`. This file states the blueprint.

## 1. Evidence base

1. **Labels and attribution.**
   - Source models are verified per run before any model access.
   - For the released data this needs D1 (Yazan). For new data, generation logs must record the model.
2. **Independent units.**
   - Evaluation scenario ancestors (templates) must be disjoint from development ancestors.
   - Topology replicas of one template count as **one** unit.
3. **Class support.** ≥ 2 independent ancestors per class in development and ≥ 2 in evaluation. No universal number is asserted beyond this structural minimum.
4. **Estimability before unblinding.**
   - On development data, the registered target coverage (0.80) must be attainable in each stratum under the frozen flag rules.
   - Concretely: ≥ 80 % of windows must have ≥ 2 top-class families and ≥ 2 scenarios among their k = 25 neighbours.
   - If not attainable, the protocol is revised **before** any test access.

## 2. Locked analysis

| Element | Requirement |
|---|---|
| Hypothesis | H1 as stated in `H1_EXECUTION_DECISION.md` §1, unchanged |
| Estimand | Δ_R = R_sel(s_C) − R_sel(s_C−D) at rank-matched coverage 0.80 (PA-1), plus the conventional-confidence contrast as a pre-declared secondary |
| Calibration | fitted on development groups only; selection rule frozen |
| Thresholds and tie key | frozen config hash; tie salt `h2prism-pa1-v1` |
| Unit and interval | scenario-ancestor paired bootstrap (stratified if ≥ 2 ancestors per stratum), 2,000 replicates, fixed seed, 95 % percentile |
| Test access | access-controlled partition, opened once after the protocol hash is recorded |

## 3. Decision rules (pre-registered)

| Outcome | Rule |
|---|---|
| **Supported within registered scope** | Δ_R(0.80) < 0, the 95 % ancestor-level interval entirely below 0, estimable in every stratum, and SPECIFIC decisions in ≥ 2 classes |
| **Not supported (genuine failure of H1)** | Δ_R(0.80) ≥ 0, or the interval includes 0 while its half-width is ≤ the pre-declared precision |
| **Inconclusive** | interval includes 0 with half-width above the pre-declared precision |
| **Not estimable** | target unattainable in any stratum (reported, never replaced by a lower target) |

## 4. Precision planning (heuristic)

- **Observed spread:** on the inspected R2 data, the ancestor-level bootstrap SD of Δ at c = 0.20 is 0.052 (17 ancestors).
- **Scaling assumption:** if the SD scaled as 1/√n, a ±0.10 half-width would need ≈ 18 independent ancestors, and ±0.05 ≈ 71.
- **Caveat:** these numbers come from defect-driven errors and may not transfer. They are an order-of-magnitude planning input, not a sample-size requirement.

## 5. Minimum path from the current repository

| Step | Unblocks | Gate |
|---|---|---|
| 1. Yazan records D1 (A/B/C) | the corrected exploratory replication (Experiment F) | dataset owner |
| 2. Run the replication with `scripts/h1_analysis.py` on its outputs | whether a nontrivial shared coverage region and nonzero independent errors exist after correction | project-lead authorization |
| 3. Generate new independent scenario ancestors (H2Net v1 design) | a genuinely untouched evaluation | simulation authorization + D2 |
| 4. Confirmatory run under §2–3 | an H1 verdict | confirmatory authorization |

**Steps 1–2 cannot confirm H1**, because every R2 window has been inspected. Only steps 3–4 can.
