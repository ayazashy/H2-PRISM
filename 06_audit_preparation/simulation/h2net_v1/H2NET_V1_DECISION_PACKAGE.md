# H2Net v1 — Engineering decision package

**Status: DRAFT FOR OWNER REVIEW. Not sent, not approved.**
- Prepared 2026-11-14 for Yazan (dataset/model owner) and the designated modeller. Methods review: Faisal.
- Every value here is a **proposal**. Nothing in this document changes `PARAMETER_DECISIONS.yaml`, which stays `status: OWNER_DECISIONS_REQUIRED`, or any authorization record.
- A decision counts only once the owner records it there.

The recommendations are the preparer's advice, for owner consideration:
- **APPROVE**: adopt as proposed.
- **AMEND**: adopt with the stated change, or choose between the stated options.
- **DEFER**: needs a source, a MATLAB result or a scope choice first.

Evidence base (all in the repository):

| Source | What it holds |
|---|---|
| `candidate/SIMSCAPE_SOURCE_EVIDENCE.md` | installed R2026b Simscape source, with SHA-256 |
| `candidate/RELEASED_NETWORK_GRAPH.json`, `RELEASED_PIPES.csv` | read-only parse of the 6 released `.slx` files (hash-checked) |
| `candidate/REFERENCE_CALCS.json` (parts A–G) | hydrogen calculations: CoolProp 7.2.0 tables with the unchanged grant-bound `gas_physics.py` |
| `candidate/ENVELOPE_SCREENING.csv` | 144 states |
| `02_methodology/HYDROGEN_MODEL_SPECIFICATION.md` | S1–S8, V1–V8 |
| `00_governance/ISSUE_CLOSURE_MATRIX.csv` | issue status |

---

## 0. Minimum decisions that unlock the next valid step

The next technically valid step is **X06: compute the V2 steady-state reference targets before any simulation**. It needs no MATLAB. An isothermal steady state needs only these five decisions:

| # | Decision | Table row |
|---|---|---|
| M1 | Operating pressure envelope, supply set-point and compressor Δp | P2, P9 |
| M2 | Nominal demand and its allocation to the outlets | P4 |
| M3 | Demand outlets replace the open vent and the atmospheric orifices (topology of the steady state) | P10 |
| M4 | One roughness value for all pipes | P7 |
| M5 | Reference gas temperature for the isothermal targets | P3 |

Two gates are fail-closed:
- **The X06 tool** (`h2net_v1_envelope_screening.py --targets`) refuses until `PARAMETER_DECISIONS.yaml` is `DECIDED` for **all** items.
- **Model construction (X05)** needs all of S2–S8 decided as well.

So the owners either decide everything at once, or they decide M1–M5 and explicitly record the rest as deferred. Changing the gate's scope is itself an owner decision. It is not made here.

## 1. Decision table

