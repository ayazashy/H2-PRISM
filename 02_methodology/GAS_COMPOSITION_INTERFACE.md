# Gas-composition interface and H2–CH4 feasibility (action X20)

Status: **IMPLEMENTED_NOT_VALIDATED (interface) / BLOCKED_AUTHORIZATION (mixture tables)**. Date: 2026-11-13.
Code: `src/h2prism/gas_composition.py`; tests: `tests/test_gas_composition.py` (8 passed).
Probe: `tools/simulation/probe_h2ch4_feasibility.py` → `06_audit_preparation/simulation/h2net_v1/H2CH4_FEASIBILITY_PROBE.json`.

## 1. Interface (versioned `gas_composition/0.1`)

| Element | Rule |
|---|---|
| `GasComposition` | Mole fractions over a whitelist of species; they must sum to 1 within 1e-9; the composition carries a schema version. |
| `PureHydrogenTableProvider` | Serves the hash-verified H2Net v1 tables (CoolProp 7.2.0, Leachman/Muzny/Assael) **only** when x_H2 ≥ 1 − 10⁻⁶. |
| `MixtureProviderUnavailable` | Refuses every blend and states the blocker. |
| `resolve_provider` | Returns the first valid provider. It never falls back to an invalid one. |
| Out-of-table (T, p) | Refused by `gas_physics.TabulatedGas` (no extrapolation). |

The tests prove three things:
- 0.01 %, 2 %, 10 % and 20 % CH4 are all refused.
- Out-of-range temperature and pressure are refused.
- Pure H2 resolves to the verified tables.

## 2. Mixture equation of state: feasibility evidence (probe only, no tables)

- CoolProp 7.2.0 in the H2Net v1 environment contains the Methane–Hydrogen binary pair with the GERG-2008 parameters (`BibTeX: Kunz-JCED-2012`; departure function F = 1; γ_T = 1.3526, γ_V = 1.0187).
- CoolProp combines this GERG-2008 mixing model with its own high-accuracy pure-fluid equations. The result is therefore **not identical to GERG-2008** as published, because GERG-2008 uses its own pure-fluid equations. Any use must state this.
- **The default PT flash fails** at 300 K and 5 MPa for x_CH4 = 0.05, 0.10 and 0.20 ("One stationary point (not good)"). It succeeds for x_CH4 = 0.9.
- With an imposed single gas phase, every state evaluates. For example, at x_CH4 = 0.10: Z = 1.0266, ρ = 6.675 kg/m³, cp = 8 771 J/(kg·K). The imposed phase is defensible only if the state is shown to be single-phase gas, which holds far above the cricondentherm for these blends; that must be checked per table point.
- CoolProp returns mixture viscosity and thermal conductivity, but their model has **not been validated for H2–CH4 in this project**. Before use they must be validated against published measurement data. No reference for such data has been verified yet; see `00_governance/LITERATURE_REGISTER.csv`.

## 3. What remains blocked

1. **Owner decision:** decide whether blends are in scope at all. Hydrogen-primary is the current scope decision.
2. **New scoped authorization:** for example `MODEL_DEVELOPMENT:H2NET_V1_BLEND_TABLES`, to generate mixture tables with an imposed gas phase, per-point phase-stability checks and transport validation.
3. **Before any blend simulation:** the simulator's property interface must accept a composition-specific table set.

Nothing in this repository approximates blend properties from pure-H2 tables.
