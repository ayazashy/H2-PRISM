# Advanced validation — predeclared protocol (written before any new decision was computed)

- **Date:** 2026-11-18.
- **Base commit:** `e944e1b`.
- **Applies to:** every analysis in `advanced_validation/`.

## Fixed rules

1. **No frozen artifact is modified, and no model is trained or refit.** Labels, partitions, thresholds, tie keys, calibration and the formal engine stay as frozen.
2. **R2 analyses.** They reuse the frozen R2 predictions (hash-pinned) and the registered rank-matched exact-count selection.
   - The coverage grid is the one fixed by the R2 diagnostics: {0.05, 0.10, 0.15, 0.20, 0.25}.
   - Everything is EXPLORATORY_POST_HOC.
   - The independent unit for intervals is the scenario ancestor (17). The registered family unit (39) is reported alongside.
3. **Center formal D(Y).**
   - It uses the frozen engine and the accepted Center construction, with the frozen bound ladder S1–S6 and REF, the eps split 0.5/0.5 and the 30 s window.
   - Every result is CONDITIONAL_HYPOTHETICAL_BOUNDS. Counts come from repeated views of six captures, not independent trials.
4. **E1 sensor configurations, fixed before running.** The set has 79 configurations:
   - all 13 channels; pressure-only (10); flow-only (3);
   - each single-channel removal (13);
   - three outlet-branch outages, defined by the accepted relevant-sensor lists: SID 213 = {MFS3, PS1}, SID 312 = {MFS1}, SID 215 = {PS4, PS8, PS9};
   - 20 random masks each removing 3, 4 and 7 channels. These approximate 20 %, 30 % and 50 % of 13. Seed 20261118. 10 % is one channel, which is covered exhaustively by the single removals.
   - Scenarios: S3, S4, S5, REF. Clock bound ±1 s. Restricted universe. The full universe is UNRESOLVED by construction (unmodelled hypotheses), which was verified on the frozen grid.
5. **E2 admissible clock bound:** τ ∈ {0, 1, 2, 5, 10} s, with no observation delay. These values are multiples of the 0.2 s sample step and fit the 30 s window and padding.
6. **E3 fixed observation delay:** d ∈ {0, 1, 2, 5, 10} s. The observed signal lags the process by d. It is evaluated with τ = 1 s (unchanged bounds) and with τ = max(1, d) (widened admissible alignment).
   - Timestamp jitter is **not** executed: the captures come from a fixed-step simulation clock, and the engine flags any non-uniform grid as INVALID_TIME_GRID or IRREGULAR_SAMPLING. A jitter study needs a declared jitter model and resampling rule, and those would change the measurement contract.
7. **E4 hypothesis library:** four variants over all seven scenarios:
   - restricted (modelled hypotheses);
   - restricted minus NORMAL_OPERATION (missing operating rival);
   - restricted minus the true hypothesis (missing truth);
   - the full declared universe.
   - An unrestricted UNKNOWN hypothesis without an adapter is **not** added. It would be indeterminate by construction, so it is identical to the full universe.
8. **Mathematical invariants tested on paired runs with frozen bounds.**
   - **Allowed status transitions** when information is removed (sensor removal), or when the admissible uncertainty or clock set is enlarged:
     - FEASIBLE → FEASIBLE only;
     - EXCLUDED → any status;
     - INDETERMINATE → INDETERMINATE or FEASIBLE.
   - Any other transition counts as a violation.
   - **Sensor nesting:** each configuration is compared with the all-channel run, which is its superset.
9. **Certificate re-verification.** Every EXCLUDED certificate (disjoint interval on a declared coordinate) and every FEASIBLE witness (exact-rational re-check of the shifted trajectory) is re-verified independently of the engine.
10. **Localization metrics.** These use only queries with an independent same-outlet template. Repeated captures of one outlet are never counted as independent locations.