| ID | Parameter | Proposed value (units) | Key basis | Rec. | Owner |
|---|---|---|---|---|---|
| P1 | Gas composition | pure normal hydrogen; real-gas tables T 200–500 K × p 0.05–12 MPa | S1 already decided; V1 PASS; table interface matches Simscape (fact) | APPROVE (confirm) | Yazan |
| P2 | Operating pressure (transmission sections) | **3–8 MPa** (amended from 2–8) | At 2 MPa the 20 m/s capacity of the 1.2 m line is 34.6 kg/s, and every outlet then sits below 2 MPa (calcs F; screening) | AMEND | Yazan + modeller |
| P3 | Gas temperature | 270–330 K in transmission after cooling; isothermal reference at **313.15 K** (aftercooler set-point). Soil 283.15 K. | Compressor discharge 330–431 K without cooling (calcs G) | AMEND (choose the reference T); soil value DEFER (source) | Yazan + modeller |
| P4 | Nominal demand | Total ≤ 50 % of the 20 m/s capacity **at the minimum pressure, in every segment**. At 3 MPa, 313 K: ≤ 25.9 kg/s through the 1.2 m line, ≤ 17.9 kg/s through the 1.0 m pipes, ≤ 2.2 kg/s through the 0.355 m end pipe. | Calcs F. The earlier 42.6 kg/s (defined at 5 MPa) is infeasible at 2 MPa. | AMEND | Yazan |
| P5 | Velocity limit | v ≤ 20 m/s at pipe **outlets** | Velocity grows along each pipe, up to 20.9 m/s for a 20 m/s inlet (screening) | AMEND (apply at outlet); limit source DEFER | modeller |
| P6 | Pipe lengths and diameters | released geometry unchanged: 8 pipes, 3–30 km, D_h 0.355–1.2 m | keeps comparability with the released models; feasibility established under P2/P4 | APPROVE | Yazan |
| P7 | Wall roughness | **0.045 mm** for all pipes (range 0.02–0.1) | Released values 0.0045–50 mm (A-08). Δp sensitivity about ±10 % within the range; 50 mm gives 6× Δp (calcs B). | APPROVE value; source DEFER | modeller |
| P8 | Heat transfer | convective transfer to ground at the soil temperature; replaces the perfect insulators (A-04). U-value per pipe **not yet sourced**. | S2. Steady-state targets are isothermal and do not need U; V3/V8 do. | DEFER (needs a cited U-value) | modeller |
| P9 | Compressors | ideal pressure rise, **power_spec = none**, plus an **explicit aftercooler to 313.15 K**. Supply Δp and mid-line Δp set so every node stays inside P2. Efficiency recorded for the V3 energy balance. | Released `isentropic` with no cooling heats hydrogen to 330–431 K (calcs G; A-05) | APPROVE representation; Δp set-points AMEND (to M1) | Yazan + modeller |
| P10 | Demand outlets | **Controlled mass-flow sinks** at G3–G6 **and at the network end**. Remove the open terminal vent and the four atmospheric demand orifices. | With hydrogen the vent alone passes 3.3–3.5× line capacity; the orifices give pressure-dictated demand (calcs A; A-06) | APPROVE | Yazan |
| P11 | Leak geometry | separate Local Restriction (G) branches to atmosphere at ≥ 6 mid-pipe positions, never on demand blocks; three severity classes | Calcs C and E: the size depends on how severity is defined (see §3) | AMEND (choose severity definition A or B) | Yazan (+ Faisal for labels) |
| P12 | Segmentation and inertia | steady state: one block per pipe is sufficient (fact). Transients: segment length from V5/V7 convergence, starting at ≤ 1 km; inertia on only if wave signatures are in scope. | Lumping error < 10⁻⁵ in steady state (calcs D) | DEFER (MATLAB convergence); scope of inertia: owner | modeller |
| P13 | Initial state | steady state from the reference solver or a converged pre-run; never from atmosphere (A-09) | S6 | APPROVE | modeller |
| P14 | Numerics | ode15s / ode23t, RelTol 1e-6 as validation reference; production solver only if within V6 | S8 | APPROVE as baseline | modeller |
| P15 | Down-model let-down | Pressure Source (G)6 (−1 MPa, isentropic) → pressure-reducing element with power_spec = none, set-point inside P2 | Released isentropic expansion is not a let-down station model | DEFER (owner chooses the representation) | Yazan + modeller |
| P16 | V4 acceptance | Compare Simscape Local Restriction (G) against an implementation of **its own** loss-coefficient equation, plus a model-form comparison with the isentropic orifice equation reported separately | Simscape uses a loss-coefficient, area-ratio and pressure-recovery model, not the nozzle formula (installed `local_restriction.ssc`) | AMEND (methods) | Faisal |
| P17 | Sensors and units | position map v0.1 blocks, MPa absolute, kg/s, log by block identity | S7 already decided | APPROVE (confirm) | Yazan |

## 2. Released-model defects and the proposed remedy

