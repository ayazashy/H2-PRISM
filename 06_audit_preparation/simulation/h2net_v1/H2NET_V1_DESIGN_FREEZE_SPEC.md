# H2Net v1 — design-freeze specification (decision-ready)

**Status: PROPOSED FOR FREEZE. Not approved.**
- 2026-11-14, coordinated by Ahmed. `PARAMETER_DECISIONS.yaml` is unchanged.
- No MATLAB run, simulation, dataset or training.

Figures come from the independent Python steady-state reference:
- `tools/simulation/h2net_v1_design_freeze_calcs.py` → `candidate/DESIGN_FREEZE_CALCS.json` (PROVISIONAL);
- the same solver and hydrogen tables as `PROVISIONAL_STEADY_STATES.json`.

Builds on `H2NET_V1_APPROVAL_CHECKLIST.md` (D1–D7).

---

## 1. D1 + D7 evaluated jointly (supply 3.2 MPa; C1 → 5.0 MPa; C2 → 6.5 MPa)

### 1.1 Operating point (identical across the center, up and down models; down model let-down to 4.0 MPa)

| Quantity | C1 (sid 55) | C2 (sid 239) |
|---|---|---|
| Suction → discharge | 3.200 → 5.000 MPa (Δp 1.800) | 4.986 → 6.500 MPa (Δp 1.514) |
| Mass flow | 20.0 kg/s | 16.0 kg/s |
| Real-gas isentropic discharge / power | 356.6 K / 12.8 MW | 337.6 K / 5.8 MW |
| At η = 0.75: discharge / shaft power / aftercooler duty | 371.2 K / 17.0 MW / 16.9 MW | 346.0 K / 7.75 MW / 7.6 MW |

**Network**
- Pipes 4.986–6.500 MPa (down model ≥ 3.996 MPa); outlet velocity ≤ 5.3 m/s.
- Mass conservation exact; feasible at load ×0.5 and ×1.5 (v ≤ 7.9 m/s).

**Compared with the single-stage proposal (3.0 → 6.5 MPa):**
- total isentropic power 18.6 MW instead of 22.8 MW;
- maximum discharge 371 K instead of 416 K at η = 0.75;
- both machines now carry real load.

### 1.2 Fault states (Simscape Pressure Source (G) imposes Δp, so faults scale Δp)

| Fault | Min. pipe pressure | Max. node change vs NORMAL | Inside proposed fault envelope (≥ 2.5 MPa) |
|---|---|---|---|
| C1 trip (Δp = 0) | 3.178 MPa | −1.81 MPa | yes |
| C1 at 50 % Δp | 4.083 MPa | −0.90 MPa | yes |
| C2 trip | 4.970 MPa | −1.52 MPa | yes |
| C2 at 50 % Δp | 4.986 MPa | −0.76 MPa | yes |

**Verdict:** D1 + D7 is feasible, cooler and lower in power, and makes both compressor-fault families and the C2-based DELAY observable.
- **Recommend APPROVE** (Yazan + modeller).
- Open: the compressor efficiency used for power reporting (SOURCE); the cooler sizing (V3, MATLAB).

## 2. Sensor placement for mass-flow balance

### 2.1 Required sensors

Port names refer to the Simscape blocks. All new sensors log by block identity.

| Id | Type | Exact placement | Topologies | Status |
|---|---|---|---|---|
| `MFS0` | Flow Rate Sensor (G) | in series between the C1 aftercooler outlet and Pipe (G)1 port A | all | **new** |
| `MFS2s` | Flow Rate Sensor (G) | in series at Pipe (G)4 port A (flow into CV_B; excludes the chamber) | all | **new** |
| `MFS5` | Flow Rate Sensor (G) | in series on the G4 demand branch (sink SID 222 replacement) | all | **new** |
| `MFS6` | Flow Rate Sensor (G) | in series on the G6 demand branch (sink SID 215 replacement) | all | **new** |
| `MFS7` | Flow Rate Sensor (G) | in series on the END sink branch | center, up | **new** (down: existing `MFS4`, SID 196) |
| `MFS3`, `MFS1` | existing | G3 (SID 218) and G5 (SID 311) branches | all | keep |
| `PS_N6` | Pressure & Temperature Sensor (G) | node N6 (Pipe (G)3 / (G)8 junction, G5 node) | center, down | **new** (up: N6 ≈ N9 via the open restriction, covered by existing PS SID 418) |
| `PS_END` | Pressure & Temperature Sensor (G) | Pipe (G)5 port B (end node) | center, up | **new** (down: existing SID 134) |
| `MFS2` | existing (dead-end chamber) | unchanged | all | keep as `MFS2_chamber` (comparability only) or drop: **owner** |

