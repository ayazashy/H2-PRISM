# Study C evidence enhancement — Limitations

| Category | Item | Status |
|---|---|---|
| Fixed reproducibility issue | The CSV in Git history is LF-normalised and fails the official MD5 | Documented; restoring CRLF line endings reproduces the official bytes exactly |
| Resolved reporting ambiguity | "72.5 % unresolved" lacked a mechanism | Decomposed: 97.8 % tank out of support, 1.3 % invalid input, 0.9 % empty cell |
| Resolved reporting ambiguity | Meaning of pressure MAE/RMSE differences | Expressed against the 0.1 bar recording grid and the step classes |
| Descriptive finding | Tank-pressure drift beyond development support | Temporal association only |
| Descriptive finding | Flow-based state separation is zero vs positive production | Rank probability 0.945 → 0.554 on positive flow |
| Historical test reuse | Test period previously inspected; no access seal | Every result descriptive; no new threshold evaluated |
| Unverified prerequisite | Instrument resolution, accuracy, synchronisation | Not documented in the source |
| Missing physical truth | Fault labels, event mechanisms, leak locations, qualified bounds | Fault, localisation and formal D(Y) blocked |
| Label restriction | Operating states derive from electrical draw | Not equipment-fault labels |
| Single system | One residential pilot, three weeks | No transfer claim |
| Repository integrity (outside Study C results) | Conflict markers committed in 11 shared files by merge `abed1c1` (for example `src/h2prism/windows.py`, `configs/frozen_evaluation_config.yaml`, `02_methodology/*.md`) | Not modified here; must be resolved before integration |
| Cannot be removed by code | Domain shift in the test period, minority-state scarcity, absent physical labels | Needs new, independent evidence |
