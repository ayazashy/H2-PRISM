# Independent confirmation data: specification (protocol 2.0)

Every window of the current dataset was an R2 outer-test window and informed the candidate design. **No evaluation on these windows can confirm protocol 2.0.** Confirmation needs data that shares no scenario ancestor with them.

## Minimum requirements

| Requirement | Why | Acceptance test |
| --- | --- | --- |
| **New scenario ancestors only:** no stem of the current 17 (e.g. `CONSTANT_SEGMENT_LEAKG3`) with the same parameters | independence from everything inspected | the independence-group map of new runs is disjoint from the current 13 groups |
| **At least 3 independently parameterised scenarios per class per topology** for NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY (different operating points, fault severities and delay times; not only noise seeds); at least 5 for LEAK at untested restriction positions or severities | thin classes currently rest on one independence group, so no support rule can be met | ≥ 3 groups per thin class per topology |
| **Each topology simulated with its own model** and the same sensor set; exported with the model's own sensor list (no padded constants) or with explicit missing values | FA-01 / FA-02 | `forensic_audit.py` attribution 100% consistent; no zero-variance channel |
| **Recorded generation metadata:** model file hash, solver and step, parameter values, noise seed, export script | provenance | manifest columns present for every run |
| **A held-out confirmation partition fixed before any analysis** (e.g. one complete new topology, or a pre-registered subset of new ancestors), never used for selection | confirmation | partition hash pinned in the protocol 2.0 config before the first run |
| **For generalisation claims, a fourth topology or an independent replicate network** | three topologies, one compromised, cannot support generalisation | present or claim withheld |

## Confirmatory design

1. Freeze protocol 2.0, including the target rule, on the current data at development stage only.
2. Run once on the new confirmation partition under an authorization scoped to it.
3. Report the single registered contrast: s_C vs s_C−D at the development-fixed target, rank matched, with group-level units.
4. Report every secondary metric as secondary.
