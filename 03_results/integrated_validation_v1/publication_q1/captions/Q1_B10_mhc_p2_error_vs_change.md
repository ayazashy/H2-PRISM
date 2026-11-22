# Q1_B10 — P-2 error versus observed change

**Scientific question.** Where does Ridge gain or lose against persistence on P-2?

**Caption.** Ridge − persistence differences for P-2 Stage II hydrogen pressure by observed one-step change |Δy| in recording increments (bins fixed before scoring; pooled held-out runs). Positive (burgundy) favours persistence, negative (teal) favours Ridge. Total ΔSSE -28.95 barg²: Ridge's small RMSE gain comes from rows with recorded changes, while its MAE loss accumulates on unchanged rows. Retrospective: |Δy| uses the outcome.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/error_vs_change.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_p2_vs_change` · Files: `figures/Q1_B10_mhc_p2_error_vs_change.png`, `figures/Q1_B10_mhc_p2_error_vs_change.svg`
