# Literature benchmark

The evidence matrix is `tables/A17.csv`.

- **Sources.** DOIs were found by web search on 2026-11-18 in publisher or bibliographic listings. Verify each on the publisher page before formal citation.
- **Reported metrics.** These quote abstracts or listings. "NOT EXTRACTED" means the paper was not read for metrics.
- **Missing values.** Missing runtime or cost is NOT REPORTED, never zero.

## Comparability gate

No study passes the gate. Each differs in at least one of the following:

- task: dispersion modelling, image classification, or water networks;
- gas or system;
- data independence;
- metric definition.

**All comparisons are therefore contextual.** No head-to-head number is reported.

## Positioning

| Strand | Representative work | Relation to H₂-PRISM |
|---|---|---|
| Selective classification | Chow 1970 (10.1109/TIT.1970.1054406); Geifman & El-Yaniv 2017 (NeurIPS) | H1 is a risk–coverage question in this tradition. H₂-PRISM's registered test could not reach the coverage needed to compare. |
| Set-membership fault diagnosis | Puig 2010 (10.2478/v10006-010-0046-y) | D(Y) is an instance of interval consistency testing. Its distinctive elements are certificate re-verification, explicit unsupported-hypothesis handling, and refusal under an incomplete declared library. |
| Structural diagnosability | Krysander, Åslund & Nyberg 2008 (10.1109/TSMCA.2007.909555) | H₂-PRISM's isolability analysis is template-based (data-driven), not structural. A structural analysis would give sensor requirements independent of hypothetical bounds. |
| Leak localization with pressure sensors | Pérez et al. 2014 (10.1109/MCS.2014.2320336), water networks | Real-network, model-based localization with sensor placement. H₂-PRISM reaches only categorical Level 2 for one outlet. |
| Gas leak detection surveys | Murvay & Silea 2012 (10.1016/j.jlp.2012.05.010) | Context for detection methods. H₂-PRISM does not detect leaks in the field. |
| Hydrogen and hydrogen-blend pipelines | Zhu et al. 2022 (10.1016/j.ijhydene.2022.10.185); Lu et al. 2024 (10.1016/j.ijhydene.2024.02.075); IJHE review 2024 (10.1016/j.ijhydene.2024.04.140) | Mostly leakage and dispersion physics or modelling requirements. These define what a gas-specific transient model must capture (see `GAS_COMPOSITION_TRANSFER_ASSESSMENT.md`). They are not diagnostic baselines. |

## Strongest defensible distinctive contribution

**Evidence qualification that is auditable and verified to be monotone.**

- Every exclusion carries a re-checkable interval certificate.
- Removing information never creates an exclusion.
- The decision refuses to be specific when declared hypotheses are not modelled.

This is demonstrated conditionally, on one controlled simulation family under hypothetical bounds. It is not shown to improve diagnostic accuracy relative to published methods.
