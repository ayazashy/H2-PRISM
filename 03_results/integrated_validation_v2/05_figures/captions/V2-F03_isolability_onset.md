# V2-F03 — Pairwise isolability matrix

**Scientific question.** For each hypothesis pair, how much tighter than REF must the bounds be for no observation to fit both?

**Caption.** λ* is the largest bound scale, in units of the REF solver-refinement delta, at which the pair is template-isolable over all ±1 s shifts (isolable iff λ < λ*). Normal vs SID 215 needs bounds about 0.08 × REF even with all channels: a bound limitation, not intrinsic identity (λ* > 0). Pressure-only sensing cannot separate the withdrawals at REF.

**Interpretation limit.** Template-level analysis of one capture per mechanism under hypothetical bounds; says nothing about field sensors.

**Source data.**
- `03_results/integrated_validation_v2/04_results/analysis/i1_isolability_onset.csv`

**Code.** `scripts/fig_v2.py::f03` · Files: `figures/V2-F03_isolability_onset.png`, `figures/V2-F03_isolability_onset.svg`
