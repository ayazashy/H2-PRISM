# Advanced validation — acceptance gates

**Decision: ACCEPTED WITH LIMITATIONS (package level).**

When a gate fails or is conditional, the corresponding claim is limited as stated. Passing the package checks does not establish any blocked claim.

| Gate | Result | Evidence or limit |
|---|---|---|
| 01 Frozen results preserved | PASS | No tracked file outside the package changed (`AV_VERIFICATION.csv`). Frozen inputs are read hash-verified. |
| 02 Data provenance verified | PASS | R2 parquet and config hashes; Center capture hashes in the loader; gas property report hashes in the H2Net v1 folder. |
| 03 Source-label attribution understood | PASS | A03 L01; every R2 error decomposed by attribution (A02a). |
| 04 No unaddressed leakage in newly claimed performance | PASS (no performance claimed) | Every R2 number is labelled exploratory and confounded (L01, L04). Center counts are conditional. |
| 05 Independent units identified | PASS | 17 templates (R2); one supported location; six captures (Center). Counts are never presented as rates. |
| 06 H1 estimability and matched coverage | PASS | Registered grid and tie key; coverage matched; no extrapolation (AV-F01). |
| 07 No unjustified fault or location accuracy | PASS | Localization Level 2 for one outlet; classification accuracies are window-level, exploratory and inspected. |
| 08 Formal D(Y) mathematical checks | PASS | 0 violations in 25,024 checks; 11,061 certificates and 1,552 witnesses re-verified. |
| 09 Hypothesis-library incompleteness evaluated | PASS | E4, A05, AV-F04. |
| 10 Missing-sensor results preserve the real topology | PASS | 13 real channels; branch outages from the accepted relevant-sensor lists; no synthetic sensors. |
| 11 Timing scenarios preserve temporal semantics | PASS (conditional) | Delays are multiples of the 0.2 s step inside the captured horizon. Jitter excluded and documented. |
| 12 Gas results have qualified physical models | **CONDITIONAL → claim blocked** | Only pure-H₂ property tables exist. No diagnostic gas-transfer result is claimed. |
| 13 Cost results have verifiable assumptions | **CONDITIONAL → claim blocked** | No prices, so no monetary result. Only a parametric structure and measured CPU time. |
| 14 Published comparisons pass comparability | **FAIL for head-to-head → contextual only** | A17: all gates fail. No numeric head-to-head is given. |
| 15 Runtime and memory actually measured | PASS | `benchmarks/`; hardware recorded. |
| 16 No invented numbers | PASS | All numbers trace to analysis outputs or cited files. Blocked cells carry a status, not a value. |
| 17 Exact provenance for figures and tables | PASS | Captions list their sources. The manifest records SHA-256. |
| 18 Tests and reproducibility | PASS | 57/57 package checks; deterministic rerun of the full advanced pipeline (see `quality_control/AV_DETERMINISM.txt`); study test suites unchanged. |
| 19 Original registered H1 verdict intact | PASS | NOT_ESTIMABLE, unchanged. |
| 20 Unresolved requirements documented | PASS | A20; `H1_AND_LOCALIZATION_ASSESSMENT.md`; `GAS_COMPOSITION_TRANSFER_ASSESSMENT.md`. |

## Governance

D1 is still NOT_RECORDED, so the corrected-attribution replication was not run.

## The four verdicts

| Verdict | Finding | Detail |
|---|---|---|
| A — H1 | Registered: **NOT ESTIMABLE**. Exploratory: **INCONCLUSIVE**. | `H1_AND_LOCALIZATION_ASSESSMENT.md` |
| B — Classification and localization | Exploratory window-level accuracy on inspected data. Localization Level 2 for one outlet. | `H1_AND_LOCALIZATION_ASSESSMENT.md` |
| C — Formal D(Y) | Mathematically verified and conditionally capable. Not physically qualified. | `FORMAL_DY_VALIDATION.md` |
| D — Engineering practicality | See the breakdown below. | Topic reports |

**Engineering practicality (D), by component:**

| Component | Status | Detail |
|---|---|---|
| Sensor demand | Template-level | MFS1 + MFS3 suffice for the separable pairs (conditional) |
| Computation | Measured | Under 0.4 s per decision on one laptop core |
| Timing | Robust only within the declared τ | — |
| Hardware dependence | Measured on one CPU | — |
| Cost | Not quantifiable | — |
| Portability | Not demonstrated | The engine has run only on Center |
| Gas readiness | Level A only (software) | — |
