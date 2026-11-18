# Q1_C04 — Archive benchmark recall

**Scientific question.** Does archive machine-learning recall exceed a trivial rule?

**Caption.** Oracle-onset event-window benchmark on the historical archive. All 39 scored held-out scenarios carry LEAK annotations, so a constant 'LEAK' rule recalls 39/39. XGBoost reaches 39/39 in every sensor variant (ties the constant rule); the best random forest recall is 0.949. Multiclass accuracy is not reported because only one class is present.

**Interpretation limit.** Single-class held-out set: recall cannot show discrimination.

**Source data.**
- `03_results/validation/publication_final_v1/tables/TAB_03.csv`

**Code.** `scripts/fig_center.py::plot_center_archive_recall` · Files: `figures/Q1_C04_center_archive_recall.png`, `figures/Q1_C04_center_archive_recall.svg`
