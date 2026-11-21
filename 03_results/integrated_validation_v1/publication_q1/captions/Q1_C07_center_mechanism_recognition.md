# Q1_C07 — Mechanism recognition with and without self-templates

**Scientific question.** Does mechanism recognition survive removal of the query's own template?

**Caption.** Nearest-mechanism label (normalized B3 RMS, all sensors, 30 s prefix, ±1 s shift) for each controlled query. With its own template present every query is labelled correctly at distance 0 by construction. With the own template excluded, 2/4 supported controlled queries agree (QN, the nominal run, is matched to a near-duplicate nominal transient), 2 are unsupported, and Q213-alt matches only because a near-duplicate SID 213 template exists. Counts from one source family.

**Interpretation limit.** Seven queries from one simulation family; counts, not rates.

**Source data.**
- `03_results/validation/center_evidence_enhancement/tables/TAB_C02.csv`

**Code.** `scripts/fig_center.py::plot_center_mechanism_recognition` · Files: `figures/Q1_C07_center_mechanism_recognition.png`, `figures/Q1_C07_center_mechanism_recognition.svg`
