# Center evidence enhancement v1

Additive analysis on the frozen Center baseline (`h2prism-center-baseline-v1`, `6fee8a0`). Nothing frozen was changed.

- [Results](CENTER_ENHANCEMENT_RESULTS.md)
- [Methods](CENTER_ENHANCEMENT_METHODS.md)
- [Discussion](CENTER_ENHANCEMENT_DISCUSSION.md)
- [Limitations](CENTER_ENHANCEMENT_LIMITATIONS.md)
- [Reproduce](CENTER_ENHANCEMENT_REPRODUCE.md)
- [Acceptance](CENTER_ENHANCEMENT_ACCEPTANCE.md)
- [Experiment F proposal (not run)](EXPERIMENT_F_PROPOSAL.md)
- [All tables](tables_bundle.md)

## Figure selection

Each retained figure answers one question that no table or other figure shows as directly.

| Figure | Question | Why retained |
|---|---|---|
| FIG_C01 intervention observability | What was tested; which outlet each sensor can see | Explains every later sensor effect (SID 215 has no branch meter) |
| FIG_C02 mechanism recognition (LOTO) | Does recognition survive self-template removal? | Headline negative result as counts |
| FIG_C03 mechanism ranking evidence | How close are competing mechanisms? | Shows near ties hidden by top-1 labels |
| FIG_C04 location ranking | Can the configured outlet be ranked? | Only figure showing which outlets are unrepresentable |
| FIG_C05 sensor-group sensitivity | Which sensor group carries location separation? | Ratio view; corrects the "MFS3 removal hurts" reading |
| FIG_C06 pressure vs flow contrast | Where does information lie in native units? | Only native-unit, dimension-safe view |
| FIG_C07 conditional exclusion map | Which rivals are excluded under declared bounds? | Hypothesis-level status behind the decisions |
| FIG_C08 exclusion thresholds | What precision separates hypotheses? | Exact onsets and correct-SPECIFIC windows |
| FIG_C09 decision transitions | How do decisions change with assumptions? | Shows wrong SPECIFIC under the restricted universe |
| FIG_C10 evidence breakdown | Why did D(Y) abstain? | Contrasts frozen and conditional reason codes |
| FIG_C11 capability map | What is established? | Synthesis of evidence levels |

A separate full-universe decision figure was dropped: all 336 cells are UNRESOLVED, which FIG_C09's footnote and FIG_C10 already state.
