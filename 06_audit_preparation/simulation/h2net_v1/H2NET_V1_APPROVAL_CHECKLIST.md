# H2Net v1 — approval checklist (decision gate)

**For the authorized owners: Yazan (dataset/model owner) with the designated modeller; Faisal reviews methods and labels.**
- Prepared 2026-11-14, coordinated by Ahmed.
- **Nothing here is approved.** `PARAMETER_DECISIONS.yaml` is unchanged (`OWNER_DECISIONS_REQUIRED`).

Evidence:

| File | Content |
|---|---|
| `candidate/PARAMETER_DECISIONS_PROPOSED.yaml` | proposed entries |
| `candidate/PROVISIONAL_STEADY_STATES.json` | provisional network steady states |
| `candidate/REFERENCE_CALCS.json` | parts A–G |
| `candidate/SIMSCAPE_SOURCE_EVIDENCE.md` | installed Simscape source |
| `H2NET_V1_DECISION_PACKAGE.md` | P1–P17 |

**Evidence labels used below:**
- **SUPPORTED:** follows from existing calculations or installed-source facts.
- **VALIDATE:** needs a MATLAB physical-validation result (V2–V8).
- **SOURCE:** needs a cited literature or design value.
- **OWNER:** a scope or design choice with no technical answer.

Figures marked "est." are scaled from existing results. They are not new runs; X06 recomputes them once decided.

---

## 1. Critical assessment before acceptance

### 1.1 The proposed 20 kg/s operating point

| Finding | Value | Consequence |
|---|---|---|
| Binding constraint | 0.355 m end pipe (≤ 2.2 kg/s at 3 MPa) | Total demand is set by one small pipe. The 1.2 m trunk runs at 2–4 m/s, under 20 % of its 20 m/s capacity. |
| Per-pipe Δp (center model) | 4.85 / 5.94 / 2.18 / 1.26 / 2.28 / 0.41 / 6.64 kPa (Pipe 1, 2, 3, 8, 4, 7, 5) | Steady pressure differences across the network are a few kPa at 6.5 MPa. |
| Feasibility | all three topologies; mass conservation exact; v ≤ 5.3 m/s | Physically consistent. |

**Verdict.** The operating point is feasible and conservative. Total demand can rise to about 25 kg/s within the P4 rule, but that changes the signatures only by (25/20)² ≈ 1.6×, so it is **not** the lever for informative scenarios (see 1.3).

### 1.2 Compressor power and cooling duty

| | C1 (3.0 → 6.5 MPa, 20 kg/s) | C2 (6.489 → 6.5 MPa, 16 kg/s) |
|---|---|---|
| Real-gas isentropic discharge | 390.3 K | 313.3 K |
| Isentropic power | 22.8 MW | 0.04 MW |
| η = 0.75 discharge / power / aftercooler duty | 416 K / 30.4 MW / 30.0 MW | ≈ 313 K / 0.05 MW / 0.05 MW |

**Verdict.**
- The energy balance is consistent: for scale, 20 kg/s of hydrogen carries about 2.4 GW on a lower-heating-value basis.
- The temperatures stay inside the property tables (≤ 500 K). The aftercooler is mandatory.
- **C2 does almost nothing.** It is a defect for scenario design, not for physics.

### 1.3 Pressure signatures of events (est., Δp ∝ ṁ² at fixed density)

| Event | Pressure signature | Flow signature |
|---|---|---|
| LEAK 0.5 % (0.1 kg/s) mid Pipe (G)1 | ≈ 0.02 kPa | +0.5 % at the supply |
| LEAK 2 % (0.4 kg/s) | ≈ 0.10 kPa (1.5×10⁻⁵ of 6.5 MPa) | +2 % |
| LEAK 10 % (2 kg/s) | ≈ 0.51 kPa (7.8×10⁻⁵) | +10 % |
| NORMAL demand variation ×0.5–1.5 | trunk Δp 2.9–23.5 kPa | — |
| C2 fault or delay at the proposed set-points | ≤ 0.011 MPa | — |
| C1 fault (Δp lost) | network falls toward 3.0 MPa | — |

