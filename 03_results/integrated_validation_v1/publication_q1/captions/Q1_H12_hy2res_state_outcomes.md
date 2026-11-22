# Q1_H12 — Operating-state decision outcomes

**Scientific question.** Does the evidence rule recognise the minority operating state?

**Caption.** Frozen state-rule outcomes per power-defined operating state (44,397 test rows). The compressor-powered minority state (817 rows) receives 0 SPECIFIC calls: 201 ambiguous and 616 unresolved. All 10,762 SPECIFIC calls agree with a constant 'electrolyzer only' baseline. Operating-state labels are not fault labels; this is not compressor-fault detection.

**Interpretation limit.** One residential hydrogen system (HY2RES, April 2024); operating-state labels are power-defined, not fault labels; reference prediction and evidence validity only — no diagnosis, localisation or transfer claim.

**Source data.**
- `evidence_enhancement/results/analysis/state_outcomes.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_state_outcomes` · Files: `figures/Q1_H12_hy2res_state_outcomes.png`, `figures/Q1_H12_hy2res_state_outcomes.svg`
