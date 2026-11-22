# Q1_I04 — Mechanism-recognition potential

**Scientific question.** How much of the apparent recognition survives independent templates?

**Caption.** Nearest-mechanism recognition for the 7 controlled Center queries (normalized B3 RMS, all sensors). With the frozen library every query matches a self (5) or near-duplicate (2) template. Excluding the own template leaves 5 supported queries, of which 3 agree; adding the alternate-profile SID 213 capture as a replicate raises agreement to 4/5. Counts from one source family, not rates; details in Q1_C07.

**Interpretation limit.** Seven queries from one controlled simulation family; not a classification accuracy.

**Source data.**
- `03_results/validation/center_evidence_enhancement/tables/TAB_C07.csv`

**Code.** `scripts/fig_integrated.py::plot_integrated_mechanism_recognition` · Files: `figures/Q1_I04_integrated_mechanism_recognition.png`, `figures/Q1_I04_integrated_mechanism_recognition.svg`