**Verdict.**
- In **pressure alone**, LEAK is swamped by NORMAL demand variation by about two orders of magnitude.
- Whether a 0.1–0.5 kPa change can be resolved also depends on the sensor-noise model, which is still undecided (A-12, SOURCE).
- **Leak information is in the flow balance.** The design must measure flow at the supply side and in series on the main line.

### 1.4 The MFS2 sensor

- Fact: Flow Rate Sensor (G)1 (MFS2, SID 210) feeds a **single-port** Constant Volume Chamber (1 m³, `num_ports = one`). Its other connection is a thermal port on a Perfect Insulator.
- Consequence: MFS2 reads only chamber filling, 0 kg/s in steady state and about V/(ZRT)·dp/dt during transients. **It carries no network-flow information.**

### 1.5 Design changes needed for informative NORMAL, LEAK, COMPRESSOR_FAULT and DELAY scenarios

| # | Change | Why | Evidence |
|---|---|---|---|
| D1 | **Split compression.** C1 discharge **5.0 MPa**, C2 discharge **6.5 MPa**; C2 Δp ≈ 1.5 MPa (est.). | C2 fault and the released DELAY mechanism (ramp on SID 241) become observable. Est. with the 3.2 MPa supply (D7): C1 ≈ 357 K / 12.5 MW and C2 ≈ 338 K / 5.8 MW isentropic; all pipes stay ≥ 4.98 MPa. The scaling method reproduces the real-gas C1 base case: 392 vs 390.3 K, 22.8 MW. | SUPPORTED as an estimate; X06 recomputes |
| D2 | **Flow sensing for mass balance.** Add a supply flow sensor after C1 (new id `MFS0`). Re-site MFS2 **in series on the main line** at the Pipe (G)8 / Pipe (G)4 junction (new id `MFS2s`). | Leaks are visible as flow imbalance, not as absolute pressure. MFS2 at the dead-end chamber is uninformative. | SUPPORTED |
| D3 | **Keep the released MFS2 channel** only as a labelled comparability channel (`MFS2_chamber`), or drop it. | Avoids silently changing the meaning of a released channel name; position map v0.1 lists MFS2. | OWNER (amends S7) |
| D4 | **NORMAL load profiles** defined explicitly (range and rate of change); the ×0.5–1.5 range is feasible | NORMAL variability sets the detection floor for every other class | OWNER |
| D5 | **Leak classes:** keep 0.5 / 2 / 10 %; label 0.5 % as an expected low-signature class | The 0.5 % class tests the INSUFFICIENT_EVIDENCE behaviour of distinguishability v2 and must not be dropped silently | OWNER (+ Faisal for labels) |
| D6 | **Fault envelope:** V8 limits apply to NORMAL; for FAULT/DELAY runs, define a minimum pressure (proposal: ≥ 2.5 MPa) and a maximum discharge temperature (≤ 450 K, inside the tables) | A C1 trip drives the trunk toward the 3.0 MPa supply, at or below the NORMAL lower bound | OWNER |
| D7 | Supply reservoir **3.2 MPa** (not 3.0) | Keeps NORMAL operation strictly inside 3–8 MPa with margin | SUPPORTED (est.) |

---

## 2. Checklist

The minimum set for X06 is M1–M5.

