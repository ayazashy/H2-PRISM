# Q1_C03 — Command timing shift

**Scientific question.** How does a one-second command-issuance shift appear?

**Caption.** Command-issuance timing pair. The PS7 command channel steps by 3.40 MPa at 25.0 s in the control and at 26.0 s in the intervention; PS1 follows each command. Exact recorded samples, 15–40 s. Event alignment of these traces is retrospective and does not measure actuator lag.

**Interpretation limit.** Command timing is distinct from actuator response; one simulated pair.

**Source data.**
- `publication_q1/data/center_trace_windows.csv (timing pair)`
- `03_results/validation/publication_final_v1/tables/TAB_06.csv`

**Code.** `scripts/fig_center.py::plot_center_timing_alignment` · Files: `figures/Q1_C03_center_timing_alignment.png`, `figures/Q1_C03_center_timing_alignment.svg`
