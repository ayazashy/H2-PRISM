# Human Sign-off Requirements (Phase 6)

Sign on the existing sheets: `phase5_decisions/YAZAN_SIGNOFF.md`, `FAISAL_SIGNOFF.md`, `AHMED_SIGNOFF.md`. Each approval must record:
- decision ID;
- the exact option;
- approver;
- date;
- artifact hash or version: manifest v0.2 `36bcbaf9…`, config `CANDIDATE_EVALUATION_CONFIG.yaml` (record its SHA-256 at signing);
- conditions;
- evidence reference (message, minutes or review).

| Owner | Decisions | P0 among them | Special attention |
| --- | --- | --- | --- |
| Yazan (15) | 14 Y-IDs (Y-D01–Y-D10 incl. a–d; Y-D05d and Y-D06a are joint) + joint F-D05 | Y-D01, Y-D05b, Y-D05d, Y-D06a, Y-D07, Y-D08 | Y-D03: accept the interim mapping or provide `.slx` evidence; Y-D05a/b and Y-D06a cannot be resolved from the data; restrictions are implemented |
| Faisal (20) | F-D01–F-D18 + joint A-D04, Y-D06a | F-D01–F-D08, F-D10–F-D12, F-D15, F-D17 | Code review of 3 new modules and 2 modified modules; the threshold-vs-thin-class-flag tension (F-D11) |
| Ahmed (18) | A-D01–A-D11 + joint Y-D05d, Y-D06a, F-D05, F-D07, F-D11, F-D13, F-D17 | A-D04, A-D05, A-D10 | Inference protocol C6 and RQ2 criteria C2 fixed **before** any run; documentation edits (C5) |
| User | G-D01 | — | Already approved (commits executed) |

**Approval order:** Yazan (Y-D01, then Y-D05 and Y-D06a, then Y-D07, then Y-D08) → Faisal (F-D01–F-D12, then F-D17) → Ahmed (A-D04, A-D05, then A-D10) → user authorisation.

Ahmed's A-D01–A-D03 and Faisal's F-D15 / F-D18 code review can proceed in parallel now.
