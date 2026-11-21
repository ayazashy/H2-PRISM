# Scientific Decision Resolution: Master Report (Phase 6)

**Principle.** Recommendations and technical statuses are not human approvals. 43 of 44 decisions remain `PENDING_HUMAN_SIGNOFF`. G-D01 (the commit plan) is `APPROVED_BY_HUMAN` on the user's explicit instruction.

## Resolution summary (`UPDATED_DECISION_MATRIX.csv`)

| Technical status | n | Decisions |
| --- | ---: | --- |
| VERIFIED | 5 | Y-D02, Y-D05c, Y-D10, A-D07, A-D11 |
| IMPLEMENTED | 2 | Y-D07 (manifest v0.2), Y-D09 |
| TESTED | 6 | F-D08 (thin-class flag), F-D09 (calibration fallback), F-D10 (combined score), F-D13 (bootstrap), F-D15, F-D18 |
| PROVISIONALLY_SELECTED | 16 | Y-D01, Y-D04, Y-D05d, Y-D06b, F-D01–F-D07, F-D11, F-D12, F-D14, F-D17, A-D04 |
| RECOMMENDED_FOR_APPROVAL | 10 | Y-D08, F-D16, A-D01–A-D03, A-D05, A-D06, A-D08–A-D10 |
| BLOCKED_BY_EVIDENCE (restriction implemented) | 4 | Y-D03, Y-D05a, Y-D05b, Y-D06a |
| APPROVED_BY_HUMAN | 1 | G-D01 |

Owner reports: `YAZAN_RESOLUTION.md`, `FAISAL_RESOLUTION.md`, `AHMED_RESOLUTION.md`. Candidate artifacts: `CANDIDATE_MANIFEST_V02.csv`, `CANDIDATE_EVALUATION_CONFIG.yaml`, `CANDIDATE_EXPERIMENTAL_PROTOCOL.md`.

## Cross-owner consistency review

| Dimension | Yazan package | Faisal package | Ahmed package | Consistent? |
| --- | --- | --- | --- | --- |
| Scenario identity | 57 runs, misfiled copies merged | folds and feature builder read v0.2 | dataset text uses 57 / 51 | ✔ (tested) |
| Classes | 4 classes; 6 runs excluded; multi-location = LEAK | config classes = v0.2 classes | class definitions A-D05 | ✔ (tested) |
| Label timing | row-level; post-delay and pre-event rows excluded | `pre_event_policy=exclude` | NORMAL support stated as 3 runs | ✔ |
| Families | primary map; extended for sensitivity | bootstrap unit = primary, extended as sensitivity | conditional intervals | ✔ |
| Folds | families nest in topology | LOTO outer and inner | estimand = held-out topology | ✔ (tested) |
| D reference | — | outer-train only; query-family exclusion; thin-class flag | flag documented in the methodology | ✔ |
| Calibration | — | none / sigmoid with feasibility fallback | not assumed beneficial | ✔ |
| **Thresholds vs policy** | — | the thin-class flag blocks SPECIFIC; in development the thin classes have 1 family, so thresholds are LEAK-driven | RQ2 criteria per class | **⚠ known tension**, documented. Options: (a) keep blocking (conservative, current); (b) record without blocking. Owners: Faisal + Ahmed (F-D11). Not silently resolved |
| Statistics | windows not units | family bootstrap, pooled only | thin classes descriptive | ✔ |
| Claims | location analysis blocked for G5G6 | localisation not a target | localisation prohibited | ✔ |

No upstream data definition was changed to resolve a conflict.