### 2.2 Control volumes and balance equation

- **CV_A** (center and down): Pipe (G)1, 2, 3, 8, plus C2 and its aftercooler. Up model: additionally Pipe (G)5.
  - In: MFS0. Out: MFS3, MFS1, MFS2s (up: + MFS7).
  - Leak positions 47, 48, 49, 309 lie in CV_A.
- **CV_B** (center): Pipe (G)4, 7, 5. Down: Pipe (G)4, 7, 6. Up: Pipe (G)4, 7.
  - In: MFS2s. Out: MFS5, MFS6, and the END meter (center MFS7, down MFS4).
  - Leak positions 106, 221 lie in CV_B.
- Residual: **r(t) = Σ ṁ_in − Σ ṁ_out − dM/dt**, with the line-pack term M = Σ_pipes A·L·ρ(p̄, T).
  - dM/dt is estimated from the pressure rates at the pipe ends.
  - Every pipe end in both CVs is now pressure-instrumented.

### 2.3 Line-pack magnitude (hydrogen density tables, nominal pressures)

| CV | dM/dp | dp/dt resolution needed for a 0.1 kg/s residual error |
|---|---|---|
| CV_A | 56 kg/kPa (hydrogen inventory ≈ 316 t at about 5–6.5 MPa) | **1.8 Pa/s** |
| CV_B | 7 kg/kPa (≈ 47 t) | 14 Pa/s |

A NORMAL load step that moves CV_A pressures by 10 kPa over 10 min shifts line-pack by about 560 kg. That is an apparent imbalance of about 0.9 kg/s, more than a 2 % leak (0.4 kg/s).

**Requirements:**
1. Line-pack correction is mandatory in every balance feature and label check.
2. Detection windows must be long enough that the window-averaged pressure-rate noise is ≤ 1.8 Pa/s in CV_A. The noise model decides the window length (SOURCE).
3. NORMAL scenarios must include load transients of the same kind, so that transient imbalance is never a LEAK shortcut (§3).

## 3. Scenario design without operating-condition shortcuts

### 3.1 Operating conditions (OC)

One OC is a full specification of the normal operation. All factors are drawn independently of class:

| Factor | Levels (proposed) |
|---|---|
| Topology | center, up, down |
| Demand level | nominal × {0.6, 0.8, 1.0, 1.2, 1.4} (all feasible per §1) |
| Demand allocation | nominal shares; or ±25 % reallocation between G3/G5 and G4/G6 |
| Load profile | step (±20 %), ramp (±20 % over 10 min), diurnal-like sinusoid (±15 %, 30 min period), constant |
| C2 set-point | 6.3 / 6.5 / 6.7 MPa |
| T_ref | 313.15 K (fixed in v1) |
| Seeds | load-profile seed and noise seed per OC |

### 3.2 Matched design (counterfactual siblings)

For every OC, generate the sibling set below. Every sibling shares the OC, the seeds, the run duration, the sampling and the noise.

| Class | Sibling runs per OC | Event definition |
|---|---|---|
| NORMAL | 1 | no event; same load profile |
| LEAK | 6 positions × 3 sizes = 18 (or a balanced rotation: 6 per OC, 2 per size) | Local Restriction (G) area from 0 to the class area with a 10 s ramp at onset t₀ |
| COMPRESSOR_FAULT | 4 | C1 trip, C1 50 %, C2 trip, C2 50 %; Δp change with a 10 s ramp at t₀ |
| DELAY | 3 | the C2 set-point response to the OC's load change starts τ ∈ {60, 120, 240 s} late. The NORMAL sibling responds at τ = 0. |

