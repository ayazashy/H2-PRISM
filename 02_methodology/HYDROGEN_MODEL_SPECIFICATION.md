# Hydrogen network model H2Net v1: conversion and validation specification

**Status:** SPECIFICATION ONLY. No model has been built or simulated.

- The released H2-SimNet models are not modified; they remain a secondary methodological benchmark.
- Project-lead scope decision (2026-11-13): H₂-PRISM targets hydrogen pipeline systems.
- Evidence: `05_documentation/GAS_MODEL_LIMITATION.md`; `06_audit_preparation/simulation/v2_normal_support/FINAL_PRE_EXECUTION_CHECK.md`; block parameters read from the six `.slx` files.

## 1. Physical defects of the released simulator (exact evidence)

| # | Defect | Evidence (all six models unless noted) | Consequence |
| --- | --- | --- | --- |
| P1 | **Gas is not hydrogen** | Gas Properties (G) SID 4: R = 0.287 kJ/kg/K (air); hydrogen = 4.124 | Densities, sound speeds and flows are those of a ~29 g/mol gas |
| P2 | **Active perfect-gas constants are physically impossible** | `gas_spec = 1` (perfect, to be confirmed in MATLAB); cp = 0.3469 kJ/kg/K with Z·R = 0.2865 → γ = 5.75 (> 5/3); Pr = cp·μ/k = 0.079 | Compression heating, sound speed and heat transfer are unphysical |
| P3 | **Adiabatic network** | the thermal ports of all 7 pipes and the chamber connect to Perfect Insulator blocks | Compression heat is never removed (estimated ≈ 2,000 K at compressor outlets under P2); buried pipelines are near ground temperature |
| P4 | **Idealised compressors** | Pressure Source (G) SIDs 55 and 239: ideal Δp source, `power_spec = isentropic`; no efficiency, map, speed, surge, cooling or power limit. Driven by `PS Step` (3 → 6.4 MPa at 25 s) and `PS Ramp` (let-down) | Compressor faults and delays have no physical mechanism to act on; the released FAULT/DELAY mechanisms are unknown |
| P5 | **Demand modelled as fixed orifices to atmosphere** | Local Restrictions G3–G6 (SIDs 213, 222, 312, 215) = 1e-3 m² venting to Reservoir (G) at p_atm 0.1 MPa (choked) | Consumer demand is pressure-driven venting. **Leaks are implemented on the same blocks**, so "weak leak" = changed withdrawal (root-cause report §3) |
| P6 | **Lumped pipes, no inertia** | each Pipe (G) is one lumped segment of 4–30 km; `inertia = false` | No pressure-wave propagation, no leak-position resolution along a pipe, no transit delays |
| P7 | **Inconsistent wall roughness** | ε = 0.045 mm (pipe 1), 4.5 mm (2), 0.45 mm (3, 8), **50 mm** (4, 7; ε/D = 0.05), 0.0045 mm (5) | Friction is arbitrary across pipes; likely unit slips (mm vs m) |
| P8 | **Start-up from atmosphere** | all pipes start at `p_init` = 0.101325 MPa | Every run starts with a pressurisation transient, not a steady operating state |
| P9 | **Mixed units at the supply boundary** | the supply reservoir's pressure input converter is in **bar** (Simulink-PS SID 6), temperature 288 K | A legitimate but error-prone convention; must be explicit |
| P10 | **Solver configuration** | launcher forces fixed-step ode14x 0.8/0.9 s; Solver Configuration: RelTol 1e-3, MaxNonlinIter 3, no local solver | Not verified against a tolerance study; the release grid (1 s) differs from the solver step |
| P11 | **Measurement model** | P&T sensors measure pressure only; noise added post hoc (0.0005 MPa, 0.25 kg/s; white) | No temperature channel. The noise level differs from the README claim (1–2%). |

## 2. Can a credible hydrogen-specific model be built from the available source files?

**Partly.** The released files supply a **network skeleton**:
- topology;
- pipe lengths and diameters;
- node, sensor and logging structure;
- the position map;
- block identities.

That skeleton is reusable. **Nothing in them supplies hydrogen physics.** P1–P8 must be re-specified, and four ingredients do not exist in the release:

| Missing ingredient | Why it cannot be derived from the release |
| --- | --- |
| Hydrogen thermophysical properties (Z, cp, μ, k as functions of T and p) | not present. They must come from a reference equation of state (normal hydrogen: Leachman et al. 2009; viscosity Muzny et al. 2013; conductivity Assael et al. 2011), e.g. via NIST REFPROP or CoolProp, with the version recorded. None is installed in this environment. |
| Compressor-station definition (stages, ratio per stage, efficiency, intercooling/aftercooling, control) | P4: not in the files; an engineering decision |
| Consumer demand profiles and leak geometry | P5: not in the files; an engineering decision |
| Intended operating envelope of a hydrogen network of this size (pressures, velocities, temperatures) | the release targets other conditions; must be specified and justified |

A model built this way is **physically credible as a simulation**. It will still **not be validated against a real hydrogen network**: no field data exist in this project. Claims must be worded accordingly ("simulated hydrogen network, physically consistent and verified against independent references").

## 3. Smallest technically sound implementation path

All steps produce a **new, versioned model family** `H2Net_v1_{center,down,up}.slx`, built from **copies**. The released files stay untouched, and each change is recorded as a parameter diff against the released block SIDs.

