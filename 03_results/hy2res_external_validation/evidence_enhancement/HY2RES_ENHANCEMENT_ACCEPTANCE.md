# Study C evidence enhancement — Acceptance

**Decision: ACCEPTED WITH LIMITATIONS.**

| Gate | Result | Evidence |
|---|---|---|
| A — Official source | PASS | 38,621,947 bytes, MD5 9a3c3e3b… (publisher value) |
| B — Frozen benchmark | PASS | 60/60 archived metric reconciliations; maximum difference 9e-17 |
| C — Decision reproduction | PASS | Replica and original script both reproduce the published counts (10,762 / 1,126 / 31,279; 201 / 616; 413; 32,002) |
| D — Temporal integrity | PASS | Development ends 2024-04-09 02:34:59 and test starts 2024-04-12 12:13:56; 0 shared development/test segments; lag-1 same-segment inputs only; no interpolation |
| E — Support validity | PASS | Channel reasons reproduce the frozen min–max guard; exclusive reasons sum exactly to 32,308 |
| F — Interpretation | PASS | 0.1 bar labelled as recording increment, never as instrument accuracy |
| G — Figures | PASS | 10 standalone PNG (3840 × 2160) + SVG + caption files, each inspected |
| H — Reproducibility | PASS | Deterministic reruns; 6 focused tests pass |
| I — Frozen preservation | PASS | No published Study C file changed (`git diff` against `6a926de` is empty outside this directory) |
| J — Claims | PASS | No diagnostic, localisation, D(Y) or transfer claim (TAB_H09) |

**Why "with limitations":** one previously inspected pilot record; no physical truth; no instrument specification.

**Separate blocker for integration, outside Study C's results:** merge `abed1c1` committed unresolved conflict markers into 11 shared repository files on the published branch. As a result, the existing `tests/test_faisal_pipeline.py` cannot import `h2prism.windows`. This enhancement does not modify those files.
