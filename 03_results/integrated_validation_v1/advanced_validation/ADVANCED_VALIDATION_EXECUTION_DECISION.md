# Advanced validation — execution decision

- **Base:** `e944e1b` on `research/integrated-validation`, verified clean at the start.
- **Governance:** D1 is NOT_RECORDED (`06_audit_preparation/protocol2/release_candidate/P2_0_RC1.yaml`: `yazan: NOT_RECORDED`). The corrected-attribution replication is therefore **not executed**. The exact specification of that replication is in `../h1_validation/H1_EXECUTION_DECISION.md` §8 and `03_results/validation/center_evidence_enhancement/EXPERIMENT_F_PROPOSAL.md`.
- **Protocol:** predeclared in `protocols/AV_PROTOCOL.md` before any new decision was computed.

## Verification of the starting facts

| Statement | Verified | Source |
|---|---|---|
| Registered H1 NOT_ESTIMABLE | yes; 12/12 rows | R2 `rq1.csv` |
| Source-folder attribution error | yes; 36/57 runs | `03_results/diagnostics/forensics/source_model_attribution.csv` |
| D1 outstanding | yes; NOT_RECORDED | `P2_0_RC1.yaml` |
| 17 independent templates behind 39 families | yes; recomputed from predictions | `h1_02_independence_units_check.csv` |
| Evaluation partitions inspected | yes; all R2 outer-test windows | R2 diagnostics; Protocol 2.0 |
| D(x) has no demonstrated incremental value | yes; development arms | `ARM_SUMMARY.csv` |
| D(Y) evaluated only under hypothetical bounds | yes | Center enhancement; label in every record |
| Center model is air-like | yes; R = 0.287 kJ/(kg·K), and the active perfect-gas constants are physically impossible (γ = 5.75) | `02_methodology/HYDROGEN_MODEL_SPECIFICATION.md` P1–P2 |
| Center localization supported for one outlet | yes; SID 213 only (2 near-duplicate captures) | TAB_C03 |
| MHC and HY2RES have no fault or location labels | yes | TAB_B08, TAB_H09 |
| No industrial transfer validation | yes | — |

## Candidate studies

**Priorities.**

| Code | Meaning |
|---|---|
| P0 | Execute if eligible |
| P1 | Execute if justified |
| P2 | Defer |
| BLOCKED | Cannot establish the intended claim with existing evidence |

**Table columns.**

| Column | Meaning |
|---|---|
| H1 | Direct relevance to H1 |
| Loc | Relevance to localization |
| D(Y) | Relevance to formal D(Y) |
| Data | Data available |
| Truth | Ground truth available |
| Units | Independent units |
| Validity | Expected statistical validity |
| Leak | Leakage risk |
| New? | Whether the result is new |

| # | Study | H1 | Loc | D(Y) | Data | Truth | Units | Validity | Leak | New? | Priority | Decision / deliverable |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Corrected-attribution R2 replication | high | — | — | yes (v0.3) | disputed | 17 templates | exploratory | inspected data | yes | **BLOCKED (D1)** | Specification only |
| 2 | R2 false-specific accounting (class, topology, confidence, attribution, ancestors), no-abstention baseline, discarded-case error rates | high | — | — | yes | R2 labels | 17 templates | exploratory | inspected | partly new | **P0** | A01, A02, AV-F01–F03 |
| 3 | R2 negative control on NORMAL windows (false LEAK calls) | medium | — | — | yes | R2 labels | **1 template** | descriptive | inspected | new | **P0** | A11 |
| 4 | D(Y) invariants: bound widening, clock widening, sensor removal | — | — | high | yes | not needed | not applicable (mathematical) | exact | none | **new** | **P0** | A04 |
| 5 | Independent certificate re-verification | — | — | high | yes | not needed | not applicable | exact | none | new | **P0** | A04, A18 |
| 6 | Hypothesis-library variants (missing truth, missing operating rival) | — | — | high | yes | configured | 6 captures | conditional | self-templates excluded | new | **P0** | A05, AV-F04 |
| 7 | Missing-sensor robustness (79 predeclared masks) | — | high | high | yes | configured | 6 captures | conditional | none | new | **P0** | A08, AV-F08 |
| 8 | Timing: clock widening and fixed delay | — | — | high | yes | configured | 6 captures | conditional | none | new | **P0** | A09, AV-F09 |
| 9 | Timestamp jitter | — | — | medium | **no jitter model** | — | — | — | — | — | **BLOCKED** | It needs a declared jitter or resampling model, which would change the measurement contract |
| 10 | Template-level pairwise isolability and exhaustive minimum sensor set | — | high | high | yes | not needed (model property) | 6 templates | conditional | none | **new** | **P0** | A16, AV-F07 |
| 11 | Localization levels and selective localization (H-Loc) | — | high | medium | yes | configured outlet | **1 supported location** | descriptive only | near-duplicate replicate | partly new | **P0** (honest accounting) | A06, A07, AV-F06 |
| 12 | Evidence availability vs decision outcome (channel count) | — | medium | high | yes | configured | 6 captures | conditional | none | new | **P0** | A10, AV-F10 |
| 13 | Leakage and overfitting register | high | high | medium | yes | — | — | — | — | partly new | **P0** | A03 |
| 14 | Runtime and memory scaling (D(Y) on real captures; D(x) on synthetic arrays) | — | — | — | yes | not needed | — | measured | — | new | **P1** | A14, AV-F12 |
| 15 | Cross-study portability matrix (code inspection) | — | — | — | yes | — | — | — | — | new | **P1** | A12 |
| 16 | Gas-composition qualification matrix (existing H2Net v1 tables, mixture probe) | — | — | — | partial | — | — | — | — | new | **P1** | A13. **No diagnostic transfer run is possible** |
| 17 | New gas-specific transient simulation campaign | — | — | — | **no model** | — | — | — | — | — | **BLOCKED** | Needs H2Net v1 model build (BLOCKED in `STATUS.md`) and authorization |
| 18 | Sensor cost model and cost–risk Pareto | — | — | — | **no prices** | — | — | — | — | — | **P1 (parametric only)** | A15: symbols and sensitivity. Uses sensor count as the only measured axis |
| 19 | Literature comparison | — | — | — | external | — | — | contextual | — | — | **P1** | A17. No head-to-head (comparability gate fails) |
| 20 | Traceability audit | — | — | high | yes | — | — | — | — | new | **P1** | A18 |
| 21 | New Evidence Sufficiency Index | — | — | — | — | — | — | — | — | — | **P2 / not proposed** | The objective axes (channel count, bound scenario, library completeness) already serve. A composite index without validation would be a new score built after the outcome |
| 22 | Open-set rejection (19.1) | — | — | high | **no unknown events** | — | — | — | — | — | **BLOCKED** | "Minus-true" library variants test a missing *modelled* mechanism, not open-set events |
| 23 | Retraining RF, SVM or XGBoost baselines on R2 | medium | — | — | yes | disputed | 17 | exploratory | **high (inspected)** | no | **P2 / rejected** | It would add models fitted after inspection without changing estimability |
| 24 | Asymmetric error-cost analysis (19.6) | — | — | — | **no cost basis** | — | — | — | — | — | **P2** | Only a symbolic framework, inside A15 |

## Stop rules

1. Any reproduced R2 count that differs from the frozen output stops the analysis. The H1 script asserts this.
2. Any invariant violation is investigated before it is reported.
3. No result on blocked items is presented as a number.
