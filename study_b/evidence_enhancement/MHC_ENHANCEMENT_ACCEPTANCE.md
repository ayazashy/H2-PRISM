# Study B evidence enhancement — Acceptance

**Decision: ACCEPTED WITH LIMITATIONS.**

| Gate | Result | Evidence |
|---|---|---|
| A — Source provenance | PASS | Size, MD5 and SHA-256 match the official and previously verified values; the frozen `verify_publication.py` passed |
| B — Frozen protocol | PASS | Frozen `protocol.json`, `read_run`, `pairs`, `score`, split, α = 100 and features reused unchanged |
| C — Prediction replay | PASS | 24/24 per-run metrics bit-identical, with counts matching (`results/replay/gate_frozen_replay.csv`) |
| D — Error analysis | PASS | All derived tables come from the replayed rows; ΔSSE totals reconcile with the frozen per-run RMSEs (P-2 −28.948 barg², MFC-3 −2.630 (ln/min)²) |
| E — Measurement interpretation | PASS | Units from workbook rows 10–11; increments labelled as observed quantization; controller role taken from source notes and checked against data |
| F — Independent units | PASS | Rows, runs and dates reported separately; no row bootstrap or p-values |
| G — Figures | PASS | 14 standalone PNG (3840 × 2160) + SVG + caption files, each inspected at reading size; no PDF |
| H — Frozen integrity | PASS | `git diff` against `2f36d15` is empty for every frozen Study B file (test `test_frozen_study_b_files_unchanged`) |
| I — Claims | PASS | No fault, localization, formal D(Y) or transfer claim (TAB_B08) |

**Why "with limitations":** 3 held-out workbooks on one apparatus; no instrument specification; MFC-3 is a controlled variable with an unrecorded setpoint; openpyxl version differs from the pin (outcome verified identical).
