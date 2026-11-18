# Q1_B04 — MFC-3 prediction traces

**Scientific question.** How do the reference predictions follow measured MFC-3?

**Caption.** MFC-3 outlet hydrogen flow in the three held-out runs over the representative cycles declared in the analysis manifest (4,200 displayed observations), with the frozen persistence and Ridge one-step predictions. Persistence repeats the previous recorded value; Ridge is the frozen two-input linear reference. Times are workbook clock times.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/replay/replayed_predictions.csv.gz`
- `analysis/analysis_manifest.json (representative_windows)`

**Code.** `scripts/fig_mhc.py::plot_mhc_mfc3_traces` · Files: `figures/Q1_B04_mhc_mfc3_prediction_traces.png`, `figures/Q1_B04_mhc_mfc3_prediction_traces.svg`
