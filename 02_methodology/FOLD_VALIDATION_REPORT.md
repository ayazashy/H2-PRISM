# Fold Validation Report (F4)

- **Validated:** 2026-11-11 with the runner preflight on real data (read-only).
- **Folds:** `pre_experiment_review/CANDIDATE_OUTER_FOLDS.csv` (`3b21d823…`), inner `CANDIDATE_INNER_FOLDS.csv` (`ebff65da…`).

| Check | Result |
| --- | --- |
| Pinned hashes (outer, inner) | PASS |
| Each fold's train ∪ test = the 51 eligible runs exactly | PASS (3/3) |
| Family isolation (`splits.validate_outer_folds`, required training classes present) | PASS, 0 issues |
| Topology isolation (one test topology per fold; disjoint from training) | PASS |
| Run isolation inside the runner (`assert_group_disjoint` on Scenario_ID, family and topology for every fold) | PASS (enforced at run time) |
| Pinned inner `LOTO_within_train` splits equal the runner's derived topology splits | PASS (preflight `inner_folds_match_runner`) |
| Class presence per fold | train: NORMAL 2, LEAK 26, FAULT 4, DELAY 2 runs; test: NORMAL 1, LEAK 13, FAULT 2, DELAY 1 |
| Content duplicates across splits | 0 duplicate raw hashes; 0 duplicate feature vectors |
| Extended family map (sensitivity) | nests in topology (max 1 topology per family), so it is valid under the same folds |

**Historical folds:** `01_dataset_audit/folds.csv` failed family isolation (every family on both sides; ISS-01) and must not be used. See `01_dataset_audit/DATASET_AUDIT_AMENDMENT_2026-11.md`.

**Tests:** `tests/test_primary_protocol.py` (duplicate family, topology leakage, inconsistent fold ids, missing training class); `tests/test_splits.py`.