| Defect (fact, with evidence) | Consequence for hydrogen | Proposed remedy | Row |
|---|---|---|---|
| Gas Properties (G): `gas_spec = 1` = perfect gas, R = 0.287 kJ/(kg·K) (air), cp = 0.3469 → γ ≈ 5.75, Pr ≈ 0.079 (all six models) | not hydrogen; thermodynamically impossible constants | real-gas normal-hydrogen tables (interface verified statically) | P1 |
| Open terminal vent: fully open Local Restriction (G)2 → Pipe (G)5 → atmosphere (center and up) | vent flow 3.3–3.5× line capacity; no envelope-compliant steady state exists | controlled end-of-line demand sink | P10 |
| Demands = fixed 1e-3 m² orifices to atmosphere (Cd 0.64) | demand dictated by local pressure (0.8–3.2 kg/s each); demand and leak mechanisms indistinguishable | controlled sinks; leaks as separate branches | P10, P11 |
| Compressors: Pressure Source (G) Δp = 4 MPa, `power_spec = isentropic`, no efficiency or cooling | discharge 330–431 K, above the 330 K envelope at nearly every suction pressure | power_spec none plus aftercooler | P9 |
| Down models: constant −1 MPa isentropic let-down | expansion modelled as a reversed compressor | pressure-reducing element | P15 |
| Roughness 0.0045 / 0.045 / 0.45 / 4.5 / 45 / 50 mm | Δp distorted by up to 6× between otherwise equal pipes | one steel value | P7 |
| Perfect insulators on all pipes and the chamber | adiabatic network; temperatures drift with compression heating | convective transfer to ground | P8 |
| Initial pressure 0.101325 MPa in every pipe | every run starts with a fill transient | steady-state initial state | P13 |
| Lumped 3–30 km pipes, inertia off | steady state accurate (< 10⁻⁵); waves not represented | segment for transients only | P12 |

## 3. Envelope consistency review (calcs E, F, G; not extrapolated from one point)

1. **Capacity (F).** Capacity is proportional to pressure. Any fixed demand that is feasible at 8 MPa can be infeasible at the lowest pressure. Results at 313 K:

   | Pipe | 2 MPa | 3 MPa | 5 MPa | 8 MPa |
   |---|---|---|---|---|
   | 1.2 m | 34.6 | 51.7 | 85.1 | 133.9 kg/s |
   | 1.0 m | 24.0 | 35.9 | 59.1 | 93.0 kg/s |
   | 0.4 m | 3.8 | 5.7 | 9.5 | 14.9 kg/s |
   | 0.355 m | 3.0 | 4.5 | 7.4 | 11.7 kg/s |

   P4 therefore binds the nominal demand to the **lowest** pressure and to **every** segment, not only the trunk.
2. **Leak severity (E).** Choked leak flow is proportional to upstream pressure. Areas sized once at 5 MPa give:
   - **Definition A**, demand scaling with capacity (∝ p): 0.47–0.51 / 1.89–2.02 / 9.4–10.1 % of throughput over 2–8 MPa and 283–313 K. Consistent within ±6 %.
   - **Definition B**, demand **fixed** in kg/s: a nominal "2 %" leak is 0.8 % at 2 MPa and up to 3.3 % at 8 MPa (×0.4 to ×1.67). Not consistent.
   - The owner must choose either:
     - **(A)** severity = fraction of the run's actual local throughput, with the area recomputed per operating point; or
     - **(B)** severity = fixed area, with the actual fraction recorded per run as a label attribute.

   Both are valid; (B) mixes severity with operating point. All leaks are choked at every pressure in the envelope.
3. **Model form.** The leak areas come from the isentropic nozzle formula with local hydrogen γ (1.41–1.43). Simscape's Local Restriction (G) uses a different (loss-coefficient) model. Final areas must be confirmed against the Simscape block (V4, P16) at the decided operating points.
4. **Temperature (G).** Released Δp = 4 MPa with isentropic compression: suction 2 / 3 / 4 / 6 MPa at 313 K gives 431 / 401 / 384 / 364 K. These are inside the property tables (≤ 500 K) but outside 270–330 K, so the aftercooler is necessary. The values are an ideal-gas isentropic estimate with mean local γ; the real-gas path is to be checked in V3.
5. **Pressure drop (B, screening).** The frictional Δp per pipe is 14–85 kPa at 20 m/s and 2 MPa, so leak signatures in pressure are small relative to the operating pressure. This is an input to the sensor-noise budget (spec §5), not a defect.

## 4. Physical validation gates before any generated dataset is scientifically usable

All must pass and be recorded. Thresholds are fixed before running (spec §4); amendments are marked.

