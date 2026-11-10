# Final Pre-Experiment Acceptance (authoritative)

## Verdict: `PRE_EXPERIMENT_ACCEPTANCE_BLOCKED`

**Every engineering acceptance criterion is met.** The only blockers are named-human attestations, which this review may not supply. No explicit waiver exists. No primary experiment has been run, and no claim about the hypothesis is made.

### Actual blockers (only these)

1. **F-D15:** Faisal's acceptance of the reviewed code. The independent review and its fixes are complete.
2. **F-D16:** Faisal's acceptance of interface contract v2.0.0. The contract is implemented and tested.
3. **A-D10:** named attestation of Gates 1–3 (Ahmed re-records; Yazan is the gate owner). Engineering re-verification is done: Gate 1 PASS, Gates 2–3 CONDITIONAL.
4. **PA-1:** owner acceptance of the matched-coverage tie amendment. It was pre-registered before any outer-test evaluation.

Each is cleared by the named attestation or by the project lead's written waiver. The runner enforces this through `governance_clearance` in the authorization file.

## Acceptance standard (§13)

| Criterion | Met | Evidence |
| --- | --- | --- |
| Every required preparatory task complete or justified non-blocking | ✔ (with justification) | `TEAM_PLAN_COMPLETION_MATRIX.csv`: the only `execution_blocking=YES` rows are the 4 attestations above. Documentation gaps (A1–A6, A10, F3/F7/F9/F11 named specs) and post-execution deliverables are non-blocking |
| All executable components integrated | ✔ | one runner; `FINAL_EXPERIMENT_CONTRACT.md` §3 |
| All material bugs fixed | ✔ | D1–D8 (`FINAL_CODE_AND_METHOD_AUDIT.md`) |
| Matched-coverage comparisons coherent | ✔ | PA-1; identical counts asserted per fold; 17 tie tests |
| No unresolved leakage defect | ✔ | 16-boundary audit; two validity risks reported (run fingerprint, DELAY/start-up) |
| D(x) safeguards enforced | ✔ | flags block SPECIFIC; synthetic run shows the flags firing |
| Real-data preflight succeeds | ✔ | 26/26 for noise_added and clean; 0 non-finite values |
| End-to-end synthetic tests succeed | ✔ | `FINAL_VALIDATION_EVIDENCE.md` |
| Reproducibility checks pass | ✔ | byte-identical resume and reordered inputs; feature-table hash reproduced |
| Protocol and implementation agree | ✔ | D1–D3 fixed; contract tests. Gap: 7 of 9 secondary sensitivity analyses lack a runner path; not part of the primary run |
| Governance evidence recorded | ✔ | `FINAL_GOVERNANCE_AND_GATE_RECORD.md` |
| No execution-blocking attestation without waiver | **✘** | blockers 1–4 |
| Final configuration hash-pinned | ✔ | `f788b6d8…` (LF-normalised through `.gitattributes`) |
| No unexpected critical validation failures | ✔ | full suite: 231 passed, 0 failed, 2 expected skips |

## Team-plan completion

Unit: one row per plan task or deliverable group in the matrix. Rate = (VERIFIED_COMPLETE + COMPLETE_WITH_DOCUMENTED_LIMITATIONS) / (rows − NOT_APPLICABLE).

| Owner | Rows | Verified | With limitations | Partial | Not implemented | Blocked by evidence | Human attestation | N/A | Rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Yazan | 10 | 1 | 4 | 1 | 1 | 0 | 2 | 1 | 5/9 (56%) |
| Faisal | 17 | 3 | 7 | 3 | 0 | 0 | 2 | 2 | 10/15 (67%) |
| Ahmed | 16 | 0 | 6 | 4 | 3 | 0 | 1 | 2 | 6/14 (43%) |

Evidence-limited items are recorded as limitations on Y2 and Y4 (ancestry, location labels, annotation anomalies). They are permanent source-data restrictions, not open work.

## Milestones (kept distinct)

| Milestone | Status |
| --- | --- |
| Coding completed | yes (runner and all modules) |
| Integration completed | yes |
| Tests passed | yes |
| Data integrity verified | yes (264/264 archive checksums; 51/51 eligible-file hashes per realization) |
| Scientific methodology reviewed | yes (independent review; owner sign-offs pending) |
| Research results produced | **no** |

## Explicit scientific limitations added in Phase 9 (no protocol change)

These were found by a read-only structural scan, before any model fitting. Neither changes the primary features or labels.

1. **Run fingerprint:** absolute-level features nearly identify the run within its topology. Interpretation is restricted until the registered offset-invariant sensitivity analysis is run.
2. **COMPRESSOR_DELAY confounding:** DELAY is confounded with the start-up phase. It stays descriptive-only, with no event-specific DELAY claim.

Both are recorded in `phase6_resolution/SCIENTIFIC_LIMITATIONS_AND_CLAIMS.md` (items 10–11).