**Shortcut controls (all required):**
1. **Onset time.** t₀ is drawn from the same uniform window for every class. NORMAL runs carry a pseudo-onset t₀ from the same draw for windowing symmetry.
2. **Pre-onset equality.** Siblings are bitwise identical before t₀ (same seeds). This is checked automatically.
3. **Equal marginals.** The OC-factor distribution is identical across classes by construction. This is checked by exact count tables.
4. **DELAY needs a load change in NORMAL too.** DELAY uses only OCs with a step or ramp load change, and the matched NORMAL sibling contains the same change. Otherwise "a load change is present" would identify DELAY.
5. **Metadata leakage.** No class-dependent run length, file name, sensor set or sampling.
6. **Pre-release probe.** A classifier trained on pre-onset windows alone must score at chance (group-balanced accuracy within the 95 % binomial band of 1/K).

## 4. Detectability and independence requirements (fixed before generation)

### 4.1 Objective detectability

Computed per class, position, size and OC from the X06 steady states plus the MATLAB transients and the decided noise model:
- **SNR_p** = |Δp_event at the best pressure channel| / σ_p, with σ_p the window-averaged noise.
- **SNR_b** = |ṁ_leak| / σ_r, with σ_r = √(Σ σ_ṁ² + (C_CV · σ_ṗ)²) the mass-balance residual noise after line-pack correction.
- **SNR_d** (DELAY) = ∫|p_delay − p_normal| dt / (σ_p · √window).

**Classes:**

| Class | Condition |
|---|---|
| DETECTABLE | max(SNR) ≥ 3 |
| LOW_SIGNATURE | 1 ≤ SNR < 3 |
| SUB_NOISE | SNR < 1 |

**Requirements:**
- 2 % and 10 % leaks, every compressor fault and DELAY τ ≥ 120 s must be DETECTABLE.
- The 0.5 % leak class is kept and labelled with its class (expected LOW_SIGNATURE or SUB_NOISE). It is the test set for INSUFFICIENT_EVIDENCE.
- If a required class is not DETECTABLE, the threshold is not lowered and the event is **not** made detectable artificially:
  - The noise model is fixed from a cited source **before** any SNR is computed, and is never reduced to reach SNR ≥ 3.
  - The only admissible design change is adding physically real instrumentation, at its sourced accuracy.
  - Otherwise the class is reported and labelled LOW_SIGNATURE or SUB_NOISE. That is a valid scientific outcome, and it is exactly what the INSUFFICIENT_EVIDENCE path is for.
  - The "must be DETECTABLE" list is a design target, not a label rule.

**Existing steady-state evidence:**
- Compressor faults: 0.76–1.8 MPa, DETECTABLE under any plausible σ_p.
- Leaks in pressure: 0.06–3.2 kPa, against 26.6 kPa of NORMAL variation. Pressure alone is insufficient, so leak detectability rests on SNR_b. **That is not decidable until the noise model is decided.**

### 4.2 Independence

| Requirement | Value |
|---|---|
| Independence group | one **initial-state family**: all OCs that share a deterministic initial state (topology, demand level, allocation, C2 set-point), with all their siblings. OCs differing only in seeds or profile share their pre-load prefix and are NOT independent. Each run records `ancestry = ["IS:<initial-state hash>", "LP:<load-profile seed>"]`; `data_contracts.check_partition_integrity` rejects any shared ancestor that spans partitions. |
| Groups per topology | ≥ 10 development + ≥ 5 sealed confirmation **initial-state families** (the design offers 5 × 2 × 3 = 30 per topology) |
| Groups per class | ≥ 45 (3 topologies × 15). Group-balanced risk then has a resolution of ≤ 1/45 ≈ 2.2 %, against the saturation at 1/11 seen in arm H. |
| Partitioning | by OC; siblings never split (`data_contracts.check_partition_integrity`) |
| Topology hold-out | leave-one-topology-out remains available because every class exists in every topology |
| Seeds | independent across OCs; shared only inside a sibling set |
| Confirmation partition | sealed at generation (hash list), opened only under a confirmatory authorization |

