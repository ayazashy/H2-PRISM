# Empirical Distinguishability D(x): Mathematical Specification (F7)

- **Status:** SPECIFIED from `src/h2prism/distinguishability.py`; IMPLEMENTED and TESTED.
- D(x) is an **empirical neighbourhood statistic, not physical identifiability**. No value of D has been demonstrated on project data.
- Companion documents: `D_STATISTIC_IMPLEMENTATION_SPEC.md` (implementation detail), `D_STATISTIC_EDGE_CASES.md`, `D_STATISTIC_DESIGN_DECISION.md`.

## Definitions

Let the reference set R hold labelled windows (r, y_r, family_r, scenario_r) from the development data only, and let x be a query window with family f(x).

```
z(v)      = (v − μ_R) ⊘ σ_R          μ_R, σ_R: per-feature mean and population SD on R (σ = 1 if constant)
R(x)      = { r ∈ R : family_r ≠ f(x) }                            (own-family exclusion)
d_r(x)    = ‖z(x) − z(r)‖₂ ,  k_av = min(k, |R(x)|),  d_(k)(x) = k_av-th smallest d_r(x)
N(x)      = { r ∈ R(x) : d_r(x) ≤ d_(k)(x) + 1e-12 }               (tie-inclusive; |N(x)| ≥ k_av)
s_c(x)    = Σ_{r∈N(x), y_r=c} w_r ,  w_r = 1 (uniform; primary)
s_c(x)   ← s_c(x)/π_c  with π_c = |{r∈R(x): y_r=c}|/|R(x)|         (only if prior_correction; s_c = 0 if π_c = 0)
q_c(x)    = s_c(x) / Σ_c' s_c'(x)                                    (q(x) ∈ Δ^{K−1})
D(x)      = q_(1)(x) − q_(2)(x),  ordering ties broken by the lower class index;  D ∈ [0, 1]
```

## Properties (tested)

- Invariant to the row order of R (tie inclusion).
- No NaN from absent classes (q_c = 0).
- The query label is never an input.
- D = 1 with weak support is **not** strong evidence: the flags qualify it.

## Reference construction in the protocol

| Stage | Query | R | Family exclusion |
| --- | --- | --- | --- |
| Development (per outer fold) | development windows of topology t | development windows of the **other** development topology | implied (families nest in topology) plus explicit |
| Outer test | outer-test windows | **all** development windows of the fold | explicit (disjoint by assertion) |

The out-of-support threshold is the 0.99 quantile of leave-one-family-out mean neighbour distances, computed on R only.

**Known asymmetry:** the reference is one topology in development and two at outer test. Test-time support is therefore larger than during combined-score fitting. This is recorded as a design limitation (`D_STATISTIC_DESIGN_DECISION.md`).

## Primary parameters (config `distinguishability`)

- k = 25, uniform weights, prior_correction = false, exclude_query_family = true.
- min_class_reference = 25, min_distinct_scenarios = 2, low_support_min_top_count = 5, min_top_class_families = 2.
- OOS quantile 0.99.
- Registered sensitivities: `k_10`, `k_50`, `prior_correction`.
