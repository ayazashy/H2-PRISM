# H₂-PRISM Protocol 2.0: owner decisions to freeze the next protocol

- **For:** Yazan (dataset owner), Faisal (methods owner).
- **Prepared:** 2026-11-13, from the eight completed development-only ablation arms and the forensic audit. No new runs were made for this package.
- **Status:** Protocol 2.0 is **not active** and cannot run until the decisions below are recorded.

**Evidence status, which applies to every number below.** All eight arms are **development-only and exploratory**:

- each was trained and evaluated on the training topologies of each outer fold, never on a held-out topology;
- every window was already inspected as R2 outer-test data.

These results can inform design decisions. They cannot confirm any claim. Confirmation needs the independent simulations in Section 4.

## 1. What the eight arms showed (development means over 3 folds; same 27,993 windows)

| Arm | Change | Accuracy | Balanced accuracy | Scenario-group-balanced accuracy | ECE | Errors with confidence ≥ 0.9 | Flag-free share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | protocol 1.1 (reference) | 0.478 | 0.416 | 0.468 | 0.465 | 0.696 | 0.213 |
| B | source-model topology (v0.3) | **0.907** | 0.647 | **0.880** | 0.086 | **0.000** | 0.136 |
| C | 13 common sensors only | 0.524 | 0.461 | 0.488 | 0.411 | 0.799 | 0.267 |
| G1 | B + C | **0.913** | **0.722** | **0.902** | **0.046** | 0.612 | 0.244 |
| D, E, F | decision-layer components | identical to A (they do not change the classifier) | | | | | |
| G2 | B + C + D + E + F | identical to G1 | | | | | |

**Three findings drive the decisions:**

1. **The classifier improvement comes from the data correction (B / G1), not from the decision layer.** Correcting the topology attribution removes confidently wrong predictions (0.70 → 0.00 in B). It also makes confidence informative again: minimum correctness AUROC across development topologies is 0.07 in A and 0.51 in B.
2. **The `down` simulation model remains out of support** against the other two models, even on the 13 shared sensors. OUT_OF_SUPPORT flags are 0.17 in A, 0.67 in B and 0.64 in G1. Usable coverage exists only where development pairs two models of the same configuration (Center + Upstream: 73% flag-free in G1). This is why D2 is blocking.
3. **No decision-layer component adds measurable value on this dataset:**
   - D(x) inside s_C: at the only development-fixed operating point (G1, coverage 0.6), s_C, s_C−D and confidence all have scenario-group-balanced selective risk **0.091**.
   - The evidence-conflict policy and group-level support: not distinguishable from A (0-vs-0 risk floor).
   - E_h: **undefined for 80% of windows** (0.796; 0.788 in G2), minimum AUROC 0.49 vs D(x) 0.49 in F, and 0.27 in G2.
   - G2's mean AUROC gain of s_C over s_C−D (+0.121) rests on **one fold**: the meta-model is undefined in 2 of 3 folds.

## 2. Decisions for Yazan (dataset owner)

### D1: topology attribution of the event runs (R-18)

- **Evidence.**
  - The MATLAB/Simscape source models: only `*_gest_down.slx` logs PS11, PS12 and MFS4.
  - The export scripts write each NORMAL file from its own model.
  - All 18 runs in release folder `anom_gestcent` show the down-model sensor set; all 18 in `anom_gestdown` show the center-model signature.
  - In total, **36 of 57 manifest runs (32 eligible)** are attributed to the other topology's model.
  - Sources: `03_results/diagnostics/forensics/{source_model_attribution,simulation_model_sensors}.csv`; `01_dataset_audit/YAZAN_TOPOLOGY_DECISION_PACKAGE.md`.
- **Effect.** Development group-balanced accuracy 0.47 → 0.88 (B), 0.90 (G1).
- **Limitation.** No file in the release states the intended folder naming; only the dataset authors can confirm it.
- **Decision required:**
  - **A:** keep the release attribution;
  - **B:** adopt candidate manifest v0.3, i.e. `topology_source_model` beside the verbatim `topology_release`, with labels, families and files unchanged (all integrity checks pass, `CANDIDATE_MANIFEST_V03_CHECKS.json`);
  - **C:** ask the authors first.
- **Acceptance test if B:**
  - 57/57 runs consistent with their source model;
  - every outer fold a single configuration;
  - the diff of v0.2 and v0.3 touches only the topology column (36 rows) and the added columns;
  - R2 hashes unchanged.

### D2: physical equivalence of the "common" sensors (blocking)

- **Evidence (event runs, mean of window means):**

  | Sensor | `down` model | `center` and `up` models |
  | --- | --- | --- |
  | PS5 | 0.100 | 0.684 |
  | PS6 | 0.684 | 5.64–5.75 |
  | PS10 | 4.32 | 5.51–5.61 |
  | PS1 | 6.55 | 6.50–6.51 (agrees) |

  The down model stays out of support on all 13 shared sensors (finding 2).