| ✓ | ID | Decision | Proposed entry | Evidence | Owner | Rec. |
|---|---|---|---|---|---|---|
| ☐ | **M1** | Pressures and compressors (S3, P2, P9) | supply 3.2 MPa; C1 → 5.0 MPa; C2 → 6.5 MPa; `power_spec` isentropic + aftercoolers to 313.15 K (D1, D7) | SUPPORTED (est.); X06 computes; V3 = VALIDATE | Yazan + modeller | APPROVE amended |
| ☐ | **M2** | Demand (S4, P4) | G3 4, G5 4, G4 5, G6 5, END 2 kg/s; every segment ≤ 50 % of its 20 m/s capacity at the minimum pressure; load profiles per D4 | SUPPORTED; profiles OWNER | Yazan | APPROVE + define profiles |
| ☐ | **M3** | Outlet topology (S4, P10) | controlled Flow Rate Source (G) sinks (mass, power_spec none) to atmospheric reservoirs at G3–G6 and END | SUPPORTED | Yazan | APPROVE |
| ☐ | **M4** | Roughness (S6, P7) | 4.5e-5 m, all pipes | SUPPORTED; SOURCE for the value | modeller | APPROVE, cite source |
| ☐ | **M5** | Reference temperature and envelope (V8, P2, P3, P5) | T_ref 313.15 K; NORMAL 3–8 MPa, 270–330 K, v ≤ 20 m/s at outlets; FAULT/DELAY limits per D6 | SUPPORTED; limit sources = SOURCE | Yazan + modeller | APPROVE amended |
| ☐ | S7 | Sensors (P17 + D2/D3) | add `MFS0`, `MFS2s`; keep or drop `MFS2_chamber` | SUPPORTED | Yazan (+ Faisal) | AMEND |
| ☐ | S4 leaks | Leak geometry (P11, D5) | 6 mid-pipe branches, Local Restriction (G) variable, Cd 0.64, classes 0.5/2/10 %, **severity definition A or B** | SUPPORTED; final areas = VALIDATE (V4) | Yazan + Faisal | AMEND (choose A/B) |
| ☐ | V4 rule | Restriction acceptance (P16) | compare with Simscape's own loss-coefficient equation ≤ 1 %; nozzle-formula difference reported | SUPPORTED (installed source) | Faisal | APPROVE |
| ☐ | S2 | Heat transfer (P8, P3 soil) | convective to ground at 283.15 K; U per pipe | SOURCE | modeller | DEFER (explicitly) |
| ☐ | S5 | Segmentation and inertia (P12) | steady state 1 block per pipe; transient per V5/V7; inertia scope | VALIDATE; scope = OWNER | modeller | DEFER (explicitly) |
| ☐ | S8 | Numerics (P14) | ode15s, RelTol 1e-6 reference | VALIDATE (V6) | modeller | APPROVE baseline |
| ☐ | P13 | Initial state | steady state from the X06 targets | SUPPORTED | modeller | APPROVE |
| ☐ | P15 | Down-model let-down | pressure reduction to 4.0 MPa; isenthalpic (+0.87 K) | SUPPORTED (thermo); representation = OWNER | Yazan + modeller | DEFER or approve isenthalpic |
| ☐ | P1, P6 | Gas, geometry | pure normal H2 (decided); released geometry | SUPPORTED | Yazan | APPROVE (confirm) |
| ☐ | Gate scope | X06 / X05 gates | either all entries decided, or M1–M5 decided and S2/S5 recorded as **explicitly deferred** with `status: DECIDED_WITH_DEFERRALS` | — | Yazan | OWNER |

**Supported by existing calculations now:** M1 (as an estimate), M2, M3, M4 value, M5, S7, P13, V4 rule, P15 thermodynamics.

**Needs physical validation (MATLAB, after the build):**
- V2 network vs targets;
- V3 compressor and cooler (heating, duty, cooler length);
- V4 final leak areas;
- V5/V7 segmentation;
- V6 numerics;
- V8 per run.

**Needs a cited source:** roughness value, U-value and soil temperature, the 20 m/s limit, the sensor-noise model.

---

## 3. Exact entries for `PARAMETER_DECISIONS.yaml`

For the owner to paste and complete. Every `<…>` must be filled by the deciding owner; nothing is pre-filled as approved.

