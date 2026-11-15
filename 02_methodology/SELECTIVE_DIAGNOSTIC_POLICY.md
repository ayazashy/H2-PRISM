# Three-Outcome Selective Diagnostic Policy (Faisal F9)

## Frozen threshold and candidates

The `C` ranking score is \((C+M+(1-H)+D)/4\). For each outer fold, choose the
80% target-specific-coverage threshold from inner grouped OOF training
predictions only. Apply this threshold unchanged to outer-test observations.
Actual test coverage may differ from 80%; it is always reported alongside
selective risk.

Candidate classes are the union of classes whose calibrated probability is
within 0.15 of the maximum probability and classes whose empirical support is
within 0.15 of maximum \(q\), with zero-support classes omitted. If more than
three classes qualify, retain the three with the largest combined
probability-plus-support score and mark the set truncated.

## Outcomes

- `SPECIFIC`: combined score clears the development threshold and the candidate
  set has exactly one class.
- `AMBIGUITY_SET`: at least two candidates remain and either maximum calibrated
  confidence is at least 0.40 or maximum class support is at least 0.35.
- `UNRESOLVED`: neither rule supports a specific diagnosis or informative
  ambiguity set.

Each prediction stores `policy_outcome`, `ambiguity_set`, candidate count,
truncation flag, threshold, and a reason code. These are policy parameters
frozen in `configs/frozen_evaluation_config.yaml`; they are not chosen from
outer-test labels. This policy reports diagnostic abstention behavior and does
not assert calibrated set coverage.
