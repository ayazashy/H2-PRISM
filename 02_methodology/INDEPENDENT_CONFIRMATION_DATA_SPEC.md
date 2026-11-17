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

## Generation readiness (2026-11-13; from the released MATLAB/Simscape artifacts)

**Sensor mapping for new runs.** Use the diagram position map `06_audit_preparation/protocol2/CANDIDATE_SENSOR_POSITION_MAP_V01.csv`, not the column names. The down model logs other sensor blocks under PS5–PS10 (`03_results/diagnostics/sensor_correspondence/SENSOR_CORRESPONDENCE.csv`). Each new run's export must:

- record the block identity (SID) of every logged channel;
- keep each model's own channel list;
- leave sensors absent from a model missing, never padded.

**What the release can regenerate, and what it cannot:**

| Item | In the release | Usable for new scenarios? | Missing |
| --- | --- | --- | --- |
| Normal models `Normal_HNetwork_gest_{center,down,up}.slx`, `models_launcher.m` (ode14x, fixed step 0.8 s center / 0.9 s down and up), `save_model_data_*.m` | yes | **yes, for NORMAL**: vary the supply step (`PS Step` 3 → 6.4 MPa at 25 s), the ramp (`PS Ramp` −0.3 MPa, −1e-5 MPa/s from 10 s), compressor pressure differentials (4 MPa; −1 MPa on the down model's extra source) and the withdrawal restrictions | parameter ranges for "independently parameterised" operating points (author decision) |
| Anomalous models `Anomalous_HNetwork_gest_*.slx` | yes, but **only the last saved state**: one variable restriction (SID 213, PS1/MFS3 node) driven by `PS Step1`; open (0.001 m², t = 1 s) in down, closed (1e-10 m²) in center and up | **LEAK at G3 only** (restriction 213) | how the leaks at G4, G5 and G6, the compressor faults and the compressor delays were imposed (block edits, parameter sets, timings) |
| Anomalous export script | no (the generic `save_model_script.m` maps pressure_sensorN → PSN) | yes, with the position map | an export that also writes block identities |
| Noise | README: Gaussian white noise, about 1–2% of typical range | partially | the noise script, seeds and per-channel σ; without them, new noise_added runs are not the same procedure |
| Manifest provenance (model hash, solver, step, parameters, seed) | not in the release | — | required for every new run (table above) |

**Independence.** A run is a new ancestor only if its physical parameters differ. These do **not** create new independence groups, because they share the ancestor's physics:

- re-noising an existing run;
- re-exporting, re-windowing or relabelling a run;
- running the same parameter set under another folder name.

**Development and confirmation separation:**

- **Development:** all current 51 eligible runs.
- **Confirmation:** only new ancestors, with the partition hashed before the first analysis.
- No current run may enter the confirmation partition.

**Readiness verdict.**

- NORMAL scenarios and LEAK-at-G3 variants can be generated now from the shipped models.
- The other LEAK positions, COMPRESSOR_FAULT and COMPRESSOR_DELAY need the authors' scenario definitions or a re-specification by the dataset owner.
- **D6 is therefore not executable for all four classes from the release alone.**
