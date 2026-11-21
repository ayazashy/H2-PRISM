# 03 — Scientific findings catalog

**What this covers.** Every value below is taken from a verified repository output. The source is cited in brackets; nothing was recomputed or created for this inventory.

**Path abbreviations.**
- `v1` = `03_results/integrated_validation_v1`
- `v2` = `03_results/integrated_validation_v2`
- `CE` = `03_results/validation/center_evidence_enhancement`
- `ATL` = `03_results/validation/publication_final_v1`
- `HY` = `03_results/hy2res_external_validation`
- `MHC` = `study_b`

**Category labels (the brief's A–F).**
- **A** Formally verified property
- **B** Model-conditional engineering result
- **C** Exploratory diagnostic result
- **D** Reproducibility or computational measurement
- **E** Negative finding or demonstrated limitation
- **F** Unsupported or blocked claim

## Evidence sources and independent units

| Source | What it is | Independent units | Ground truth | Status |
|---|---|---|---|---|
| R2 (H2-SimNet) | Registered 3-fold held-out-topology classification of 27,993 windows | 17 scenario ancestors (templates), 39 families, 51 scored runs; windows are dependent | Labels disputed in 36/57 runs (D1 NOT_RECORDED) | Registered RQ1 NOT_ESTIMABLE; everything else exploratory |
| Center | 12 controlled Simscape captures (6 matched pairs), 13 sensors, 0.2 s clock | 1 source family; 0 independent generating families; 6 mechanism queries, each a single capture | Configured interventions (known) | Descriptive; D(Y) under hypothetical bounds |
| HY2RES | One residential pilot, 27 Mar–15 Apr 2024, 5 s clock | 1 pilot; 414 test segments; test period previously inspected | Power-defined operating state only; no fault labels | Descriptive reference prediction |
| MHC | Experimental hydrogen compressor release, 8 dual-stage runs | 3 held-out runs | No fault or location labels | Descriptive reference prediction |
| Synthetic (v2) | Seeded designs (D(x) method check; D(Y) sensor faults) | n/a | Known by construction | Method checks only |

## A. Formally verified properties

1. **Monotone, certificate-carrying formal D(Y).**
   - Result: 0 forbidden status transitions in 25,024 hypothesis-status checks over 4,032 paired decisions. All 11,061/11,061 exclusion certificates and 1,552/1,552 feasibility witnesses were independently re-verified in exact rationals [v1 advanced_validation/tables/A04a.csv; figure AV-F05].
   - Proof: assumptions A1–A5 in [v2 02_design/DY_MONOTONICITY_PROOF.md]. 44 adversarial and property tests pass [tests/test_dy_adversarial.py].
   - Scope: an implementation and mathematical property under a fixed hypothesis library and closed intervals. It is not diagnostic validity.
2. **Closed-form agreement.** The engine agreed with the closed-form exclusion onsets in 3,584/3,584 checks, and the observation/model bound split never changed a decision [CE CENTER_ENHANCEMENT_RESULTS.md §3.5].
3. **Exact reproduction of frozen inputs.**
   - R2 frozen predictions, decisions and config hashes match.
   - The 12 Center captures are re-hashed on every load.
   - HY2RES MD5 matches.
   - HY2RES archived metrics reconcile 60/60; the frozen decision rule reproduces 7/7 counts.
   - The MHC benchmark replays bit-identically.
   - Sources: [v2 01_audit/BASELINE_REPRODUCTION.csv; HY HY2RES_ENHANCEMENT_RESULTS.md §3.1; MHC MHC_ENHANCEMENT_RESULTS.md §3.2].

## B. Model-conditional engineering results

All results in this section carry CONDITIONAL_HYPOTHETICAL_BOUNDS, on Center captures only.

1. **Three D(Y) evidence situations** [CE TAB_C06; Q1_C15]. The three conditions are not comparable rates.

   | Evidence condition | SPECIFIC correct | SPECIFIC wrong | AMBIGUOUS | UNRESOLVED |
   |---|---|---|---|---|
   | Frozen formal result | 0 | 0 | 0 | 12/12 (INVALID_UNCERTAINTY; no adapters) |
   | Full declared universe | 0 | 0 | 0 | 42/42 (INDETERMINATE_HYPOTHESES; 3 declared hypotheses lack adapters) |
   | Restricted supported universe (all sensors, ±1 s, 42 cells = 6 queries × 7 scenarios) | 8 | 2 | 4 | 28 (MODEL_MISMATCH) |

2. **Where the decisions fall.**
   - All 8 correct SPECIFIC are the two near-duplicate SID 213 queries.
   - Both wrong SPECIFIC are SID 215 → "Normal" at S5 and REF [Q1_C14].
3. **Pairwise isolability: a template property, not accuracy.**
   - At REF bounds, 14/15 hypothesis pairs are separable with all 13 channels, 9/15 pressure-only and 14/15 flow-only [AV-F07; v2 V2-T04].
   - Normal vs SID 215 is bound-limited, not intrinsic: λ* = 0.080 × REF ≈ 2.76e-3 MPa / 1.46e-3 kg/s [V2-F03].
   - The SID 215 template exceeds 2 ε_REF on 0 of 13 channels; its largest ratio is 0.081, on PS4 [V2-F04].
   - Minimum sensor set at REF: MFS1 + MFS3 [A16b].
4. **Sensor observability.** Each outlet excites a different instrument [CE §3.4; Q1_C01, Q1_C11]:
   - SID 213 moves MFS3 by 0.691 kg/s;
   - SID 312 moves MFS1 by 0.647 kg/s;
   - SID 215 moves no flow meter by more than 3.9e-4 kg/s;
   - SID 215 appears as 5.6 kPa at PS4/PS8.
5. **Sensor masks (24 decisions per configuration)** [A08; AV-F08].

   | Configuration | Correct / wrong SPECIFIC |
   |---|---|
   | All 13 channels | 8 / 2 |
   | Flow only | 8 / 4 |
   | Pressure only | 2 / 0 |
   | Without MFS1 | 8 / 0, plus 4 ambiguous |
   | Without MFS3 | 2 / 0, plus 8 ambiguous |

6. **Timing** [A09; AV-F09].
   - Widening the clock bound from 0 to 10 s changes nothing.
   - A delay of 2 s or more beyond τ = 1 s gives 0 correct and 2 wrong SPECIFIC; the rest are UNRESOLVED.
7. **SYNTHETIC sensor faults** [V2-T03; V2-F02]: 408 decisions, 33 fault settings.
   - No setting exceeded the baseline count of wrong SPECIFIC decisions.
   - At 2 ε_obs bias or drift, wrong-specific risk rises from 0.200 to 0.333, because correct decisions are lost first.
   - At 10 ε_obs every decision is UNRESOLVED.
   - ±1-sample jitter leaves every outcome unchanged.
8. **Exclusion onsets** [CE TAB_C05; Q1_C13a/b].
   - The SID 213 correct-SPECIFIC window spans ×210 in pressure and ×1,011 in flow.
   - At REF, pressure exclusion of every withdrawal rival is lost; flow exclusion of SID 213's rivals survives.

## C. Exploratory diagnostic results

1. **R2 classification** [V2-T08, V2-T09; Q1_I05].
   - Window accuracy 0.714 on all 27,993 windows (balanced accuracy 0.749, macro-F1 0.708).
   - Window accuracy 0.938 on the 19 undisputed runs (10,661 windows).
   - Run-level majority accuracy: 0.947 undisputed vs 0.562 disputed.
   - By held-out topology: Center 0.213, Downstream 0.929, Upstream 1.000.
2. **Selective risk at shared coverage 0.25** [H1-F02a/b; AV-F01/F02].

   | Policy | Wrong-specific risk |
   |---|---|
   | s_C | 0.146 (1,019 / 6,999) |
   | s_C − D | 0.152 |
   | Confidence + evidence guard | 0.238 |
   | Conventional confidence | 0.422 |
   | No abstention (coverage 1.0) | 0.286 |

   - The s_C vs s_C−D interval includes 0 (ancestor [−0.044, 0.023]).
   - All 1,019 s_C errors are in disputed runs.
3. **Registered three-outcome policy (RQ3)** [Q1_I08; T09b].
   - At coverage 0.60, pooled over the Downstream and Upstream folds (Center excluded: 0.60 unattainable): 0 of 11,198 SPECIFIC decisions wrong.
   - All 31 ambiguity sets contain the true class.
   - Compressor-fault windows are never decided.
4. **Negative control** [A11a; AV-F11].
   - The R2 NORMAL windows (1,995 windows, one scenario template) received 0 false LEAK calls from s_C at 0.10 and 0.25.
   - Conventional confidence produced 655 false LEAK calls among 680 SPECIFIC.
5. **Center mechanism recognition** [CE §3.2; Q1_C07, Q1_C08].
   - The frozen library recognises 7/7 queries by self-template or near-duplicate.
   - With the own template excluded, 3/5 supported queries; 2 of those 3 rest on near-duplicates and the third is a 1.9e-5 near tie.
   - The timing query is routed to a withdrawal (open-set failure).
6. **Center categorical localization** [CE §3.3; A06a/A07; Q1_C09; AV-F06].
   - Top-1 correct for 2/2 supported queries, but this is a single outlet (SID 213) with near-duplicate captures.
   - Localization Level 2 for one outlet only; Levels 3–5 not demonstrated.
7. **Center archive replay** [ATL ATLAS.md; Q1_C04–C06].
   - The constant "LEAK" rule recalls 39/39 held-out scenarios and ties XGBoost.
   - The clean 1 s EWMA detected 39/48 events with 42 false starts over 65.63 inactive hours.
   - A 1 s command shift produced a 228× clock-vs-event residual RMS contrast.
8. **HY2RES** [HY STUDY_C_FINAL_RESULTS.md; Q1_H05–H13].
   - Persistence vs Ridge: tank-pressure RMSE −19.6% for Ridge, MAE −1.8%; electrolyzer-flow MAE +443.9% for Ridge.
   - All differences are a fraction of one 0.1-bar recording step [Q1_I02].
   - The frozen state rule abstains on 32,308/44,397 test rows. Tank pressure is out of development support on 31,589 rows (71.2%), and abstention tracks support over time [Q1_H10, H11].
   - The rule makes 0 specific calls on the minority compressor state (0/817).
9. **MHC** [MHC RESULTS.md; Q1_B05–B12].
   - Persistence gives lower MAE on every held-out run: run-mean P-2 MAE +9.2% for Ridge, MFC-3 +34.0%.
   - Ridge RMSE gains are tiny: −0.53% for P-2 and −0.08% for MFC-3.

## D. Reproducibility and computational measurements

1. **Runtime** [A14a/A14b; AV-F12].
   - Formal D(Y) decision: 0.36 s median for 13 channels and 6 hypotheses (Ryzen 5 7520U, single process).
   - Log–log slopes ≈ 1 in channels (1.02), hypotheses (0.98) and window samples (1.06); flat in clock shifts (0.00).
   - D(x): slope 0.70 in reference windows (synthetic arrays).
2. **Package reproducibility.**
   - v2 re-run is byte-identical (88/88 outputs).
   - Verifiers: v2 35/35, v1 advanced validation 57/57, v1 publication 275/275.
   - Full test suite: 774 passed, 2 documented failures, 0 collection errors [03_results/maintenance/MAINTENANCE_CLOSURE_REPORT.md].

## E. Negative findings and demonstrated limitations

1. **D(x) adds no demonstrated value** [V2-T01; V2-F01].
   - Adding D worsens out-of-template log-loss: confidence 0.906 → 0.995; full model 0.693 → 0.828; worse in 10/16 held-out templates.
   - In Center, D separates disputed-attribution windows (AUROC of 1−D = 0.084, i.e. 0.916 separation) better than errors (0.393).
   - Synthetic check: D helps only when the classifier is blind to an informative feature.
2. **Registered H1 is NOT_ESTIMABLE**: 12/12 PRIMARY rows, 60/60 including secondary comparators. Maximum shared coverage is 0.258, below every registered target of 0.60/0.80/0.90 [H1-F01; H1-T02].
3. **Library incompleteness yields false certainty (H9 CONTRADICTED).** With the true hypothesis removed: 2 wrong SPECIFIC decisions, 4 ambiguous sets without the truth, 36 MODEL_MISMATCH of 42 [A05; AV-F04; H1-F06].
4. **Label defect dominates R2.**
   - 7,347 of 8,012 classifier errors are in disputed runs [AV-F02/F03].
   - All 13 event runs misclassified as NORMAL are disputed [V2-T09].
5. **HY2RES certified port.** The port reproduces the frozen rule exactly, yet 0 of 10,762 singleton calls survive certification: the rival state is never single-coordinate-excluded. Ambiguous decisions are preserved 1,327 = 1,327 [V2-T06; V2-F05].
6. **Traceability gap (H10 CONTRADICTED).** Required fields: 12/16 in the engine certificate, but only 7/16 in the frozen serialized record [A18].
7. **Center open-set failure.** The timing query is routed to a withdrawal when its own template is absent [Q1_C07].
8. **Flow-only sensing** doubles wrong SPECIFIC decisions (4 vs 2); moderate synthetic faults raise selective risk [AV-F08; V2-F02].

## F. Unsupported or blocked claims

| Claim | Status | Why |
|---|---|---|
| Out-of-template / out-of-domain diagnostic generalization (H6) | BLOCKED_BY_DATA | 17/17 test templates occur in training; no labelled external faults |
| Hydrogen or H2/NG-blend diagnostic transfer (H7) | BLOCKED_BY_PHYSICS | Center gas is air-like (R = 0.287 kJ/(kg·K), γ = 5.75); no transient H2 model [A13; AV-F14] |
| Corrected-attribution replication | BLOCKED_BY_PROVENANCE | D1 not recorded |
| Network-wide or distance localization | NOT DEMONSTRATED | One independent outlet; no geometry |
| Monetary sensor savings (H8) | NOT AVAILABLE | No prices; relative scenarios only [V2-T07, V2-T10] |
| Field-validated safety guarantee from D(Y) | NOT SUPPORTED | All bounds hypothetical [v2 01_audit/BOUND_ORIGIN_AUDIT.csv] |

## Cross-version changes and conflicts (reported, not resolved)

| Topic | Earlier version | Later version | Resolution |
|---|---|---|---|
| Center formal decisions | ATL FIG_08 / TAB_13: 12/12 UNRESOLVED | CE TAB_C06: 8/2/4/28 (restricted, conditional) | Different evidence conditions; both true; Q1_C15 shows both |
| Center D(Y) counts | Q1_I01 schematic: "48 correct, 11 wrong SPECIFIC (restricted)" (pooled over sensor groups and clock bounds) | All-sensor ±1 s: 8 correct / 2 wrong | Different denominators; cite with denominator |
| Engine portability | AV-F15 / A12: "formal engine runs only on Center" | V2-F05: HY2RES rule run through the engine (Level A, zero bounds) | Later result adds Level-A portability; Level C still absent |
| Library incompleteness | AV-F16, H1-F07: "D(Y) refuses with incomplete declared library" (conditional) | v2 registry H9 CONTRADICTED | Refusal holds for unmodelled declared rivals; removing the truth gives wrong SPECIFIC |
| Normal vs SID 215 onset | CE TAB_C05: flow onset 3.85e-4 kg/s (observation vs template, single sensor kind) | V2-T04: λ* = 0.080 × REF (template vs template, joint scaling) | Different quantities; do not equate |
| R2 figure-system figures | 4 run-key variants (a10530f1fcf2, _s4228b6c8, _b5ddfbcfa, _b200fcdac) | Only `_b200fcdac/final` is approved (PUBLICATION_MANIFEST) | Others superseded |
| Dataset design figure | `preliminary/` and `superseded_unapproved_final_20261111/` | — | Superseded manifest references a moved `final/` path (3 missing references) |
