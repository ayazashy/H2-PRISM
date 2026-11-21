# Q1_B12 — Errors in recording increments

**Scientific question.** Are the model differences resolvable on the recording grid?

**Caption.** Errors divided by each channel's observed recording increment (smallest step between distinct recorded values: P-2 0.2 barg, MFC-3 0.01 ln/min; all values on grid). Run-mean ΔMAE is 0.073 increments for P-2 and 1.08 for MFC-3. Persistence exact-match share: 0.706 and 0.907. The increment is recorded quantization, not instrument resolution or accuracy (neither is documented in the source).

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/resolution.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_resolution` · Files: `figures/Q1_B12_mhc_recording_resolution.png`, `figures/Q1_B12_mhc_recording_resolution.svg`
