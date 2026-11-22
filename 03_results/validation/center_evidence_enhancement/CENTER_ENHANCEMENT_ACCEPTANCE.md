# Center evidence enhancement — Acceptance

**Decision: ACCEPTED WITH LIMITATIONS.**

Every gate below passed for the analyses that were eligible. The scientific scope stays one air-like simulation family under hypothetical bounds. One planned analysis, Experiment F, is blocked by an unrecorded governance decision and was not run.

| Gate | Result | Evidence |
|---|---|---|
| A — Source integrity | PASS | All 12 raw capture hashes verified by the loader; `baseline_freeze --verify` passed: 12 captures, 410 frozen files, before and after |
| B — Frozen preservation | PASS | No tracked file differs from `h2prism-center-baseline-v1`; `test_frozen_center_artifacts_unchanged`; canonical checkout status unchanged |
| C — Experimental correctness | PASS | Primary-capture exclusion rule tested; frozen TAB_10 margins reproduced for 8/8 queries before new analysis (`analysis/gate_frozen_reproduction.csv`); near-duplicates flagged and disclosed |
| D — Physics and units | PASS | Units checked by the loader and the engine whitelist; bounds per kind in MPa and kg/s; R = 0.287 kJ/(kg·K) read from the source SLX; anchors declared retrospective |
| E — Formal D(Y) | PASS | Frozen `diagnose` used unchanged; adapter results pass engine validation; 3,584/3,584 engine statuses equal the closed form; split invariance holds |
| F — Reporting traceability | PASS | Every Results number maps to `analysis/` or a named frozen file |
| G — Visualization | PASS | 11 standalone figures, 3840 × 2160 PNG + parseable SVG + caption; rendered images inspected for clipping and overlap; no PDF |
| H — Reproducibility | PASS | Script-driven; configurable workspace; two runs byte-identical; 12 focused tests pass; Center regression suite 106 passed, 2 skipped (workspace-dependent) |
| I — Claim integrity | PASS | No field validation, fault accuracy, certified exclusion or independent localization claimed (TAB_C08) |

**Blocked.** Experiment F, the corrected v0.3 classification replication, needs owner decision D1 and a written authorization (`EXPERIMENT_F_PROPOSAL.md`).

**Why not ACCEPTED outright.**
- The positive results (location ranking, conditional SPECIFIC window) rest on one outlet with a near-duplicate replicate, inside one source family, under hypothetical bounds.
- Mechanism recognition did not survive self-template removal.
