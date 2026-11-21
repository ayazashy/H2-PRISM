# Yazan: Dataset Approval Dossier (decisions Y-D01 … Y-D10)

**Status:** CANDIDATE_NOT_APPROVED. Every decision below is `PENDING_HUMAN_APPROVAL` in `MASTER_DECISION_MATRIX.csv`. Your originals in `01_dataset_audit/` and `audit/` are unchanged.

## Y-D01: Canonical identity (reconciliation, `evidence/INVENTORY_RECONCILIATION.csv`)

| Step | Count | Rule |
| --- | ---: | --- |
| Archive members (official Zenodo V2) | 264 files | 242 tabular + models/scripts/docs |
| Tabular files | 242 | CSV + Parquet |
| → CLEAN_SIMULATION files | 114 | 57 runs × {CSV, Parquet} in `H2-SimNet-clean/` |
| → NOISE_ADDED_RELEASE files | 114 | 57 runs × {CSV, Parquet} in `anomalous-/normality-scenarios/` |
| → NOISE_ADDED_VARIANT (`_noisy`) | 6 | 3 runs (leakG5G6_overlapped, one per topology) × 2 formats |
| → RAW_SOLVER_EXPORT (MATLAB CSV) | 6 | 3 normality runs × 2 copies |
| → MISFILED_COPY | 2 | byte copies of the noisy Upstream transient leakG4 |
| **Distinct simulated runs** | **57** | candidate Scenario_IDs (your map had 58: the misfiled copy was a separate "Unknown" scenario) |
| Excluded runs | 6 | 3 `leakG4brokenC1` (compound), 3 `brokenC1G5_weak` (annotation conflict) |
| **Eligible runs** | **51** | NORMAL 3, LEAK 39, COMPRESSOR_FAULT 6, COMPRESSOR_DELAY 3 |
| Families over eligible runs | 39 / 32 / 3 | primary / extended / conservative (45 / 35 / 3 over all 57) |

Each run's evidence is in `pre_experiment_review/CANDIDATE_FILE_INVENTORY.csv` (path, SHA-256, realization, resolution evidence).
*Recommendation: accept.*

## Y-D02: Realizations are one run

- Labels are identical in 60/60 clean-vs-noise comparisons.
- The residual is zero-mean and white.
- Solver exports match the clean runs within a median 0.08–0.6% of range.

Raw files are untouched, and file identities and hashes are preserved.
*Recommendation: confirm.*

## Y-D03: The 19 unresolved relationships (`evidence/RELATIONSHIP_19_REVIEW.csv`, one row per edge)

| Group | Edges | Pattern | Assessment | Recommendation |
| --- | ---: | --- | --- | --- |
| A. Start-up identical until t = 25 s | 11 | brokenC1 weak/strong ↔ startdelayC1 (Downstream, Upstream: 25/25 rows; Center: 24/25 rows), and leakG4 runs ↔ leakG4brokenC1 (25/25) | **PLAUSIBLE.** Every run starts from the network start-up; a 25-row match is shared initial state, not proof of a common run (plan Y2 step 23). 6 of the 11 involve the excluded compound run | Keep separate in the primary map; merge in the extended/sensitivity map |
| B. Near-identical pre-event trajectory | 8 | transient leakG4 (onset 400 s) ↔ constant-segment leakG4 weak/strong (387–397 of 400 rows identical); start-transient leakG3 ↔ constant-segment leakG3 (98–100 of 100) | **PLAUSIBLE_DEPENDENT.** Same valve and topology; the trajectories diverge only just before the onset | Treat as dependent for inner splits; decide whether to merge in the primary map |

- 13 of the 19 pairs are cross-class (FAULT↔DELAY, LEAK↔compound).
- **None crosses a topology, so none affects the leave-one-topology-out outer folds.** They matter only for family-grouped inner splits and for any family bootstrap.
- To resolve them definitively, check whether the `.slx` models used one configuration with different injection parameters. That needs MATLAB, which is not available here.

## Y-D04: Family definition