- **Question.** Are PS1–PS10 and MFS1–MFS3 at the **same physical positions** in the three models, so that the differences are physics caused by the different withdrawal point? Or does the numbering refer to different locations?
- **Decision required:**
  - **Same positions:** the common-sensor representation stands, and leave-one-topology-out across configurations is a valid but hard transfer task.
  - **Different positions:** the shared set must be redefined from the model diagrams, and cross-configuration transfer is not a like-for-like task.
- **Acceptance test.** A sensor-position table per model (from the `.slx` diagrams or the authors) is attached to the manifest, and the feature register lists only position-matched sensors.

### D6: commission independent confirmation simulations (Section 4)

## 3. Decisions for Faisal (methods owner): one decision per component

| Component | Development evidence | Limitation | Proposed acceptance criterion for the confirmatory protocol | Decision |
| --- | --- | --- | --- | --- |
| **B source-model topology** (needs D1 = B) | group-balanced accuracy 0.47 → 0.88; confident errors 0.70 → 0.00; minimum confidence AUROC 0.07 → 0.51 | coverage lost (no registrable target) because of finding 2 | include if D1 = B | accept / reject |
| **C 13 common sensors** (needs D2) | alone: +0.02 group-balanced accuracy, confidence AUROC worsens (0.005); with B: ECE 0.086 → 0.046, balanced accuracy 0.647 → 0.722 | does not remove out-of-support | include only if D2 confirms position equivalence | accept / reject / redefine |
| **D independence-group support** | no classifier change (by design); counts each simulated scenario once (13 groups, not 39 families) | coverage cost (R2 exploratory: Center ceiling 0.258 → 0.184); risk comparison uninformative (0 vs 0) | **include as a scientific-integrity rule**, not as a performance improvement: pseudo-independent support must be 0 | accept / reject |
| **E evidence-conflict policy** | no measurable effect (0-vs-0 floor); ambiguity-set inclusion 1.0 where issued | no estimable operating point with errors to test it | optional design rule; evaluate only on confirmation data | accept / defer |
| **F E_h evidence margin** | **undefined for 80% of windows**; AUROC not better than D(x); meta-model undefined in 2 folds | needs ≥ 2 independent scenarios per neighbourhood, which this dataset rarely has | **not a validated improvement; exclude** from the frozen protocol; keep the code and its counterexample tests for re-evaluation on independent data | exclude / defer |
| **D(x) inside s_C** (registered RQ1 test) | no incremental value at matched coverage (0.091 vs 0.091) | single estimable operating point | keep **s_C vs s_C−D** as the one registered confirmatory contrast; interpret a null result as null | confirm contrast |
| **P2-E development-only target rule** | A: one registrable target; G1: one (0.6); B and F: none, NOT_ESTIMABLE_BY_DESIGN declared in advance | many folds not estimable under current data | include: targets are fixed from development attainability before any outer evaluation | accept / revise |
| **P2-F fail-closed meta-model** | recorded "undefined" instead of crashing in B (1 fold), F and G2 (2 folds) | none | include (no fallback score ever substituted) | accept / reject |
| **Inference units (D4)** | 51 runs = 13 independence groups (NORMAL 1, DELAY 1, FAULT 1, LEAK 10) | intervals on current data are not meaningful | bootstrap by independence group, stratified by topology; one registered contrast; effect sizes only | accept / revise |

**Freeze rule.** The protocol is frozen when D1, D2 and every component decision above are recorded. The frozen config is then the candidate config with the accepted components, a new status and a pinned hash, plus a pinned inner-fold record for v0.3. It must never be tuned on the current data.

## 4. Independent simulation evidence required for confirmation

Full specification: `02_methodology/INDEPENDENT_CONFIRMATION_DATA_SPEC.md`.

| Requirement | Minimum |
| --- | --- |
| New scenario ancestors | none of the current 13 independence groups (17 scenario stems) reused with the same parameters |
| Thin classes | **≥ 3 independently parameterised scenarios per class per topology** for NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY (different operating points, fault severities and delay times; not only noise seeds); ≥ 5 for LEAK |
| Topology fidelity | each topology simulated with its own model; position-matched sensor set (D2); absent sensors left missing, never padded constants |
| Provenance | model file hash, solver and step, parameter values, noise seed and export script per run |
| Confirmation partition | fixed and hashed before any analysis; never used for selection |
| Generalisation | a fourth topology or an independent replicate network before any cross-network claim |
| Confirmatory run | the frozen protocol, once, under a new authorization; the registered contrast s_C vs s_C−D at the development-fixed target; secondary metrics reported as secondary |

## 5. Preservation

Nothing in this package changes recorded outputs.

| Item | State |
| --- | --- |
| R2 | `a10530f1fcf2`, hash list verified |
| R1 | archived invalid |
| Seven registered sensitivity runs and the incomplete offset run | unchanged |
| Eight ablation runs | hash lists in `03_results/ablation_runs/logs/`; external backup verified |
| Commits | `0a0a9e2` (R2 code), `ddb91ae`, `6f768a2`, `6301e62`, `dd5def7`, `d3b6cde`, `81baba4` |
