# Monotonicity of the formal D(Y) under information removal and widened uncertainty

Scope: `h2prism.certified_evidence.diagnose` used with `h2prism.center_enhancement.TemplateEnvelopeAdapter`. The guarantee is mathematical and conditional. It holds for this adapter only. It says nothing about whether the templates or bounds are physically right.

## Setting

- A measurement Y has coordinates k = (channel c, time i). Each coordinate has a closed observation interval O_k = [y_k − e_obs(c), y_k + e_obs(c)]. These are exact rationals built from the float inputs.
- A hypothesis h is a finite set of trajectories T_h. Each trajectory comes from one template at one admissible integer clock shift. Each value has a model half-width e_mod(c), so its predicted interval is P_{h,s,k} = [s_k − e_mod(c), s_k + e_mod(c)].
- The adapter returns exactly one status per hypothesis:
  - **EXCLUDED** if some coordinate k has hull interval H_{h,k} = [min_s s_k − e_mod(c), max_s s_k + e_mod(c)] disjoint from O_k. It emits that coordinate as an interval-separation certificate.
  - otherwise **FEASIBLE** if some trajectory s has P_{h,s,k} ∩ O_k ≠ ∅ for every k. It emits s as the shift witness.
  - otherwise **INDETERMINATE**.
- `diagnose` re-verifies every exclusion certificate against the measurement. A result it cannot verify becomes INDETERMINATE (`INVALID_ADAPTER_RESULT`).

## Assumptions

1. **A1.** The hypothesis set is fixed. No hypothesis is added, removed or renamed between the two evaluations.
2. **A2.** Templates and their values are unchanged. Only the following relaxations are allowed:
   - **R1.** Remove a subset of channels (coordinates).
   - **R2.** Increase e_obs or e_mod for any channel kind.
   - **R3.** Add admissible trajectories to T_h (wider shift set).
3. **A3.** Intervals are closed. Separation is strict (hull upper < observation lower, or hull lower > observation upper).
4. **A4.** Comparisons are decided in exact rationals. The float prefilter (tolerance 1e-9 · max(1, |template|)) only preselects candidates. It never discards an exact witness: at an exact witness the float violation is a rounding error, far below the tolerance, at the magnitudes used.
5. **A5.** The measurement is valid both before and after the change (no `issues()`); otherwise every status is INDETERMINATE by construction.

## Claims

**Lemma 1 (witness persistence).** If s is a witness for h before a relaxation, s is still a witness afterwards.

- Under R1, the remaining coordinates are a subset, so the per-coordinate overlap conditions still hold.
- Under R2, both P and O only grow, and nonempty intersections stay nonempty.
- Under R3, s stays in T_h.

**Lemma 2 (no hull separation next to a witness).** If h has a witness s, no coordinate separates h. For every k, P_{h,s,k} ⊆ H_{h,k} and P_{h,s,k} ∩ O_k ≠ ∅, so H_{h,k} ∩ O_k ≠ ∅.

**Lemma 3 (separation cannot appear).** If no coordinate separated h before a relaxation, none separates it afterwards.

- Under R1, there are only fewer coordinates.
- Under R2 and R3, H_{h,k} and O_k only grow, so an overlap persists.

**Theorem.** Under A1–A5, for every hypothesis, the status after any composition of R1–R3 satisfies:

| Before | After |
|---|---|
| FEASIBLE | FEASIBLE (Lemmas 1 and 2) |
| INDETERMINATE | INDETERMINATE or FEASIBLE (Lemma 3: never EXCLUDED) |
| EXCLUDED | any status (the separating coordinate may be removed or its intervals may come to overlap) |

**Corollary (safety of the decision).**

- If the true hypothesis was FEASIBLE, it stays in the candidate set after any relaxation.
- A SPECIFIC decision can only:
  - stay SPECIFIC on the same hypothesis;
  - become AMBIGUOUS with the same hypothesis still a candidate;
  - become UNRESOLVED (INDETERMINATE_HYPOTHESES).
- So a relaxation can never turn a correct SPECIFIC decision into a wrong one. A relaxation can, however, turn MODEL_MISMATCH into SPECIFIC on a hypothesis that is not true, when an EXCLUDED hypothesis becomes FEASIBLE. Relaxation is therefore not safe in that direction, and this is not claimed.

## What is not covered

- **Perturbed data.** Bias, drift, noise, a stuck channel or timestamp jitter change the observation itself, not its bounds. None of the claims applies. Those cases are studied empirically, and labelled SYNTHETIC, in `04_results/analysis/s1_dy_synthetic_stress_*.csv`.
- **Changing the hypothesis set** (A1). Removing the true hypothesis can produce a wrong SPECIFIC decision; v1 experiment E4 `minus_true` showed exactly this.
- **Physical adequacy** of templates, bounds and shifts. The bounds are hypothetical; REF is the solver-refinement delta, not a sensor specification.

## Verification

- `tests/test_dy_adversarial.py` holds 40 seeded property tests over R1, R2 and R3 (transition table above) plus boundary, invalid-input and forged-certificate tests.
- In v1, 25,024 transition checks on the Center experiments found 0 violations.
- Passing tests show that the implementation agrees with the argument on the cases tested. They do not prove a scientific hypothesis.
