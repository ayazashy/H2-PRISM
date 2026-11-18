# V2-F05 — Cross-domain software portability (Level A)

**Scientific question.** When the frozen HY2RES operating-state rule is run through the formal engine, which of its decisions survive certification?

**Caption.** The port reproduces every ambiguous and unresolved decision of the frozen rule, but none of its 10,762 singleton calls: the rival state is never excluded by a single-channel certificate, so they become UNRESOLVED. No certified decision is wrong. Frozen-rule UNRESOLVED rows are split by the reason the certified port records for the same rows.

**Interpretation limit.** Level A software portability only: no measurement uncertainty is declared, labels describe electrical power, and the partition was inspected before.

**Source data.**
- `03_results/integrated_validation_v2/04_results/analysis/h1_hy2res_certified_vs_frozen.csv`
- `03_results/integrated_validation_v2/04_results/analysis/h2_hy2res_equivalence_summary.csv`

**Code.** `scripts/fig_v2.py::f05` · Files: `figures/V2-F05_hy2res_certified_port.png`, `figures/V2-F05_hy2res_certified_port.svg`
