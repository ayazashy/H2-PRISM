# AV-F14 — Gas-composition qualification matrix

**Scientific question.** Which gas compositions can H₂-PRISM currently handle, and at which level?

**Caption.** Qualification of gas compositions (A13). Pure-H2 property tables reproduce the Leachman equation of state (CoolProp 7.2.0) within 250–400 K × 0.1–10 MPa, and the composition interface refuses every blend. No gas-specific transient network model has been built (H2Net v1 blocked), so no simulation (Level B) or experimental (Level C) diagnostic transfer result exists. The legacy Center model is air-like with an unphysical heat-capacity ratio.

**Interpretation limit.** Status summary; no new physical result.

**Source data.**
- `advanced_validation/tables/A13.csv`

**Code.** `scripts/fig_av.py::plot_av_gas_matrix` · Files: `figures/AV-F14_gas_qualification_matrix.png`, `figures/AV-F14_gas_qualification_matrix.svg`
