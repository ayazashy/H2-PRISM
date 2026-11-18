# Q1_C12b — Operational rivals stay excluded except Normal at wide bounds

**Scientific question.** Are operational (non-withdrawal) hypotheses excluded for the withdrawal queries?

**Caption.** Status of the normal, pressure-command and timing hypotheses for the withdrawal queries. Rows are query/hypothesis pairs (IDs in TS02_center_dy_id_map.csv); columns are declared total bound scenarios (ε_total = ε_obs + ε_model per kind; S1: 1e-06 MPa, 1e-05 kg/s; S2: 1e-05 MPa, 0.0001 kg/s; S3: 0.0001 MPa, 0.001 kg/s; S4: 0.001 MPa, 0.01 kg/s; S5: 0.01 MPa, 0.1 kg/s; S6: 0.1 MPa, 1 kg/s; REF: 0.0344 MPa, 0.0182 kg/s). Full declared universe, all sensors, ±1 s clock. Cell counts: excluded 78, consistent 6. The complete matrix for every universe, sensor group and clock bound is in TS01_center_dy_status_matrix.csv. Conditional hypothetical bounds — not calibrated uncertainty.

**Interpretation limit.** Conditional hypothetical bounds — not calibrated uncertainty. One controlled simulation source family with an air-like gas model; no field or hydrogen-material claim.

**Source data.**
- `03_results/validation/center_evidence_enhancement/analysis/dy_decisions.json`
- `publication_q1/tables/TS01_center_dy_status_matrix.csv`

**Code.** `scripts/fig_center.py::plot_center_dy_operational_rivals` · Files: `figures/Q1_C12b_center_dy_status_operational_rivals.png`, `figures/Q1_C12b_center_dy_status_operational_rivals.svg`
