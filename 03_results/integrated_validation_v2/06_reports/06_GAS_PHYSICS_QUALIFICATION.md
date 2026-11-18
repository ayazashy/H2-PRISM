# Gas-physics qualification

Status **BLOCKED_BY_PHYSICS**. The Center gas is air-like (R = 0.287 kJ/(kg·K)) and is not renamed hydrogen.

| composition | property_basis_in_repository | diagnostic_data | missing_for_transfer | level_A_software | levels_B_C |
|---|---|---|---|---|---|
| Air-like legacy (Center) | R = 0.287 kJ/(kg·K); perfect gas, cp = 0.3469 → γ = 5.75 (>5/3, unphysical) | existing Simscape captures | physically inconsistent gas specification | A: engine runs on it | B/C: NOT QUALIFIED |
| Natural-gas reference | no property provider | none | — | A: refused by interface | B/C: NOT AVAILABLE |
| H2/CH4 blends (e.g. 80–95 % H2) | CoolProp 7.2.0 GERG-2008 binary (Kunz 2012) probe at 300 K, 5 MPa: default flash FAILED for x_CH4 0.05/0.10/0.20; imposed gas phase Z = 1.0266 at x_CH4 = 0.10 | none | phase stability per point and transport validation required | A: refused by interface (MixtureProviderUnavailable) | B/C: NOT AVAILABLE |
| Pure H2 | tables from Leachman EOS (CoolProp 7.2.0), envelope 250–400 K × 0.1–10 MPa; max interpolation error ρ 0.04% | property tables only; no transient model built (H2Net v1 BLOCKED) | transient model, boundary conditions, solver verification | A: provider resolves; engine unit-agnostic | B/C: NOT AVAILABLE |

Requirements for Level B:
- a transient network model with a qualified EOS (pure H2: Leachman; blends: GERG-2008 with per-point phase-stability checks);
- validated viscosity and transport;
- compressor maps;
- boundary conditions and a solver-convergence study.

Requirements for Level C: measured data.