Indicative size with the balanced 6-leak rotation: per OC, 1 + 6 + 4 + 3 = 14 runs. That is 45 OCs × 14 = 630 runs. Duration and sampling are owner decisions; they set the MATLAB cost, so run on a ≥ 16 GB executor or with MATLAB alone.

## 5. Approval status by evidence

| Item | Existing evidence suffices | Needs MATLAB validation | Needs a cited source | Approver |
|---|---|---|---|---|
| M1 = D1 + D7 set-points | yes | V3 cooler sizing, outlet T | compressor efficiency | Yazan + modeller |
| M2 demand + OC factor levels | yes (feasible ×0.5–1.5) | V8 per run | — | Yazan |
| M3 controlled sinks | yes | V2 | — | Yazan |
| M4 roughness 0.045 mm | yes (sensitivity) | — | roughness value | modeller |
| M5 envelope (NORMAL 3–8 MPa; FAULT/DELAY **minimum** pipe pressure 2.5 MPa, i.e. no pipe may fall below it, and maximum discharge temperature 450 K) | yes | V8 | velocity and temperature limits | Yazan + modeller |
| Sensors §2.1 + MFS2 handling | yes (topology, line-pack) | V2 sensor readings | — | Yazan (+ Faisal) |
| Leak branches, sizes, severity definition A/B | sizes: estimate | V4 final areas | — | Yazan + Faisal |
| Scenario design §3 (onset, siblings, DELAY definition) | yes (design) | transients (MATLAB) | — | Yazan + Faisal |
| Detectability criteria §4.1 and the noise model | criteria: yes | transient SNR | **sensor noise model** | Faisal (+ Yazan) |
| Independence and partition §4.2 | yes | — | — | Faisal |
| Heat transfer (S2), segmentation (S5) | — | V5/V7 | U-value, soil T | modeller (explicit deferral allowed) |
| Numerics (S8) | — | V6 | — | modeller |
| Dataset generation itself | — | all V1–V8 PASS | — | **new scoped authorization** (project lead), after the above |

## 6. Assumptions and unresolved risks

**Assumptions**
- Isothermal steady states after the aftercoolers.
- Compressors as ideal pressure-rise elements (no map).
- The steady-state leak signature is taken at the adjacent node.
- Choked leak flow does not depend on downstream conditions.
- Faults scale Δp.

**Risks**

| Risk | Status |
|---|---|
| R1 | Leak detectability depends entirely on the undecided noise model and on line-pack correction (1.8 Pa/s in CV_A). If σ_ṗ is too large, the 2 % class may be LOW_SIGNATURE: the design must change, not the threshold. |
| R2 | Transient behaviour (wave travel, line-pack dynamics, DELAY signatures) is unverified until MATLAB V5–V7. Steady-state evidence cannot settle it. |
| R3 | MATLAB capacity: about 630 runs on an 8 GB laptop is impractical. A ≥ 16 GB executor is needed (X27). |
| R4 | Adding sensors changes the channel set relative to position map v0.1. Comparability with the released data holds only for the retained channels. |
| R5 | Compressor efficiency and cooler sizing are unvalidated (V3). Temperatures are inside the tables, with margin to 500 K. |
| R6 | The fault envelope (≥ 2.5 MPa, ≤ 450 K) and the 20 m/s limit lack cited sources. |

## 7. Named-owner approvals needed (none recorded)

| Owner | Approves |
|---|---|
| **Yazan + designated modeller** | M1 (D1 + D7), M2 with OC levels, M3, M4, M5 and the fault envelope, sensor set §2.1 (incl. MFS2 handling), leak positions and sizes, DELAY definition, run duration and sampling |
| **Faisal** | detectability criteria and thresholds §4.1, noise-model acceptance, independence and partition rules §4.2, shortcut controls §3.2, leak severity definition and labels, V4 rule |
| **Project lead (Ahmed)** | executor designation under the H2Net v1 grant; later, a scoped dataset-generation authorization request (only after V1–V8 PASS) |

**Next valid engineering action:** record these decisions in `PARAMETER_DECISIONS.yaml`. Then regenerate the build spec, compute the X06 targets, and run the memory-compliant MATLAB readiness check.
