# Preparation Implementation Plan (dependency-aware)

Each row lists the work performed on this branch, followed by the work that remains. Priorities follow the mission order: correctness, then breakage, then interfaces, leakage, tests, provenance, scaffolding, support modules, documentation.

| # | Task | Owner | Missing component (before) | Change made | Prerequisites | Acceptance criterion | Tests | Artifact | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | ISS-03 | Ahmed | Fabricated figures and KPIs in the results folder | Quarantined and labelled; demo writes only to quarantine | none | No invented value appears as a result | test_visualization | `03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/` | DONE (owner decision pending) |
| 2 | ISS-01/02 | Yazan / Faisal | No family- or content-level fold check | `splits.validate_outer_folds` + runner assertions | Y1 duplicate audit | Every leakage path in Y5 is asserted | test_splits, test_baseline | `FOLD_VALIDATION_*.csv` | DONE (detection); correction OPEN |
| 3 | ISS-13, ISS-12 | — / Yazan | Test collection broken; silent empty folds | Import fix; loader raises; checksum-verified fallback | none | Suite collects; no silent skip | test_data_loader, test_visualization | — | DONE |
| 4 | F3 | Faisal | io / windows / features modules | Implemented with required decision arguments | Y1, Y3, Y8 | Deterministic, leakage-safe on fixtures | 22 + integration | `src/h2prism/{io,windows,features}.py`, register | DONE (synthetic) |
| 5 | F4 | Faisal | Validator, inner splits | Implemented | Y2/Y5 corrections | All assertions pass on the frozen folds | test_splits | — | PARTIAL: design and frozen config BLOCKED |
| 6 | F5/F6 | Faisal | Grouped runner, calibration | Implemented | F3 table, F4 folds | Rerunnable; no outer tuning | test_baseline | — | DONE (synthetic) |
| 7 | F7 | Faisal | D(x) | Implemented with flags and spec | F2–F4 | Hand-calculated, permutation, exclusion, dominance tests | 17 | spec | DONE (synthetic); decisions OPEN |
| 8 | F9 | Faisal | Policy | Implemented with spec | F5–F8 | Plan test list | 11 | spec | DONE (synthetic); thresholds OPEN |
| 9 | F10 primitives | Faisal | Metrics | Implemented | — | Closed-form tests | 8 | `metrics.py` | DONE; meta-model and runner NOT_STARTED |
| 10 | A16 | Ahmed | Comparators, ablation arms | Implemented | F8/F9 | Closed-form, label-free | 11 | — | DONE (synthetic) |
| 11 | A14 | Ahmed | LR reference | Implemented via the shared runner | F3/F4 | Same schema and leakage rules | 5 | yaml, spec | DONE (synthetic) |
| 12 | A15 | Ahmed | Sensitivity arms | Implemented | F3/F4, Faisal arm approval | Same population; rule-based arms | 3 | yaml, spec | DONE (synthetic) |
| 13 | A12 | Ahmed | Validators | Implemented and executed | F12 contracts | Read-only, deterministic | 6 | validation outputs, provenance index | DONE; Faisal acceptance pending |
| 14 | A13 | Ahmed | Figure/table builders | Implemented; dry run fails clearly | A5, F6/F10 outputs | Fixtures never final; values unchanged | 6 | yaml | DONE; inputs pending |
| 15 | F2/A4 | Faisal / Ahmed | Formulation, symbols | Draft document | Y4 | Symbols consistent with code | (equation tests) | `02_methodology/` | DRAFT |

## Not attempted (out of scope or blocked)

- F10 correctness meta-model and the matched-coverage runner, F11 statistics: need F5–F9 outputs and Faisal's design decisions.
- A1–A3, A5 rewrite, A7–A11: Ahmed's scientific writing. A3 and A7 depend on corrected Y evidence.
- Any correction of Yazan's audit outputs (owner action).