| Gate | Content | Status / dependency |
|---|---|---|
| R0 | MATLAB readiness Phases 1, 3, 4 PASS (independent validator), memory gate respected | open: E4 blocks on this laptop |
| V1 | property tables vs reference EOS | **PASS** (recorded) |
| V2 | steady state vs independent solver at ≥ 5 operating points per topology: pressures within 0.5 % of Δp, flows within 1 %. Effective length = L + length_add; Haaland confirmed identical. | targets need M1–M5 (X06); then MATLAB |
| V3 | compressor and aftercooler energy balance; outlet T inside the band | MATLAB; needs P8/P9 |
| V4 | Local Restriction (G) flows vs its own documented equation (≤ 1 %), plus model-form comparison with the nozzle formula reported | MATLAB; P16 amendment |
| V5 | spatial convergence (< 1 % change on halving) for the transient outputs | MATLAB; P12 |
| V6 | numerical convergence (< 0.5 %) | MATLAB |
| V7 | wave arrival L/c and line-pack mass balance (< 0.1 %) if inertia is on | MATLAB; P12 scope |
| V8 | every run inside the envelope: P2 pressures, v ≤ 20 m/s at outlets, P3 temperatures, choking only at orifices | per generated run |
| D1 | parameter diff of each H2Net copy against the released SIDs; released files' hashes unchanged | at build (X05) |
| D2 | leak labels carry the chosen severity definition and the actual per-run fraction (§3.2) | design files (X11) |

## 5. Classification of the content

| Category | Items |
|---|---|
| **Evidence-backed facts** | released gas = perfect air-like; Pipe (G) friction = Haaland, identical to the reference; real-gas table interface and units match; released topology (vent, orifices, isentropic compressors, roughness, insulators, atmospheric initial state); hydrogen calcs A–G under their stated approximations; V1 PASS; source-model hashes unchanged |
| **Engineering proposals** | P2–P16 values and representations |
| **Owner decisions** | everything in §1 marked Yazan / modeller / Faisal; leak severity definition; inertia scope; whether X06 may run on M1–M5 alone |
| **MATLAB-dependent** | R0, V2–V7 runs, final leak areas against the Simscape restriction, transient segmentation, run-time exposure of the real-gas parameters on the released block instance |
| **Unresolved uncertainties** | U-value and soil-temperature sources; velocity-limit and roughness literature sources; real-gas isentropic discharge path; let-down representation; executor designation under the grant; memory sufficiency of the 8 GB laptop for Phase 3 compiles |

---

## Appendix A — Parameter detail

Each entry gives the value, rationale, source, assumptions and limits, sensitivity, alternatives and recommendation. "No verified source" means none is in `00_governance/LITERATURE_REGISTER.csv`. No reference is invented here.

**P1 Gas composition.**
- Value: pure normal hydrogen (x_H2 ≥ 1 − 10⁻⁶).
- Rationale: project scope decision of 2026-11-13.
- Source: tables from Leachman 2009, Muzny 2013 and Assael 2011 via CoolProp 7.2.0 (register L10–L13); V1 PASS.
- Limits:
  - Tables cover 200–500 K and 0.05–12 MPa; outside that range Simscape stops (range check = error).
  - Blends are refused by the composition interface.
- Sensitivity: n/a.
- Alternatives: H2–CH4 blends (GERG-2008 parameters in CoolProp; default flash fails for H2-rich blends; new authorization needed).
- Recommendation: APPROVE.

**P2 Pressure envelope.**
- Value: 3–8 MPa (amended from 2–8).
- Rationale:
  - with a 2 MPa lower bound, any supply at the bound puts all outlets below it;
  - capacity at 2 MPa is 40 % of that at 5 MPa.
- Source: calcs F; screening. No verified design-code source.
- Assumptions: transmission service; the property tables extend to 12 MPa.
- Sensitivity: capacity ∝ p; leak flow ∝ p.
- Alternative: keep 2–8 MPa with the nominal ≤ 17 kg/s (50 % of 34.6).
- Recommendation: AMEND (owner chooses).

**P3 Temperatures.**
- Values: transmission gas 270–330 K; isothermal reference 313.15 K; soil 283.15 K.
- Rationale:
  - the aftercooler fixes discharge T;
  - buried-line gas relaxes toward soil T, at a rate set by U (unknown).
