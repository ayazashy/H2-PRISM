# Formal engine verification (D(Y))

## Decision semantics
| Decision | Meaning |
|---|---|
| SPECIFIC | Exactly one declared hypothesis is FEASIBLE (shift witness); every other is EXCLUDED by a re-verified single-coordinate interval certificate. |
| AMBIGUOUS | Two or more are FEASIBLE and none is INDETERMINATE. |
| UNRESOLVED | INVALID_MEASUREMENT, or some hypothesis is INDETERMINATE, or none is FEASIBLE (MODEL_MISMATCH). |

## Guarantees and checks
- Proof under assumptions A1–A5: `02_design/DY_MONOTONICITY_PROOF.md`.
- Finite checks: 0 forbidden transitions in 25,024 hypothesis-status checks (4,032 paired decisions); exclusion certificates re-verified 11,061/11,061; witnesses 1,552/1,552; adversarial tests: forged certificate rejected, NaN/negative bounds/duplicate sensors/broken clock never SPECIFIC, contradictory sensors -> MODEL_MISMATCH.
- Adversarial tests in `tests/test_dy_adversarial.py`:
  - 40 seeded property cases;
  - invalid inputs, closed boundaries and zero width;
  - contradictory sensors;
  - a forged certificate.
  - The suite passes as part of the full run (`03_execution/logs/pytest_full.log`).
- The certificate checker in `diagnose` re-derives each exclusion from the measurement intervals. It does not trust the adapter's claim: forged certificates become INDETERMINATE.

## Limits
- **Library completeness (A1).** H9 is CONTRADICTED by direct counterexamples.
- **Bounds.** Every bound is hypothetical or computed (`01_audit/BOUND_ORIGIN_AUDIT.csv`); none is calibrated.
- **Perturbed data.** SYNTHETIC faults are outside the proof. Empirically, wrong SPECIFIC counts never exceeded the baseline, but selective risk rose (V2-T03).
- Passing tests show that the implementation agrees with the argument on the cases tested. They do not establish diagnostic validity.