| View | Families (all / eligible) | Basis | Effective units | Use |
| --- | --- | --- | --- | --- |
| Primary | 45 / 39 | weak/strong pairs only (12 edges) | 39 | recommended dataset definition |
| Extended | 35 / 32 | + the 19 short-segment edges | 32 | registered sensitivity |
| Conservative | 3 / 3 | topology | 3 | upper-bound check only (no family-level uncertainty possible) |

- Transitivity checked: no family spans topologies in any view.
- Class representation per fold is unchanged across views: 1 / 2 / 13 / 1 runs per test fold.

## Y-D05: Labels (`pre_experiment_review/LABEL_AND_TIMING_CORRECTIONS.md`)

| Item | Raw source labels | Verified interpretation | Proposed target | Exclusion rule |
| --- | --- | --- | --- | --- |
| leakG5G6_overlapped (Y-D05a) | Leak, leak_G4, leak_G6 from 400 s | Filename and labels disagree on location | LEAK | none (localisation not a target) |
| brokenC1G5_weak (Y-D05b) | CompressorFault from 25 s; leak_G5 without Leak | Internally inconsistent annotation | none | EXCLUDED_PENDING_REVIEW |
| leakG4brokenC1 (Y-D05c) | Leak (100 s) and CompressorFault (25 s) | Coherent compound | none | EXCLUDED_COMPOUND (exploratory multi-label) |
| Multi-location leaks (Y-D05d) | Leak + ≥ 2 location columns (15 runs) | Single event type | LEAK (alternative: exclude all 15) | joint with Ahmed |

No raw label is repaired and no classes are merged for feasibility.

## Y-D06: Timing and phase

| Fact | Status |
| --- | --- |
| Onsets per run (`evidence/EVENT_DURATIONS.csv`) | VERIFIED from the Parquet `Timestamp` index |
| CompressorDelay active 25–1000 s (976 s) | VERIFIED. Policy for later rows: Y-D06a (joint) |
| C1 fault onset 25 s in `constant_segment/` | VERIFIED. Folder ≠ phase (Y-D06b) |
| Phase per window | NOT VERIFIABLE (the ReadME gives no phase boundaries). Use onset time and the ReadME phase per event type only as descriptive metadata |
| Boundary-crossing windows | Excluded; 93 at 60/30 over 51 runs (`evidence/WINDOW_OPTION_COMPARISON.csv`) |

## Y-D07: Manifest v0.2

The candidate is `pre_experiment_review/CANDIDATE_SCENARIO_MANIFEST.csv` (SHA-256 `29b8b3cc…`). The field mapping to your Y8 schema is in `CANDIDATE_DATASET_FREEZE_SPEC.md`. It is deterministic and validated (A12 33/33; reverse-order rebuild 13/13 identical). Issue it as v0.2 only after Y-D01…Y-D06.

## Y-D08: Readiness (candidate answer for you to accept or amend)

| Question | Candidate answer |
| --- | --- |
| Usable for the 4-class task? | Yes, for a **pooled** evaluation on 51 runs with 6 runs excluded |
| Classes defensible? | LEAK yes. NORMAL, FAULT and DELAY are defined correctly but rest on 3 runs (FAULT: 3 weak/strong families) |
| Grouped evaluation feasible? | Yes: LOTO, 0 leakage issues under 3 family views |
| Ambiguous labels | L1 (location only), L2 (excluded), post-delay rows |
| Descriptive only | per-class results for NORMAL, FAULT, DELAY |
| Unsupported | localisation, cross-network or field generalisation, pure H₂ / blend-fraction claims |
| Restrictions | one realization per analysis; no phase or time-in-run feature; windows never the inference unit |

Candidate decision: **READY_WITH_EXCLUSIONS (restricted)**. Ahmed must approve the interpretation.

## Y-D09 / Y-D10: Housekeeping

- Adopt `src/h2prism/dataset_manifest.py` as the reference builder.
- Regenerate `raw_checksums.sha256` from the untouched archive: 264 files, CRLF preserved, no `.gitkeep`.
