# Q1_C02 — Controlled withdrawal response

**Scientific question.** How does a controlled outlet withdrawal appear in the measured channels?

**Caption.** Intervention minus matched control for the alternate-profile withdrawal at outlet SID 213 (both runs share the +5 kPa reservoir profile; the outlet area steps 0.0010 → 0.0011 m² at 1000 s in the intervention only). Exact recorded samples at 0.2 s, 900–1300 s. Branch flow MFS3 changes by up to 0.692 kg/s, junction pressure PS1 by at most 6.05e-04 MPa.

**Interpretation limit.** One matched simulation pair; difference traces, not detection performance.

**Source data.**
- `publication_q1/data/center_trace_windows.csv (hash-verified accepted captures, alternate_profile pair)`

**Code.** `scripts/fig_center.py::plot_center_controlled_response` · Files: `figures/Q1_C02_center_controlled_response.png`, `figures/Q1_C02_center_controlled_response.svg`
