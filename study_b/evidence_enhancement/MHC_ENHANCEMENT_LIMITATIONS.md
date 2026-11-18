# Study B evidence enhancement — Limitations

| Category | Item | Status |
|---|---|---|
| Fixed reproducibility issue | Ridge predictions were not saved at observation level | **Fixed**: bit-identical replay; predictions saved in `results/replay/replayed_predictions.csv.gz` |
| New descriptive evidence | Error mechanism, tail attribution, change dependence, resolution scale, controller role | Added (descriptive; 3 runs) |
| Source metadata conflict | Run 27: "Cycle time 15 min" vs 10-min overview value and 10-min logged switch-overs | Recorded, not corrected |
| Source metadata conflict | Run 26 note refers to "Experiments 67 and 68" | Recorded, not corrected |
| Source metadata | Run 24 possible safety-valve hydrogen release; run 27 back-pressure control error; late valve openings in runs 22, 23, 25 and 26 | Recorded as notes only; not labels |
| Initial state | Runs 28 and 29 start from an "undefined state"; run 25 inherits run 5's charge | Constrains interpretation |
| Instrument metadata | No P-2 or MFC-3 resolution or accuracy specification in the source | Observed increment used only as quantization |
| Control signals | MFC-3 setpoint and valve command not recorded | Control law cannot be modelled |
| Independence | 3 held-out workbooks, 2 dates, one apparatus; rows serially dependent | No intervals or tests |
| Unavailable truth | Fault labels, leak events, locations, qualified uncertainty | Fault classification, localization and formal D(Y) blocked |
| Environment | openpyxl 3.0.10 instead of pinned 3.1.5 (no installation performed) | Replay verified bit-identical |
| Future evidence needed | Independent compressor or apparatus, recorded controller setpoints, instrument specifications, qualified incident records | Required for transfer or diagnostic claims |
