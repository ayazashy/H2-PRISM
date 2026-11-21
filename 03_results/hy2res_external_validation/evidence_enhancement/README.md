# Study C — evidence enhancement v1

Additive, descriptive analysis of the published HY2RES package (`6a926de`). No published file changed.

- [Results](HY2RES_ENHANCEMENT_RESULTS.md)
- [Methods](HY2RES_ENHANCEMENT_METHODS.md)
- [Discussion](HY2RES_ENHANCEMENT_DISCUSSION.md)
- [Limitations](HY2RES_ENHANCEMENT_LIMITATIONS.md)
- [Reproduce](HY2RES_ENHANCEMENT_REPRODUCE.md)
- [Acceptance](HY2RES_ENHANCEMENT_ACCEPTANCE.md)
- [All tables](results/tables_bundle.md)

## Figure selection

| Figure | Question | Why retained |
|---|---|---|
| FIG_H01 pressure quantization | What is the recording grid? | Establishes the 0.1 bar grid from the full source |
| FIG_H02 error in increments | How large are errors relative to the grid? | Shows persistence's exact 0 or 1 step structure |
| FIG_H03 error trade-off | Why RMSE improves while MAE worsens | Decomposes ΔSSE by recorded step |
| FIG_H04 tank-pressure drift | How does tank pressure evolve? | Main drift evidence with the support boundary |
| FIG_H05 support violations | Which channels breach support? | Shows only the tank breaches |
| FIG_H06 unresolved mechanisms | Why so many abstentions? | Reconciles exactly to 32,308 |
| FIG_H07 decision validity over time | Does abstention follow the breach over time? | Temporal view, distinct from the totals |
| FIG_H08 state decision matrix | Which states get which outcome? | Makes the 0 / 817 minority result explicit |
| FIG_H09 positive-flow distinguishability | Does separation survive without zero flow? | Shows 0.945 → 0.554 |
| FIG_H10 evidence matrix | What is supported? | Synthesis |

All ten candidate blueprints were retained, because each answers a distinct question.
