# Candidate Experimental Protocol (PROVISIONALLY_SELECTED; PENDING_HUMAN_SIGNOFF; not executed)

Configuration: `CANDIDATE_EVALUATION_CONFIG.yaml`. Every step below uses existing, tested code.

1. **Data.** Manifest v0.2, 51 eligible runs, one realization per run (noise-added primary; clean as a separate secondary run).
2. **Windows and features.**
   - Build the table with `h2prism.feature_table.build_feature_table`: 60 s / 30 s windows, row-level labels, boundary and pre/post-event windows excluded.
   - 128 features; scaling fitted inside training folds.
3. **Outer loop.** For each held-out topology (3 folds):
   1. **Development (outer-train only; inner LOTO splits):**
      - Random Forest grid selection by macro-F1 on inner out-of-fold predictions (`baseline.run_grouped_evaluation`).
      - Calibration: `calibration_feasibility`, then `select_calibration` over {none, sigmoid}.
      - D(x) on development windows, with the reference built from the other inner topology.
      - Comparators C, M, −H.
      - Cross-fitted s_C and s_{C−D} (`combined_score.fit_combined_score`).
      - Policy thresholds by rank matching at coverage 0.80 / 0.60 / 0.90 (`metrics.rank_match_selection` on development scores only).
   2. **Outer test (used once):**
      - refit the selected model on all outer-train data and predict;
      - apply the fitted calibrator;
      - compute D with the outer-train reference;
      - score with the fitted meta-models;
      - apply the frozen thresholds and the policy.
4. **Primary comparison.** s_C vs s_{C−D} (both threshold-transferred and rank-matched), on the same windows.
   - **Secondary comparisons:** confidence, margin and entropy alone; D alone; and the A16 ablation arms.
5. **Reporting** (per fold and pooled):
   - coverage together with selective risk;
   - ambiguity inclusion and set size;
   - unresolved rate and reasons;
   - per-family tables;
   - per-class tables, descriptive only;
   - realized vs target coverage.
6. **Uncertainty.** `uncertainty.paired_stratified_bootstrap` over primary families within topology, 2000 resamples, seed 20261104, pooled only. Re-run with the extended family map as a sensitivity check.
7. **Sensitivity analyses (registered now).** Clean realization; 60 / 60 windows; `label_normal`; offset-invariant features; k = 10 / 50; prior correction; extended family map.
8. **Interpretation.** `AHMED_RESOLUTION.md` C6. Effect sizes only (A-D04).
9. **Provenance.** Git commit, config / manifest / folds hashes, seed and run status recorded for every output (`build_provenance_index.py`).

**Prohibited throughout:** using outer-test labels for any choice; pooling realizations; treating windows as independent units; changing this protocol after outer-test results.
