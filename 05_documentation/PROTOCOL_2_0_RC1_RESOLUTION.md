# Protocol 2.0: scientific resolution and release candidate RC1

- **Date:** 2026-11-13.
- **Directions:** project lead's design directions D1, D2 and D6. They are not Yazan's or Faisal's attestations.
- **Evidence status:** everything here uses existing artifacts only. No classifier was trained and no held-out data were scored. Every performance number is **EXPLORATORY_DEVELOPMENT** unless it is labelled R2.

## 1. D1: topology attribution (recommendation, not a decision)

**Recommendation: adopt candidate manifest v0.3 (option B) for development.** Keep it unapproved until Yazan records D1.

**Traceability:**

| Link | Evidence |
| --- | --- |
| Source model ↔ run | Only the down model logs PS11, PS12 and MFS4 (diagram: ToWorkspace blocks; `SENSOR_TRACE.csv`). The 18 runs of `anom_gestcent` carry them; the 18 of `anom_gestdown` do not (`forensics/source_model_attribution.csv`). |
| Model files | SHA-256 of all six `.slx` files in `03_results/diagnostics/sensor_correspondence/MODEL_FILES.csv` |
| Changed assignments | 36 of 57 runs (32 eligible): `CANDIDATE_MANIFEST_V03.csv`, column `topology_source_model`. `topology_release` is kept verbatim. |
| Unchanged | Raw files, labels, families and release folders (`CANDIDATE_MANIFEST_V03_CHECKS.json`, all pass) |
| Preserved | v0.2 manifest and R2 `a10530f1fcf2` (hash list re-verified by `tests/test_protocol2_release_candidate.py`) |

**Performance is not evidence for the attribution.** The attribution rests on the logged-sensor sets of the source models alone.

## 2. D2: sensor correspondence, resolved from the `.slx` diagrams

**Method.** `tools/dataset/trace_slx_sensors.py` parses the six models. Each logged variable is traced through this chain:

1. ToWorkspace;
2. Inport;
3. From/Goto tag;
4. PS-Simulink converter;
5. sensor block;
6. physical net;
7. adjacent pipes, restrictions, compressors and reservoirs.

The CSV export scripts map `pressure_sensorN → PSN` and `flow_sensorN → MFSN` (`save_model_data_*.m`, `save_model_script.m`). No signal value is used.

**Outputs:** `03_results/diagnostics/sensor_correspondence/`:

- `SENSOR_CORRESPONDENCE.csv`, the requested table: sensor, model, block, quantity, units, node, distance to the nearest compressor outlet, same block elsewhere, verdict, evidence, status;
- `SENSOR_TRACE.csv`;
- `NETWORK_EDGES.csv`;
- `MODEL_FILES.csv`.

**Network difference.** The three models share one trunk. They differ in where a withdrawal branch attaches:

- **center:** restriction 453, pipe 5 (4 km), sensor 418 and reservoir 195, attached at the PS4 junction;
- **up:** the same branch, attached at the pipe 3 / pipe 8 / MFS1 junction;
- **down:** the branch is replaced by restriction 172, a third pressure source (−1 MPa, constant), pipe 6 (3 km) and reservoir 195. It carries four new sensors (blocks 402, 403, 196 and 134).

The down model's logging subsystem numbers sensors in a different order.

**Verdict per release name:**