```yaml
status: <DECIDED | DECIDED_WITH_DEFERRALS>
decided_by: <name(s) and role(s)>
date: <YYYY-MM-DD>

S3_compressor_stations:          # M1
  decided: true
  value:
    supply_reservoir_pressure_MPa: 3.2
    C1_pressure_source_sid_55: {discharge_setpoint_MPa: 5.0, power_spec: isentropic}
    C2_pressure_source_sid_239: {discharge_setpoint_MPa: 6.5, power_spec: isentropic}
    aftercoolers: {after: [55, 239], outlet_temperature_K: 313.15, representation: "Pipe (G) + Temperature Source", sizing: V3}
    efficiency_for_power_reporting: [0.75, 0.85]
    down_model_letdown_sid_111: <"isenthalpic reduction to 4.0 MPa" | DEFERRED>
  decided_by: <owner>
  source: candidate/PROVISIONAL_STEADY_STATES.json; H2NET_V1_APPROVAL_CHECKLIST.md D1, D7

S4_demand_and_leaks:             # M2, M3
  decided: true
  value:
    demand_outlets: "Flow Rate Source (G), mass, controlled, power_spec none, to atmospheric Reservoir (G); replaces SID 213/222/312/215 and the end vent"
    nominal_demand_kg_s: {G3: 4.0, G5: 4.0, G4: 5.0, G6: 5.0, END: 2.0}
    load_profiles: <owner specification: range (e.g. 0.5-1.5 x nominal) and rate of change>
    leaks: {branches: 6, positions: "mid-length of Pipe (G) 47, 48, 49, 309, 106, 221", block: "Local Restriction (G), variable", Cd: 0.64,
            classes_percent: [0.5, 2.0, 10.0], severity_definition: <A | B>, area_confirmation: V4}
  decided_by: <owner>

S6_roughness_and_initial_state:  # M4
  decided: true
  value: {roughness_m: 4.5e-5, applies_to: all pipes, length_add: released values, initial_state: X06 steady state}
  source: <citation for the roughness value>
  decided_by: <owner>

operating_envelope_V8:           # M5
  decided: true
  value:
    isothermal_reference_temperature_K: 313.15
    normal: {pressure_MPa: [3.0, 8.0], temperature_K: [270.0, 330.0], velocity_limit_m_s: 20.0, applies_at: pipe outlet}
    fault_and_delay: {min_pressure_MPa: 2.5, max_discharge_temperature_K: 450.0}
  source: <citations for the limits>
  decided_by: <owner>

S7_sensors_and_units:            # amendment of the decided S7
  decided: true
  value: {base: position map v0.1, add: [MFS0 supply flow after SID 55, MFS2s in series at the Pipe (G)8 / Pipe (G)4 junction],
          released_MFS2: <keep as MFS2_chamber | drop>, units: {pressure: MPa absolute, mass_flow: kg/s}}
  decided_by: <owner>

S8_numerics:
  decided: true
  value: {reference_solver: ode15s, RelTol: 1.0e-6, production_solver: "only if within V6 of the reference"}
  decided_by: <owner>

S2_thermal_boundary:   {decided: false, deferred: true, reason: "U-value source missing; steady-state targets are isothermal"}
S5_discretisation:     {decided: false, deferred: true, reason: "segment length from V5/V7 in MATLAB; inertia scope: <owner>"}
```

---

## 4. What the decision unlocks

Once the entries are recorded:

1. **Regenerate the specification:** `h2net_v1_build_spec.py` from the decided values, giving status `SPECIFICATION_DECIDED` (gate G2). The script must be updated to read `PARAMETER_DECISIONS.yaml` and accept `DECIDED_WITH_DEFERRALS`; that is a small, testable change made after the decision.
2. **X06:** compute the V2 targets (no MATLAB).
3. **R0:** a memory-compliant MATLAB readiness run, with MATLAB alone or on a ≥ 16 GB executor.
4. **Designate the executor** under the grant.
5. **Build and validate:** stage-1 build, then the structural edits, then V2–V8.

Steps 2 and 3 are independent of each other; both need step 1.
