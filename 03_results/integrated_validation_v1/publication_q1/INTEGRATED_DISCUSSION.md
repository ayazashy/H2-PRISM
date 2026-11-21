# H₂-PRISM integrated validation — Discussion

## 1. What the integrated evidence establishes

**Reference prediction on real hydrogen measurements is validated within scope.**

- In MHC (experimental) and HY2RES (operational), the frozen references reproduce exactly. The pressure targets are recorded on fixed grids (0.2 barg; 0.1 bar), and persistence is exact on 71–96 % of rows (Q1_I03).
- The learned Ridge reference wins RMSE by less than 0.1 of a recorded step on every pressure channel. It loses MAE except on HY2RES tank pressure (Q1_I02, T03).
- A learned reference is not shown to be practically better than persistence. Any such claim would have to be made in recording increments.

**Evidence validity is measurable and informative.**

- In HY2RES, 97.8 % of the frozen rule's abstentions are tank pressure outside the development range (Q1_H10). This follows a drift that development-only checks could not reveal (Q1_H09).
- Out-of-support, invalid-input and empty-cell abstentions are distinct from ambiguity. Separating them is a concrete design recommendation.

**Controlled mechanism evidence is sensor-dependent.**

- On Center, each outlet excites a different sensor group (Q1_C01).
- Location ranking succeeds only where an independent same-outlet template exists (Q1_C09).
- Separation is carried by branch flow (Q1_C10). The asymmetry matters: SID 215 has no branch meter and is visible only in kilopascal-scale pressure contrasts.

## 2. What the formal decision layer contributes

- **Conditional demonstration on Center.** Under declared hypothetical bounds, formal D(Y) produces all three outcomes on Center, but its semantics depend on the declared universe:
  - **Full universe:** the three unmodelled hypotheses keep it UNRESOLVED.
  - **Restricted universe:** it decides, and every wrong SPECIFIC decision has an unrepresented true mechanism (H1-F06).
- **Contrast with confidence scores.** This is the one decision-relevant property a confidence score cannot provide: refusing to decide because the hypothesis library is incomplete. It is also its main risk when the library is silently restricted.
- **What D(Y) needs and lacks.** It needs qualified observation and model bounds and a complete adapter library. No study supplies these (Q1_I07).

## 3. H1 and the research questions

**RQ1 / H1.** The registered verdict is NOT_ESTIMABLE, and the root causes are now quantified:

1. The source-folder attribution defect concentrates 91.7 % of errors in disputed runs.
2. Single-family neighbourhoods trigger the support flags.
3. Center coverage is 0.258, below every registered target.

The exploratory reanalysis inside the shared region is inconclusive. Point estimates favour D(x), but the intervals include 0, the information comes from 1–3 scenario templates, and neither policy errs outside disputed runs.

The strongest positive *descriptive* result: the evidence-support guard withheld 78 % of classifier errors that conventional confidence abstention would have issued. This is confounded with the defect.

**RQ2.** No incremental value of D(x) where estimable (development ablation). This is unchanged.

**RQ3.** Where evaluable, the three-outcome policy issued no wrong SPECIFIC decision, and all ambiguity sets contained the truth. The support is thin: one or two families per thin class.

## 4. Implications

- The project's demonstrated contribution is a **qualification framework**, not a diagnostic accuracy. It makes explicit when evidence is insufficient: out of support, unsupported hypothesis, single-family neighbourhood, or recording grid coarser than the claimed improvement.
- A confirmatory H1 test needs new, independent scenario templates and a pre-registered estimability check on development data (`../h1_validation/H1_CONFIRMATION_REQUIREMENTS.md`).
- No fault classification, leak localization, certified D(Y) or industrial transfer is claimed.
