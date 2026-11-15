# Uncertainty and Distinguishability Comparators (Faisal F8)

The comparators use calibrated four-class probabilities \(p\), normalized
entropy \(H\), and family-excluded empirical support \(q\):

| Indicator | Definition | Higher means |
|---|---|---|
| Confidence \(C\) | largest class probability | greater model confidence |
| Margin \(M\) | largest minus second-largest class probability | larger probability separation |
| Entropy \(H\) | Shannon entropy divided by \(\log 4\) | greater uncertainty (therefore lower is preferred) |
| Distinguishability \(D\) | largest minus second-largest \(q_k\) | larger empirical class-support separation |

Three primary ranking scores are frozen:

- `B`: \(C\) (confidence-only).
- `C_minus_D`: \((C+M+(1-H))/3\).
- `C`: \((C+M+(1-H)+D)/4\).

Secondary single-indicator scores `B2=M`, `B3=1-H`, and `D_only=D` are
retained for ablation. All values are finite and bounded for valid probability
and support vectors. Missing-class support is retained as explicit diagnostics;
it is not imputed. An empty reference set is an error.

Methods are compared on the same outer-test windows. Report coverage with
selective risk and include family-clustered uncertainty; do not treat windows
as independent replicates.
