# Independent multiclass simulation program, Distinguishability v2 support, and generalization plan

**Status:** DESIGN ONLY.

- Applies to the validated **H2Net v1** model family (`HYDROGEN_MODEL_SPECIFICATION.md`). No generation is authorized.
- It is **not** covered by the v3 NORMAL request, which stays unauthorized.
- The released simulator remains a secondary benchmark.

## 1. Independence rules (fixed before generation)

1. **One independence group = one physical parameter set.**
   - The same set simulated in several topology configurations is one group.
   - Noise seeds, re-windowing, re-export and relabelling never create groups.
2. **Inference unit: the independence group.** Windows are never independent observations.
3. **Partitions are assigned from design codes only, before any simulation.** The rule is deterministic and label-free (as in package v2/v3).
   - The confirmation set is hashed at creation and never opened before a frozen protocol and a separate authorization.
4. **Each run is paired with a matched no-event counterfactual:** same model, parameters and seed, event off. The pair belongs to the same group as its event run.

## 2. Classes and factors

Operating-point factors (all classes):

| Factor | Levels |
| --- | --- |
| Supply pressure | 3 levels within the V8 envelope |
| Demand profile | constant / daily cycle / step changes |
| Ground temperature | 2 levels |
| Topology configuration | center / down / up (verified position-matched sensors) |

**Event mechanisms,** each defined physically (H2Net v1 S3–S4) and never on the demand blocks:

| Class | Mechanism | Severity or type | Timing |
| --- | --- | --- | --- |
| LEAK | separate orifice branch at **mid-pipe positions** (≥ 4 positions in development; **≥ 2 unseen positions held out**) | **weak / medium / strong**, defined *before generation* as leak flow = 0.5% / 2% / 10% of local throughput. Detectability is measured, not assumed. | persistent (step), ramped onset, **transient** (opens then closes); ≥ 3 onset times |
| COMPRESSOR_FAULT | reduced pressure rise (−10 / −25 / −50%) or trip | 3 severities plus trip | ≥ 3 onset times |
| COMPRESSOR_DELAY | delayed start of a compressor station | 60 / 180 / 300 / 600 s | from start-up |
| NORMAL | none | — | operating-point factorial only |

**Minimum groups** (each group simulated in all three configurations):

| Class | Development | Confirmation | Notes |
| --- | --- | --- | --- |
| NORMAL | ≥ 6 | ≥ 4 | operating-point fraction covering every factor level |
| LEAK | ≥ 24 (4 positions × 3 severities × 2 temporal types) | ≥ 8, including the 2 unseen positions and every severity | transient cases are their own groups |
| COMPRESSOR_FAULT | ≥ 6 | ≥ 4 | both compressor stations |
| COMPRESSOR_DELAY | ≥ 6 | ≥ 4 | |

**Per-run acceptance:**
- the physical checks of package v3 (P1–P6), re-derived from validated H2Net v1 NORMAL runs;
- validation envelope V8;
- the event visibility of each event run, measured against its counterfactual and recorded. Low-visibility events are **kept and labelled as such**, not silently dropped.

**Provenance per run:**
- model file hash and version;
- every changed parameter, by block SID;
- solver and step;
- noise σ and seed;
- logged block identities;
- group ID and partition;
- counterfactual pairing;
- authorization scope and attempt ID (atomic claim, as in package v3).

## 3. Distinguishability v2: minimum support for estimability

v2 settings (`02_methodology/DISTINGUISHABILITY_V2.md`): m = 2, τ = 1. Groups replicate across configurations, and the query's own group is always removed from the reference.

| Quantity | Requirement | Program above |
| --- | --- | --- |
| Separability between two classes | ≥ m + 1 = **3** development groups per class | met (≥ 6 per class) |
| Detectability against NORMAL | ≥ m + 2 = **4** NORMAL development groups | met (6) |
| Out of support | ≥ 2 groups in the reference | met |
| Matched-coverage comparison estimable | every arm reaches the development-fixed coverage on development data | to be checked on development data only |
| Group-level inference on confirmation | ≥ 4 groups per class; ≥ 20 in total | met (≥ 20) |

**The comparison set is preserved:**
- (1) confidence-only abstention;
- (2) confidence with support safeguards;
- (3) original D(x) in s_C, plus s_C−D;
- (4) Distinguishability v2.

**Primary question:** is the scenario-balanced selective diagnostic risk at matched SPECIFIC coverage of (4) lower than that of (1)? The single confirmatory contrast is E vs A in the v2 matrix, using an independence-group bootstrap. **No improvement is presumed;** a null or not-estimable result is reported as such.

A power statement is deferred until development data give the between-group variance. If the confirmation partition cannot detect a prespecified minimum effect, more groups are generated **before** confirmation is opened.

## 4. Generalization tests (separate, each with its own held-out unit)

| Test | Held-out unit | Data source |
| --- | --- | --- |
| G1 unseen scenarios | new groups, same factor levels | confirmation partition |
| G2 unseen operating conditions | a held-out factor level (e.g. the highest supply pressure, a new demand profile) | a dedicated held-out set |
| G3 unseen topology configuration | leave-one-configuration-out (center / down / up) | all |
| G4 new network structure | a **fourth network with a different graph** (new model, own validation V1–V8) | not yet existing: required before any cross-network claim |
| G5 sensor availability | prespecified sensor-dropout and sensor-subset scenarios at inference (no retraining) | development and confirmation |
| G6 hypothesis and reference scaling | 2 → 4 → more classes; reference groups subsampled | development |

**No claim of industrial readiness or cross-network generalization** is made from the released three-model benchmark, or from H2Net v1 without G4.

## 5. Computational scalability (measured on synthetic data; `03_results/diagnostics/distinguishability_v2/SCALABILITY_SYNTHETIC.csv`)

**v2 at 96 features:**

| Reference size | Fit time |
| --- | --- |
| 1,440 windows | 0.3 s |
| 5,760 windows | 3.7 s |

- **Fit:** grows as about N_ref^1.7, from the leave-one-group-out calibration over the whole reference.
- **Per query:** about 1 ms, nearly flat over the measured range.
- **Memory:** peak ≤ 16 MB.
- **Hypotheses:** query time grows about linearly with the number of classes (n_classes^0.55 over 2–8).

**Projection:** a reference of 30,000 windows fits in about a minute. This is acceptable offline. For larger references, the leave-one-group-out step is the part to optimise (e.g. by sampling within groups); any such change needs its own equivalence test. Runtime on real H2Net data is re-measured in development.

## 6. Order of work

1. **Approval to install a pinned CoolProp.** Then V1 tables and reference steady states (no MATLAB).
2. **`MODEL_DEVELOPMENT:H2NET_V1_PROPERTIES_AND_STEADY_STATE`** (MATLAB): build H2Net v1 and pass V1–V8.
3. **Fix the multiclass design files and the partition rule from validated parameters.** Then a separate generation authorization per stage: NORMAL first, then each event class, each with an atomic one-attempt claim.
4. **Development analyses** (v2 estimability, matrix arms) under a frozen development protocol.
5. **The confirmation run.** It needs a frozen protocol and a new authorization.
