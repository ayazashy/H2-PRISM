# Formal D(Y) validation — verdict C

D(Y) = (H_consistent, H_excluded, H_indeterminate). Evidence comes from Results R4–R8 and tables A04, A05 and A08–A10.

## Verdict by aspect

| Aspect | Verdict | Evidence |
|---|---|---|
| Mathematical correctness | **VERIFIED on these inputs** | Bound widening, clock widening and sensor removal: 0 forbidden transitions in 25,024 paired hypothesis checks. Every exclusion certificate (11,061) and feasibility witness (1,552) re-verifies independently in exact rationals. |
| Conditional capability | **DEMONSTRATED (Center, hypothetical bounds)** | All three outcomes occur. Library dependence is quantified (A05). Missing evidence produces ambiguity or MODEL_MISMATCH abstention rather than new exclusions (A08, A09). |
| Real uncertainty qualification | **NOT ESTABLISHED** | Bounds are a declared ladder; REF is a solver-refinement scale, not an enclosure. |
| Physical validation | **NOT ESTABLISHED** | Air-like simulation with an unphysical γ; one source family; six captures. |

## Failure modes, all observed conditionally

1. **Truth absent and a rival consistent: wrong SPECIFIC.** Removing the true hypothesis gives 2 wrong SPECIFIC and 4 ambiguity sets without the truth out of 42 decisions.
2. **Flow-blind events.** SID 215 is formally inseparable from normal operation at the REF bounds even with all 13 channels (template-level isolability). The restricted universe therefore decides "normal operation" at S5 and REF. Losing pressure makes this worse (flow-only: 4 wrong out of 24).
3. **Ambiguity sets need not contain the truth.** Removing MFS1 swaps the 2 wrong SPECIFIC decisions for 4 ambiguity sets without the truth. A low wrong-SPECIFIC count is therefore not, by itself, a safety improvement.

## What D(Y) adds beyond conventional baselines

**A different safety mechanism, yes.** D(Y) can refuse to decide because the declared library is incomplete: in the full universe all 42 decisions are UNRESOLVED. It also states exclusions as verifiable interval certificates in physical units. No confidence score provides either.

**Does it reduce wrong SPECIFIC decisions under a fair comparison? Not testable.**

- No classifier was run on the same Center queries, and no qualified bounds exist.
- On Center the only comparator is the nearest-mechanism rule, which uses no bounds.
  - Leave-own-template-out recognition (TAB_C02): it is wrong for 2 of the 5 supported queries and routes the timing intervention to withdrawal.
  - In the full universe, D(Y) issues no SPECIFIC decision, so it cannot be wrong.
  - In the restricted universe, D(Y) is wrong 2 times out of 10 SPECIFIC decisions, both through failure mode 2.
  - Coverage is not matched across these comparisons, so they are descriptive only.

## Auditable evidence states

These are an interpretation of the formal outcomes, not a new validation result.

| State | Formal outcome | Count in E1–E4 (2,376 decisions) |
|---|---|---|
| Sufficient for one hypothesis | SPECIFIC | 675 (572 correct, 103 wrong) |
| Consistent with several | AMBIGUOUS | 318 (160 with the truth, 158 without) |
| Outside the modelled space | UNRESOLVED / MODEL_MISMATCH or INDETERMINATE_HYPOTHESES | 1,383 (1,338 + 45) |
| Invalid evidence | UNRESOLVED / INVALID_MEASUREMENT | 0 in these runs. The engine path is covered by `tests/test_certified_evidence.py` (invalid uncertainty, measurement gap, misaligned timestamps). |

Counts are over repeated, deliberately degraded views of six captures. They are not rates.

## Traceability (A18)

- The engine certificate carries **12 of 16** required provenance fields.
- The frozen JSON export carries **7 of 16**.
- **Missing:** predicted trajectories, residuals, model-bound values inside the certificate, and the source-model version.
- **Exclusion certificates** are verifiable in memory, but the frozen record does not persist them. Persisting them is the most useful engineering fix for auditability.
