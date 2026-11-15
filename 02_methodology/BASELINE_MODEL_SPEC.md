# Baseline Classifier Specification (Faisal F5)

The frozen baseline is a 300-tree `RandomForestClassifier` with
`max_features="sqrt"`, `min_samples_leaf=2`,
`class_weight="balanced_subsample"`, and seed 2026 plus the outer-fold ID.
Hyperparameters are fixed in the versioned configuration rather than tuned
against the outer test set. Fit only on eligible windows from the outer
training topologies. Per-window sample weights make the total contribution of
each `Scenario_Family_ID` equal before class balancing.

Raw class probabilities and predictions are retained. The final outer-fold
prediction table additionally stores the development-selected calibrated
probabilities, but baseline classification metrics are separately identified
as raw or calibrated. All metrics are calculated at the window level and
reported with family-level summaries because windows within simulations are
not independent.

Executable implementation: `src/h2prism/evaluation.py` and
`src/h2prism/experiments.py`. Outputs:
`03_results/BASELINE_RESULTS.csv`,
`03_results/OUTER_PREDICTIONS.csv`, and
`03_results/figures/fig3_confusion_matrix_stage2.png`.
