# Study B — evidence enhancement v1

Additive explanation of the accepted MHC benchmark (`2f36d15`). No frozen file changed.

- [Results](MHC_ENHANCEMENT_RESULTS.md)
- [Methods](MHC_ENHANCEMENT_METHODS.md)
- [Discussion](MHC_ENHANCEMENT_DISCUSSION.md)
- [Limitations](MHC_ENHANCEMENT_LIMITATIONS.md)
- [Reproduce](MHC_ENHANCEMENT_REPRODUCE.md)
- [Acceptance](MHC_ENHANCEMENT_ACCEPTANCE.md)
- [All tables](results/tables_bundle.md)

## Figure selection

| Figure | Question | Why retained |
|---|---|---|
| FIG_B01 measurement context | Which system and channels? | Only source-grounded view of where P-2 and MFC-3 sit |
| FIG_B02 P2 / MFC3 prediction traces | How do predictions track the data? | Shows the real signals over source-declared windows |
| FIG_B03 P2 / MFC3 per-run performance | Is the ranking stable across runs? | Run-level view; units kept separate |
| FIG_B04 P2 / MFC3 error ECDF | Central versus tail errors | Shows the exact-zero mass behind the MAE ranking |
| FIG_B05 P2 / MFC3 error concentration | Do rare errors dominate RMSE? | Shows both models share the same tail |
| FIG_B06 P2 / MFC3 error versus change | Where does Ridge gain or lose? | The mechanism of the metric disagreement |
| FIG_B07 resolution versus error | Are differences physically resolvable? | Puts every difference on the recording grid |
| FIG_B08 MFC-3 control role | Why does MFC-3's role matter? | Data-grounded evidence that MFC-3 is a controlled release |
| FIG_B09 evidence matrix | What does MHC support? | Synthesis |

Pressure and flow figures are kept separate because their units differ. A separate conceptual "control semantics" diagram was not drawn, because the setpoint signals it would depict are not recorded. FIG_B08 uses measured data instead.
