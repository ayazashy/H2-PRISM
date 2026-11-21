# AV-F15 — Actual cross-study software portability

**Scientific question.** Is the same diagnostic engine actually executed across Center, MHC and HY2RES?

**Caption.** Component-by-component code paths (A12). Import inspection shows that the MHC and HY2RES pipelines import no module of the h2prism package; formal D(Y) (certified_evidence.diagnose) has been executed only on Center. Only the presentation layer (Q1 figure style) is shared. Diagnostic portability across the three studies is therefore not demonstrated; code reuse alone would not demonstrate it either.

**Interpretation limit.** Code inspection; not a performance result.

**Source data.**
- `advanced_validation/tables/A12.csv`

**Code.** `scripts/fig_av.py::plot_av_portability` · Files: `figures/AV-F15_software_portability.png`, `figures/AV-F15_software_portability.svg`
