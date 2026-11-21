# Gas-composition transfer assessment

Table A13; figure AV-F14.

## Status

| Level | Meaning | Status |
|---|---|---|
| A — software portability | Engine and interfaces accept a composition without changing decision semantics | **Partly.** The formal engine works on templates and bounds in native units and is gas-agnostic. The composition interface (`gas_composition/0.1`, 8 tests) resolves pure H₂ to verified tables and **refuses** every blend and natural gas. 16 gas tests pass. |
| B — physics-based simulation transfer | Diagnosis on validated gas-specific simulations | **Not available.** No transient H₂ or blend network model exists. H2Net v1 model build and validation V2–V6 are BLOCKED (`06_audit_preparation/simulation/h2net_v1/STATUS.md`). |
| C — experimentally qualified transfer | Diagnosis of independently labelled physical events | **Not available.** MHC and HY2RES carry hydrogen measurements but no fault or leak events. |

**Answers:**

- **Pure-H₂ diagnostic transfer:** not demonstrated.
- **H₂/NG-blend transfer:** not demonstrated.
- **Legacy Center model:** air-like (R = 0.287 kJ/(kg·K)), with physically impossible perfect-gas constants (γ = 5.75). Its diagnostic results are therefore not hydrogen evidence.

## Required physics and evidence for a future gas campaign (protocol, not executed)

1. **Property basis.**
   - **Pure H₂:** existing tables from the Leachman equation of state (CoolProp 7.2.0). Envelope 250–400 K × 0.1–10 MPa; interpolation error ≤ 0.036 % in density.
   - **Blends:**
     - GERG-2008 (Kunz & Wagner 2012) mixing, with explicit composition basis (mole fraction).
     - A per-point phase-stability check, since the default flash failed at x_CH4 = 0.05–0.20, 300 K, 5 MPa.
     - Validated transport properties.
     - Authorization `MODEL_DEVELOPMENT:H2NET_V1_BLEND_TABLES`.
2. **Transient network model.**
   - Distributed pipes with inertia; the legacy model has lumped segments without inertia.
   - Non-adiabatic walls.
   - Physical compressor maps.
   - Consistent roughness.
   - Steady initial states.
   - All of these are listed as defects P2–P8 in `02_methodology/HYDROGEN_MODEL_SPECIFICATION.md`.
3. **Numerical verification.**
   - Solver-tolerance and grid studies.
   - Comparison with the independent steady solver (`gas_physics.Network`).
   - Mass-balance closure.
4. **Composition grid.** 0, 5, 10, 20, 50 and 100 % H₂ (mole basis). These are **candidate design points only**, not tested conditions.
5. **Gas-specific uncertainty bounds.**
   - Instrument specifications per composition.
   - Model discrepancy estimated against verification runs.
6. **Metrics, at matched coverage per composition.**
   - Specific coverage and false-specific risk.
   - Hypothesis inclusion.
   - Categorical location ranking.
   - Sensitivity to property uncertainty, and applicability failures.
   - Composition-robustness results kept separate from cross-system transfer.
7. **Effort and gates.** The MATLAB executor, engineering decisions S2–S6 and S8, and a new SIMULATION_GENERATION authorization per stage. No effort estimate is credible until the S-decisions are fixed.
