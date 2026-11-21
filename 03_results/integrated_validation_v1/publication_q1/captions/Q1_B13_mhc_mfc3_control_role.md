# Q1_B13 — MFC-3 control role

**Scientific question.** Why must MFC-3 be interpreted as a controlled output?

**Caption.** Stage II pressure P-2 conditioned on whether the outlet controller MFC-3 records flow, per held-out run. While MFC-3 is zero, P-2 never exceeds the nominal outlet set pressure by more than 1.0 bar (maxima 181, 140.6, 180.8 vs set points 180, 140, 180 barg). This is consistent with MFC-3 acting as a back-pressure release: MFC-3 is a controlled output, not an independent disturbance. The set-point signal itself is not recorded.

**Interpretation limit.** One MHC apparatus, three held-out runs (serially dependent rows); the recording increment is the observed data grid, not instrument accuracy; reference prediction only — no event labels, no diagnosis.

**Source data.**
- `study_b/evidence_enhancement/results/analysis/controller_role.csv`

**Code.** `scripts/fig_mhc.py::plot_mhc_control_role` · Files: `figures/Q1_B13_mhc_mfc3_control_role.png`, `figures/Q1_B13_mhc_mfc3_control_role.svg`