| Name | center / up block | down block | Verdict |
| --- | --- | --- | --- |
| PS1, PS2, PS3, MFS1, MFS2, MFS3 | 50, 51, 52, 311, 210, 218 | same | **VERIFIED_SAME_BLOCK_SAME_NODE** |
| PS4 | 109 | 109 | **SAME_BLOCK_DIFFERENT_JUNCTION**: the branch attaches at this node in center and down (via different restrictions), not in up |
| **PS5** | 187 (compressor 3 inlet / supply reservoir) | **134** (end of the new 3 km pipe 6, atmospheric reservoir) | **DIFFERENT PHYSICAL SENSOR** |
| **PS6** | 318 (compressor 1 outlet) | **187** (= center/up PS5) | **DIFFERENT PHYSICAL SENSOR** |
| PS7 | 392 (compressor 3 outlet) | 318 (= center/up PS6) | DIFFERENT PHYSICAL SENSOR |
| PS8 | 418 (withdrawal branch; not in down) | 392 (= center/up PS7) | DIFFERENT PHYSICAL SENSOR. Block 418 is at a different junction in center vs up. |
| PS9 | 428 | 402 (inlet of the down model's extra source) | DIFFERENT PHYSICAL SENSOR |
| **PS10** | 431 (same node as PS3) | **403** (outlet of the down model's extra source) | **DIFFERENT PHYSICAL SENSOR** |
| PS11, PS12 | not logged (release pads constants) | 428, 431 (= center/up PS9, PS10) | names exist only in down; the blocks are the center/up PS9/PS10 |
| MFS4 | not logged (padded 0) | 196 | down-only sensor |

**Consequences:**

- The "13 common sensors" of arms C and G1 compare **six different physical sensors** for down-model runs. C is refuted as a common-sensor representation. The C/G1 results describe a mixed representation.
- A physically defensible shared set exists: **12 sensor blocks logged by all three models**. The candidate map is `CANDIDATE_SENSOR_POSITION_MAP_V01.csv` (sha256 in `.sha256`). It has:
  - canonical names = the center/up names;
  - five down-model columns renamed: PS6→PS5, PS7→PS6, PS8→PS7, PS11→PS9, PS12→PS10.
- 11 of the 12 sit at an identical node in all three diagrams. PS4 sits at a junction whose attached branch differs.
- PS3, PS10 and MFS2 share one node, so they are not independent positions.

**Limits:**

- Units are Simscape defaults (MPa, kg/s; converters set to `inherit`), not stated in the release.
- No anomalous export script ships with the release. The anomalous mapping relies on the generic `save_model_script.m` convention.
- A shared node does not mean equal operating conditions: the withdrawal branch differs by design.

**Non-evidentiary consistency check.** Not used for the mapping. The mapped means agree across models (`CHANNEL_SHIFT.csv` before mapping; e.g. PS5 = 0.684 in all three after mapping).

**Status:** VERIFIED_FROM_DIAGRAM for each row. **Owner acceptance is still required:** Yazan, D2.

## 3. B vs G1: "high-confidence errors"

Source: `03_results/diagnostics/high_confidence/HIGH_CONFIDENCE_ERRORS.csv` and `..._COMPOSITION.csv`, recomputed from `dev_oof.parquet`.

**What the 0.000 / 0.612 metric measures.** `share_errors_conf_ge_0_9` = #(wrong ∧ confidence ≥ 0.9) / **#wrong**. Its denominator is each arm's own error count, so B and G1 values are not on a common base. They must not be averaged or ranked.

| Arm | Errors | Confident predictions | Confident errors | Share of errors confident | Error rate among confident | Independence groups behind the confident errors |
| --- | --- | --- | --- | --- | --- | --- |
| A | 29,230 | 37,403 | 20,348 | 0.696 | 0.544 | 12 |
| B | 5,214 | 18,708 | 0 | 0.000 | 0.000 | 0 |
| G1 | 4,873 | 44,126 | 2,984 | 0.612 | 0.068 | **1** |

The counts are pooled window × fold instances: each window enters two outer folds' development sets.

**Interpretation:**

- **B's 0.000** holds because B is almost never confident where the down model is involved: 22 and 24 confident windows of 18,662 in folds 1 and 3. Every confident prediction is in fold 2 (Center + Upstream), where B makes no error. B's errors exist (NORMAL, LEAK, FAULT and DELAY); B simply does not commit to them.
- **G1's 0.612**: all 2,984 confident errors are **NORMAL predicted as LEAK**. They come from the three NORMAL runs, which form **one independence group**. As an error rate among confident predictions, G1 is 0.068.
- **Resolution.** Both observations stand; neither is "better". They answer different questions, and the G1 figure rests on one independent scenario (n_eff = 1).
- **Evidence needed:** at least 3 independently parameterised NORMAL scenarios per topology (D6).

## 4. OUT_OF_SUPPORT in the down model: root cause

**Method.** `tools/experiments/diagnose_out_of_support.py` recomputes **only** the unsupervised support geometry behind the flag: mean distance to the k = 25 nearest neighbours, in reference-standardized features, against the reference's leave-one-family-out 99th percentile. It does this for every ordered pair of source models, under three input representations. No classifier is fitted and nothing is scored. Status: EXPLORATORY_DIAGNOSTIC.

Outputs (`03_results/diagnostics/out_of_support/`):

- `SUPPORT_BY_REPRESENTATION.csv`
- `DISTANCE_CONTRIBUTION.csv`
- `CHANNEL_SHIFT.csv`
- `DEV_OOS_BY_FOLD.csv`

| Query model → reference model | Name-matched 13 (arms C/G1) | Position-matched 12 (map v0.1) | 11 identical-node blocks |
| --- | --- | --- | --- |
| down → center | **0.917** OOS | **0.007** | 0.007 |
| down → up | **0.908** | **0.006** | 0.006 |
| center → down | **1.000** | 0.007 | 0.007 |
| up → down | **1.000** | 0.007 | 0.007 |
| center ↔ up | 0.007 | 0.007 | 0.006–0.007 |
| within model (LOFO baseline) | 0.010 | 0.010 | 0.010 |

**Root causes, ranked by evidence:**

1. **Sensor naming, not physics (confirmed).**
   - Under name matching, PS5 and PS6 alone carry 63% of the squared standardized distance of down windows (0.40 and 0.23). Next come PS8 (0.06) and PS10 (0.06), all renamed blocks.
   - With the diagram mapping, the down model's mean k-NN distance to center/up (3.3) equals within-model distances (3.6). No channel dominates (each ≤ 0.10).
   - The development flag pattern matches: the down model is OOS in 0.91–1.00 of windows whenever it is paired with another model in B and G1 (`DEV_OOS_BY_FOLD.csv`).
2. **Asymmetric scale under name matching.** With the down model as reference, center/up windows lie at a median distance of about 10⁴ in the name-matched-13 geometry. The down model's PS5 is the atmospheric end node of pipe 6 and has almost no variance, so the center/up PS5 values (a different sensor) explode after standardization. B's 16-channel geometry also contains the padded constants PS11, PS12 and MFS4. Its 1.00 OOS share in folds 1 and 3 is consistent with both effects, but this diagnostic did not separate them for B.
3. **Not supported as causes:**
   - **Feature scaling:** reference-fold standardization is unchanged across representations, and the effect disappears with mapping alone.
   - **Operating conditions or withdrawal physics:** they do differ by design, but they leave the mapped sensors inside support.
   - **Baselines or incomplete scenario support:** these limit thin-class *decision* support (13 groups), not OUT_OF_SUPPORT.

**What this does and does not show:**

- It shows that a position-matched representation removes the out-of-support failure in the support geometry.
- It does **not** show classifier or decision performance under that representation. That needs development arm H, registered but not authorized.
- Genuine physical differences are kept: nothing is normalized per model.

## 5. D(x) and decision quality

**The operational claim D(x) supports:** *the fraction of the k = 25 nearest development windows (inverse-distance weighted, own family excluded) that agree on one class*. It measures neighbourhood agreement. It is not physical distinguishability, independent evidence, or correctness.

| Aspect | Evidence (development) |
| --- | --- |
| Correctness | G1 accuracy 0.913. NORMAL recall reaches 0.003 in one fold: the worst scenario group is NORMAL. |
| Confidence | G1 ECE 0.046; min AUROC(conf→correct) 0.615 |
| D(x) agreement | min AUROC(D_only) over development topologies: A 0.494, B 0.500, C 0.289, G1 0.341. At or below chance for correctness in at least one topology of every arm. |
| Independent support | 13 independence groups; NORMAL, FAULT and DELAY have 1 each |
| Increment of D(x) in s_C | group-balanced selective risk equal (0.091 vs 0.091) at the single estimable G1 point. At window level s_C has 0.086 vs s_C−D 0.108 and confidence 0.080 (windows are not independent units). |
| E_h | kept separate; excluded (undefined for ~80% of windows) |

**Evidence for D(x):** a small window-level reduction of risk inside s_C in G1.

**Evidence against D(x):**

- no group-level increment;
- standalone AUROC at or below chance in at least one topology of every arm;
- not estimable in B and F.

**SPECIFIC decisions are not forced.** Every non-estimable point stays NOT_ESTIMABLE (`03_results/consolidated/DECISION_LAYER_COMPARISON.csv`).

## 6. Consolidated comparison

Source: `03_results/consolidated/CONSOLIDATED_COMPARISON.csv`, built by `tools/experiments/consolidated_comparison.py` from existing outputs only. The development rows and R2 use different evaluation sets. R2 is a reference, not a competitor.

| | A | B | C | G1 | R2 (outer, protocol 1.1) |
| --- | --- | --- | --- | --- | --- |
| Evidence | dev | dev | dev | dev | registered, descriptive |
| Accuracy | 0.478 | 0.907 | 0.524 | 0.913 | 0.714 |
| Macro-F1 | 0.381 | 0.652 | 0.455 | 0.720 | 0.708 |
| Balanced accuracy | 0.416 | 0.647 | 0.461 | 0.722 | 0.749 |
| Scenario-group-balanced accuracy | 0.468 | 0.880 | 0.488 | 0.902 | 0.692 |
| Worst topology (accuracy) | 0.000 | 0.789 | 0.071 | 0.877 | 0.213 (Center) |
| Worst scenario group | 0.000 | 0.000 | 0.000 | 0.003 | 0.667 |
| ECE / Brier | 0.465 / 0.953 | 0.086 / 0.163 | 0.411 / 0.877 | 0.046 / 0.157 | 0.231 / 0.442 |
| Errors with conf ≥ 0.9 (share of errors / rate among confident) | 0.696 / 0.544 | 0.000 / 0.000 | 0.799 / 0.615 | 0.612 / 0.068 | 0.373 / 0.148 |
| Flag-free share | 0.213 | 0.136 | 0.267 | 0.244 | 0.572 |
| s_C coverage / group risk / wrong SPECIFIC / inclusion | 0.50 / 0.000 / 0 / 1.0 (1 topology) | not estimable | 0.60 / 0.045 / 511 / 1.0 | 0.60 / 0.091 / 963 / 1.0 | RQ1 not estimable |
| D(x) increment (group risk) | 0 | not estimable | 0 | 0 | not estimable |

## 7. Release candidate RC1

**Identity:**

- file: `06_audit_preparation/protocol2/release_candidate/P2_0_RC1.yaml`;
- sha256 in `P2_0_RC1.sha256`;
- status `RELEASE_CANDIDATE_P2_0_RC1_NOT_APPROVED`;
- confirmatory execution **BLOCKED**. The runner refuses the status even with a well-formed authorization, which is tested.

**Components** (`RC1_COMPONENTS.csv`):

| Component | Decision |
| --- | --- |
| B source-model topology | included, conditional on D1 = B |
| C name-matched 13 | **excluded** (refuted by D2) |
| C′ position-matched 12 (map v0.1, pinned by hash, fail-closed `h2prism.position_map`) | included, conditional on D2 acceptance **and** development arm H |
| D independence-group support | included (integrity rule) |
| E evidence conflict | optional, default off |
| F E_h | excluded; code and tests retained |
| D(x) | comparator; semantics written into the config |
| Calibration | development-only, fallback none |
| Targets | development-only rule |
| Meta-model | fail-closed |
| Inference unit | independence group (new runner option `evaluation.uncertainty.unit`) |
| Registered contrast | s_C vs s_C−D |
| Cross-topology comparability | not claimed |

**Arm H_POSITION_MATCHED:**

- config: G1 with the position map;
- registered with a prespecified criterion (`arms/H_POSITION_MATCHED.yaml`, `ABLATION_MATRIX_ADDENDUM_H.csv`);
- **not authorized and not run**: it needs a `DEVELOPMENT_EXPERIMENT:H_POSITION_MATCHED` grant from the project lead.

**Approvals still required before freeze:**

- D1 and D2 (Yazan);
- component decisions and the D4 inference unit (Faisal);
- arm H authorization (project lead), then its review;
- D6 data (Yazan or the authors).

## 8. Decision record (one blocker, one accepting authority each)

| Item | Single blocker | Accepting authority |
| --- | --- | --- |
| D1 attribution | dataset-owner decision (option B recommended) | Yazan |
| D2 position map v0.1 | acceptance of the diagram trace | Yazan |
| C′ in RC1 | development arm H results | project lead (authorize), Faisal (review) |
| B, D, CAL, TGT, META, UNIT in RC1 | named component acceptance | Faisal |
| E optional | design choice | Faisal |
| F, C exclusion | none (recorded) | — |
| Confirmatory run | D6 data for all four classes (scenario definitions missing for G4–G6, faults and delays) | Yazan / dataset authors |
| Team-plan matrix: 20 items not COMPLETE | per row: `single_blocker` and `accepting_authority` columns in `TEAM_PLAN_COMPLETION_MATRIX.csv` | as listed |

**Not fully resolved:**

- D2 is technically resolved from the diagrams, but not accepted.
- The B vs G1 conflict is explained, but undecidable on current data.
- RC1 is blocked for confirmation.
