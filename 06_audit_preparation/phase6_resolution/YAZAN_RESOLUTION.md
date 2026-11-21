# Yazan: Dataset Decision Resolution (Phase 6)

Every item is **PENDING_HUMAN_SIGNOFF**. Technical statuses are in `UPDATED_DECISION_MATRIX.csv`. Candidate artifact: `CANDIDATE_MANIFEST_V02.csv` (sha256 `36bcbaf97bb17659995f393884d1dcde3bbca9236c3dcdcc6e7651e61538fb59`, status `PROVISIONALLY_SELECTED_PENDING_YAZAN_SIGNOFF`).

## A1. Canonical accounting (one table, defined populations)

| Level | Count | Definition / rule | Evidence |
| --- | ---: | --- | --- |
| Archive files | 264 | official Zenodo V2 members (MD5 verified) | `raw_verification/CHECKSUM_RECONCILIATION.csv` |
| Tabular files | 242 | CSV + Parquet | `pre_experiment_review/CANDIDATE_FILE_INVENTORY.csv` |
| Realizations | 4 types | clean 114 files · noise-added 114 · `_noisy` variant 6 · solver export 6 · plus 2 misfiled copies (byte-identical to a noise-added file) | same |
| **Simulated runs** | **57** | one Scenario_ID per run; misfiled copies resolved by SHA-256 only | `phase4_approvals/evidence/INVENTORY_RECONCILIATION.csv` |
| Excluded runs | 6 | 3 `leakG4brokenC1` (two event types at once); 3 `brokenC1G5_weak` (location flag active while Leak = 0) | v0.2 `exclusion_reason` |
| **Eligible runs** | **51** | NORMAL 3 · LEAK 39 · COMPRESSOR_FAULT 6 · COMPRESSOR_DELAY 3 | v0.2 |
| Families over eligible runs | 39 / 32 / 3 | primary / extended / conservative | v0.2 family columns |
| Windows | not samples | repeated observations inside runs; never the independence unit | — |

Exactly one realization per run enters any analysis. `feature_table.py` enforces this and it is tested.

## A2. The 19 relationships (`phase4_approvals/evidence/RELATIONSHIP_19_REVIEW.csv`, one row per edge)

| Group | n | Evidence | Assessment | Candidate mapping |
| --- | ---: | --- | --- | --- |
| Shared start-up only | 11 | the first 24–25 rows identical up to the 25 s onset (C1 fault ↔ delay; leakG4 runs ↔ compound) | Start-up state is shared by construction; not evidence of a common run | **separate** in the primary map; **merged** in the extended map |
| Near-identical pre-event | 8 | 387–400 of 400 rows (transient leakG4 ↔ constant leakG4 weak/strong) and 98–100 of 100 (leakG3 start ↔ constant) | Possible common configuration. **BLOCKED_BY_EVIDENCE**: ancestry needs the `.slx` models | **merged in the extended map** (conservative sensitivity); separate in the primary map |

- Never asserted: independence of any pair.
- Consequence: all 19 pairs sit within one topology, so **no outer or inner split changes**. The choice affects only the bootstrap unit (F-D13), which is why both maps stay registered.

## A3. Labels (raw labels untouched)

| Issue | Row-level evidence | Candidate rule | Status |
| --- | --- | --- | --- |
| `leakG5G6_overlapped` (filename) vs leak_G4 + leak_G6 (labels) | labels identical across realizations | LEAK (class unaffected); `location_analysis_allowed = False` | BLOCKED_BY_EVIDENCE (true location) |
| `brokenC1G5_weak` | CompressorFault plus leak_G5 with Leak = 0 | exclude from the exclusive task; raw labels kept | BLOCKED_BY_EVIDENCE |
| Compound `leakG4brokenC1` | Leak and CompressorFault simultaneously | exclude; exploratory multi-label only | VERIFIED |
| Multi-location single-type leaks (15 runs) | Leak only, ≥ 2 locations | LEAK | PROVISIONALLY_SELECTED (joint with Ahmed, A-D05) |

## A4. Timing and window eligibility

| Data segment | Supports | Candidate rule |
| --- | --- | --- |
| Rows with exactly one active event type | event windows | eligible |
| Normal runs (3) | NORMAL windows | eligible (whole run) |
| Pre-onset rows of fault runs | "normal-like" but **time-confounded** (only early run time) | excluded in the primary analysis; `label_normal` registered as secondary (it raises NORMAL runs from 3 to 45; `WINDOW_OPTION_COMPARISON.csv`) |
| CompressorDelay rows after 1000 s | labels 0; cause unknown | excluded (POST_EVENT), never relabelled |
| Windows crossing a label change | ambiguous | excluded (BOUNDARY_CROSSING; 93 at 60/30) |
| Phase | folder names are not phase | not used |

## A5 / A6. Manifest v0.2 and readiness

- Manifest v0.2 is built by `python tools/dataset/build_manifest_v02.py`. It is deterministic and includes per-realization SHA-256 values.
- Supported by the candidate dataset: restricted grouped evaluation (LOTO), a primary pooled comparison, per-class **descriptive** analysis, and registered sensitivity analyses (family maps, realization, pre-event policy, windows, features).
- Not supported: per-class inference for NORMAL, FAULT and DELAY; localisation.
- **Recommendation:** READY_WITH_EXCLUSIONS (restricted) — **RECOMMENDED_FOR_APPROVAL**, not approved.

## Yazan must sign (sheet: `phase5_decisions/YAZAN_SIGNOFF.md`)

Y-D01, Y-D03 (accept the interim mapping or supply `.slx` evidence), Y-D04, Y-D05a/b/d, Y-D06a/b, Y-D07 (v0.2 hash above), Y-D08, Y-D09, Y-D10 (regenerate `raw_checksums.sha256`). Y-D02 and Y-D05c are verified facts and need only acknowledgement.