| Step | Change | Can be specified from source evidence now | Needs independent physical data or validation |
| --- | --- | --- | --- |
| S1 Gas | Gas Properties (G) → **real-gas specification** with (T, p) tables for normal hydrogen over at least 250–400 K × 0.1–10 MPa (wider if the compressor model requires it) | block, parameter names, table layout | the tables themselves (reference EOS); property validation V1 |
| S2 Thermal | Replace Perfect Insulators with **convective heat transfer to ground** (soil temperature, e.g. 283–288 K; overall heat-transfer coefficient per pipe) | ports and blocks | soil temperature and U values (literature or owner) |
| S3 Compressors | Pressure Source (G) kept as an **ideal pressure-rise element** with **power_spec = none** plus an **explicit aftercooler** to a set outlet temperature. Or a two-stage representation with intercooling. Faults are realised as explicit parameter changes (reduced Δp, trip, slow ramp). | blocks, signals, mechanism placeholders | efficiency and cooling assumptions; plausibility V3 |
| S4 Demand vs leak | Demand → **Controlled Mass Flow Rate Source (G)** sinks with prespecified load profiles. Leaks → **separate** Local Restriction (G) branches to atmosphere at **new mid-pipe positions** (S5), never on the demand blocks. | topology positions; separation of mechanisms | demand profiles (owner) |
| S5 Discretisation | Split each pipe into segments of ≤ 1 km (or a convergence-justified length); enable `inertia` if wave-level signatures are in scope | segment counts | convergence study V5 |
| S6 Roughness and initial state | Uniform steel roughness (e.g. 0.02–0.05 mm, owner to confirm); initialise from a **steady state** (from the S1–S5 model or the reference solver), not from atmosphere | parameters | — |
| S7 Units, sensors, logging | Keep the position-matched sensor set (map v0.1 SIDs) plus explicit units (MPa, kg/s); optionally add temperature at compressor outlets; export block identities | everything | — |
| S8 Numerics | Variable-step stiff solver for validation (ode15s/ode23t) with a tolerance study; the fixed-step production solver is chosen only if it reproduces the variable-step reference within tolerance | configuration | V6 |

## 4. Physical validation evidence required (all before any dataset generation)

| ID | Validation | Reference | Acceptance (proposed; to be fixed before running) |
| --- | --- | --- | --- |
| V1 | Property tables vs reference EOS at ≥ 50 (T, p) points inside the envelope | REFPROP or CoolProp (version pinned) | relative error: ρ ≤ 0.1%, cp ≤ 0.5%, μ and k ≤ 1%; `check_gas_properties` passes (γ ∈ (1, 5/3], Pr within the gas range, R = R_u/M_H2) |
| V2 | **Steady-state network** vs an independent solver: node pressures and branch flows at ≥ 5 operating points per topology | `src/h2prism/gas_physics.py` (isothermal, Haaland or Colebrook, real-gas Z from V1 tables; tested against closed form) | pressures within 0.5% of the pressure drop, flows within 1%. The friction correlation must match the Simscape block's documented choice (to be verified in the R2025a documentation). |
| V3 | **Compressor and cooler energy balance**: outlet temperature, power | hand calculation from the V1 properties | outlet T within the stated design band; power positive and consistent with Δh |
| V4 | **Orifice and leak flow** vs the compressible orifice equation | `gas_physics.orifice_mass_flow` (choked and unchoked) | within 1% |
| V5 | **Spatial convergence**: segment length halved | Richardson-style comparison | key outputs change < 1% |
| V6 | **Numerical convergence**: tolerance and step study; fixed vs variable step | the same model | < 0.5% on logged channels |
| V7 | **Transient sanity**: pressure-wave arrival time ≈ L / c with c from V1 (only if `inertia` is on); line-pack mass balance over a demand step | analytic | arrival within one solver step plus 5%; mass balance < 0.1% |
| V8 | **Operating envelope**: velocities (e.g. < 20 m/s in transmission lines), pressures within design, no choking except at orifices, temperatures realistic | design limits (owner) | all runs inside the envelope |

Validated means **V1–V8 passed and recorded**. It does not mean agreement with a real network.

## 5. Sensor mapping and units

- Keep the diagram-derived position map v0.1: 12 blocks logged by all three configurations.
- In the new models, log by **block identity**; never pad absent sensors.
- Units are explicit in the provenance: pressure MPa (absolute), mass flow kg/s, temperature K if logged.
- The noise model is specified per sensor type, stated as absolute σ with a seed per run. It is a design choice, documented separately from the physics.

## 6. What can proceed now without MATLAB (done or doable here)

- **Done:**
  - this specification;
  - `src/h2prism/gas_physics.py`, the independent reference with tests: closed-form pipe flow, friction limits, choked orifice, mass-conserving network; the released constants fail the consistency check;
  - the synthetic v2 scalability benchmark.
- **Doable without MATLAB:**
  - generating hydrogen property tables with a pinned CoolProp version, **after approval to install it** (it is a download);
  - V1 property comparison;
  - reference steady states for the planned operating points (V2 targets);
  - the multiclass design files (`MULTICLASS_SIMULATION_DESIGN.md`);
  - acceptance thresholds.

## 7. What requires MATLAB R2025a or later (with Simulink and Simscape)

- building the H2Net v1 copies;
- reading the active `gas_spec`;
- all simulations for V2–V8;
- the solver and tolerance study;
- any data generation.

## 8. First narrowly scoped authorization request

`06_audit_preparation/simulation/h2net_v1/AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml`, **not authorized**:

- **Scope:** `MODEL_DEVELOPMENT:H2NET_V1_PROPERTIES_AND_STEADY_STATE`.
- **Covers:**
  - (a) installing a pinned CoolProp in an isolated environment and generating the V1 hydrogen tables plus the V1 report;
  - (b) building the H2Net v1 model copies (S1–S8);
  - (c) running only the steady-state and numerical validation simulations V2–V6 at prespecified operating points.
- **Excludes:**
  - any dataset generation, noise, labels or event scenarios;
  - any training or evaluation;
  - any change to released models or to existing results.
