# Policy Threshold Selection (F9/F10)

- **Status:** SPECIFIED from `primary_protocol._rank_threshold` and `exact_count_selection`; TESTED (`tests/test_tie_policy.py`, `test_primary_protocol.py`).
- **Config:** `thresholds` (source: development; targets 0.80 primary, 0.60 and 0.90 secondary; `matched_coverage` = PA-1).

## Definitions

- **Eligible set E:** windows with a finite score, valid probabilities, and no unresolved or specific-blocking flag under the evaluated policy variant (primary or warning_only).
- **Denominator n:** all eligible windows of the evaluated set (development fold, or outer-test fold).
- **Requested count:** m = ceil(target · n), with a 1e-9 guard so that 0.6 · 10 gives 6.

## 1. Development threshold (threshold-transfer mode)

- Computed on development out-of-fold scores only: τ = the m-th largest score in E.
- If m > |E| → `NOT_ESTIMABLE_UNDER_PRIMARY_PROTOCOL`, recording `dev_max_attainable_coverage = |E|/n`.
- `dev_realized_coverage_at_tau` is recorded. Ties at τ are all accepted when τ is transferred, because a deployable threshold cannot split ties.
- At outer test, τ is applied unchanged. Realized coverage and risk are reported and never forced.

## 2. Rank-matched mode (primary RQ1; protocol amendment PA-1)

- On the outer-test fold, without labels, select exactly m windows from E, ordered by score descending, then by SHA-256(`h2prism-pa1-v1|window_id`) ascending.
- The same key is used for every method, so s_C and every comparator have **identical SPECIFIC counts** per fold (asserted).
- If m > |E| → NOT_ESTIMABLE; the comparison is reported as not estimable, never zero.
- `estimability.csv` records requested count, realized count, realized coverage, ties at the boundary, and tied windows selected.
- **Tie-order sensitivity:** 20 alternative salts (secondary). Pooled risk differences per salt go to `tie_sensitivity.csv`, alongside the primary difference. They are never used to choose a result.

**Prohibited:** choosing targets, salts or thresholds after seeing outer-test outcomes; relaxing flags to reach a target.