- Source: calcs G. No verified soil or U source.
- Limits: the isothermal V2 target ignores the axial T profile. The choice of 313 K vs 283 K changes ρ by about 10 %, and Δp proportionally at fixed mass flow.
- Alternatives: reference at soil T; or a non-isothermal reference (not implemented).
- Recommendation: AMEND for the reference T; DEFER the soil value.

**P4 Nominal demand.**
- Value: total and per-segment flows ≤ 50 % of the 20 m/s capacity at p_min.
- Rationale: keeps margin for the load profiles and leaks within V8.
- Source: calcs F.
- Limits: the 50 % margin is an engineering choice.
- Sensitivity: velocity ∝ demand / p.
- Alternatives: 70 % margin (fewer V8 rejections at high load is not guaranteed); demand defined per outlet profile.
- Recommendation: AMEND (owner fixes the numbers and the G3–G6 + end allocation).

**P5 Velocity limit.**
- Value: 20 m/s at the outlet.
- Rationale: erosion and noise limits are customary.
- Source: none verified.
- Limits: applying it at the inlet under-states the outlet velocity by up to 4.5 %.
- Alternatives: a lower limit for hydrogen service.
- Recommendation: AMEND; source DEFER.

**P6 Geometry.**
- Value: released lengths and diameters.
- Rationale: preserves the released topology for comparability.
- Source: XML extraction.
- Limit: the 0.355 m and 0.4 m end pipes constrain the end demand strongly (3–12 kg/s capacity).
- Alternatives: re-sized end pipes (breaks comparability).
- Recommendation: APPROVE.

**P7 Roughness.**
- Value: 0.045 mm.
- Rationale: commercial steel.
- Sensitivity: Δp +12 % / −8 % at 0.1 / 0.02 mm.
- Source: none verified yet.
- Alternative: 0.02 mm (coated line).
- Recommendation: APPROVE the value; DEFER the source.

**P8 Heat transfer.**
- Value: convection to soil; U per pipe TBD.
- Rationale: buried lines are not adiabatic (A-04).
- Source: none verified.
- Limits: steady-state targets are unaffected (isothermal); transients and V3 are affected.
- Alternative: keep adiabatic and state it as a limitation.
- Recommendation: DEFER.

**P9 Compressors.**
- Value: ideal Δp, power_spec none, aftercooler to 313.15 K.
- Rationale: the isentropic release overheats (calcs G).
- Limits:
  - no compressor map;
  - power from a hand calculation in V3;
  - faults as explicit Δp changes (multiclass design).
- Alternatives: two-stage with intercooling; isentropic with efficiency.
- Recommendation: APPROVE the representation; AMEND the set-points to M1.

**P10 Demand outlets.**
- Value: controlled mass-flow sinks at G3–G6 and the network end.
- Rationale: calcs A; separates demand from leaks (A-06).
- Limits: load profiles are still to be specified (owner).
- Alternative: pressure-controlled outlets (not proposed).
- Recommendation: APPROVE.

**P11 Leaks.**
- Value: three classes (0.5 / 2 / 10 %) at ≥ 6 mid-pipe positions.
- Equivalent diameters with definition A at 5 MPa and 42.6 kg/s nominal: 11.9 / 23.8 / 53.3 mm. They scale as √(nominal / p) and must be recomputed at the decided P4.
- Limits: nozzle formula vs Simscape model form (V4).
- Sensitivity: leak flow ∝ p·A.
- Recommendation: AMEND (choose definition A or B).

**P12 Segmentation.**
- Facts:
  - steady-state lumping error < 4×10⁻⁶ even for one 30 km block;
  - transient wave content requires segments and inertia.
- Value: decided after V5/V7.
- Recommendation: DEFER.

**P13–P14.**
- Values: steady-state initial state; stiff variable-step reference solver.
- Rationale: avoid the fill transient (A-09); numerical credibility (V6).
- Recommendation: APPROVE.

**P15 Let-down.**
- Value: pressure-reducing element with power_spec none.
- Limits: hydrogen's Joule–Thomson behaviour near ambient (inversion temperature far below ambient) means real throttling warms slightly. The representation must state its thermal assumption.
- Recommendation: DEFER.

**P16 V4 acceptance.** See §3.3. Recommendation: AMEND (methods owner).

**P17 Sensors.** Already decided. Recommendation: APPROVE (confirm).
