# Simscape source and released-network evidence for H2Net v1 (2026-11-14)

**Method: static, read-only.**
- I read the installed MATLAB R2026b Update 1 Simscape Foundation library source files and the released `.slx` XML.
- **No MATLAB process was started.** The E4 memory gate (2.5 GB) blocks every MATLAB model operation on this laptop, and it was not bypassed.
- These findings answer questions that earlier required a MATLAB run. They are **not** the readiness Phases 1, 3 or 4, which remain unverified.

Installed files read (SHA-256, relative to `C:\Program Files\MATLAB\R2026b`):

| File | SHA-256 |
|---|---|
| `toolbox/physmod/simscape/library/m/+foundation/+enum/gas_spec.m` | `e41d782c008647d2e49708dceb9f8d475b2fefe05fe5d6f86b2925f1b732cd87` |
| `toolbox/physmod/simscape/library/m/+foundation/+enum/pT_region_G.m` | `6fcf3d69ddc13b2bb48ecb95ffb77bf580a427fa2a565801028dfedcce08b211` |
| `toolbox/physmod/simscape/library/m/+foundation/+gas/+elements/pipe_friction.ssc` | `62c1aa6f7afe4e046d6ddae33691f872e2edd3e00cd8eb4d8c9b9dea9c48e8e2` |
| `toolbox/physmod/simscape/library/m/+foundation/+gas/+elements/pipe.ssc` | `aa5138ed4aefc089ffc4b4675fd8a6850842da5579c4d52680635adea004138d` |
| `toolbox/physmod/simscape/library/m/+foundation/+gas/+utilities/gas_properties.ssc` | `d314d142f5b4b253092627c3919ea153e3295df54a96fe93b13ca76cc2ea09b4` |

Released network: `tools/simulation/extract_released_network.py` produces `RELEASED_NETWORK_GRAPH.json` and `RELEASED_PIPES.csv`. Each model file's hash is checked against the pinned value before parsing.

## 1. Active gas specification (A-16, X04 part 1)

- All six released models store `gas_spec = 1`.
- In the installed enum, 1 is `perfect_gas` (2 = semiperfect, 3 = real gas).
- Active constants: R = 0.287 kJ/(kg·K), Z = 0.998386, cp = 0.3469 kJ/(kg·K), μ = 10.98 µPa·s, k = 48.2 mW/(m·K).
- **Confirmed: the released models simulate an air-like perfect gas**, as recorded in `05_documentation/GAS_MODEL_LIMITATION.md`.

## 2. Pipe (G) friction correlation (A-17, X04 part 2)

`pipe_friction.ssc` (© 2019–2023):

| Element | Simscape Pipe (G) | `gas_physics.py` (independent reference) |
|---|---|---|
| Turbulent | Haaland: f = [−1.8 log₁₀(6.9/Re + (ε/D_h/3.7)^1.11)]⁻² | identical constants |
| Laminar | f·Re = shape_factor (default 64) | identical |
| Transition | `simscape.function.blend` between Re_lam = 2000 and Re_tur = 4000 | linear blend. It differs only for 2000 < Re < 4000; hydrogen transmission Re ≈ 10⁷. |
| Effective length | **length + length_add** (released: 0.004 m, or 20 m on Pipe (G)4/7) | V2 must add `length_add` |
| Density | evaluated at the block's single internal node; two half-length losses | distributed RK4 integration (difference quantified in §5 D) |

Pipe (G) in all released models: `dynamic_compressibility = true`, `inertia = false`, and heat transfer through `Nu_lam` with perfect insulators (A-04).

## 3. Real-gas table interface (Phase 4 question, answered statically)

- `gas_properties.ssc` (© 2016–2025) declares the following real-gas parameters, with these units:

  | Parameter | Unit |
  |---|---|
  | `T_TLU2` | K |
  | `p_TLU2` | MPa |
  | `rho_TLU2` | kg/m³ |
  | `s_TLU2` | kJ/(kg·K) |
  | `h_TLU2` | kJ/kg |
  | `cp_TLU2` | kJ/(kg·K) |
  | `mu_TLU2` | µPa·s |
  | `k_TLU2` | mW/(m·K) |
  | `beta_TLU2` | MPa |
  | `alpha_TLU2` | 1/K |
  | `pT_validity_TLU2` | — |
  | `T_min_real`, `T_max_real`, `p_min_real`, `p_max_real` | — |
- **All 15 fields of `H2_REALGAS_TLU2_params.m` exist, and the units of all 10 tables match exactly.**
- `pT_region_flag` defaults to `from_props`, which derives the valid region from the table extent. Our `pT_validity_TLU2` is all ones and is only used with `validity_matrix`, so it is harmless.
- `properties_range_check` defaults to `error`, so states outside 200–500 K or 0.05–12 MPa stop a simulation instead of extrapolating.
- The real-gas option value is `3` (`real_gas`). That is the explicit argument `h2prism_apply_h2_gas_to_copy` requires; it is **not executed** (build gate closed).
- **Still to confirm in MATLAB (Phase 4):** that the released block instance, saved in R2025a, exposes these parameters at run time.

## 4. Released network structure (input to S3, S4 and S6)

| Feature | Center and up models | Down models |
|---|---|---|
| Supply | controlled reservoir → Pressure Source (G)3 (Δp 4 MPa, set-point SID 59) | same |
| Mid-line compressor | Pressure Source (G)1 (Δp 4 MPa, ramp SID 241) | same |
| Compressor energy | **`power_spec = isentropic`**, no efficiency, no cooling (A-05) | same, plus Pressure Source (G)6, **−1 MPa constant let-down** |
| Withdrawals G3–G6 | fixed orifices 1e-3 m², Cd 0.64, **to atmosphere** (A-06) | same |
| Network end | Local Restriction (G)2 (0.7852 of 0.7853 m², fully open) → Pipe (G)5 (4 km, 0.355 m) → **atmospheric reservoir (open vent)** | let-down → Pipe (G)6 (3 km, 0.4 m) |
| Roughness | 0.045 / 4.5 / 0.45 / 50 / 0.0045 / 50 / 0.45 mm (Pipe (G)1, 2, 3, 4, 5, 7, 8) | Pipe (G)6: 45 mm (A-08) |

## 5. Candidate hydrogen reference calculations

Source: `tools/simulation/h2net_v1_reference_calcs.py` → `REFERENCE_CALCS.json`. Engineering evidence only; these are not decisions and not X06 targets.

**A — Released orifices with hydrogen.**
- Each withdrawal orifice is choked and passes 0.8 / 1.9–2.0 / 3.0–3.2 kg/s at 2 / 5 / 8 MPa, about 2.2 % of the 20 m/s capacity of the 1.2 m line.
- The open terminal vent alone would pass **3.3–3.5× that capacity** (upper bound: choked at the 0.0989 m² pipe exit).
- **Consequence:** with the released end vent, a hydrogen steady state cannot satisfy V8. S4 must replace the vent and the atmospheric withdrawals with controlled demand sinks.
- Approximation: perfect-gas orifice formula with local hydrogen Z and cp (γ ≈ 1.41–1.43).

**B — Roughness sensitivity** (16 km, 1.2 m, 10 m/s, 5 MPa, 313 K):

| Roughness | Δp |
|---|---|
| 0.02 mm (proposed) | 24.9 kPa |
| 0.045 mm (proposed) | 26.9 kPa |
| 0.1 mm (proposed) | 30.1 kPa |
| 4.5 mm (released) | 70.6 kPa |
| 50 mm (released) | 168.3 kPa |

Within the proposed range the effect is about ±10 %. The released values distort the signatures by up to 6×.

**C — Candidate leak sizes** at 5 MPa, 313 K, Cd 0.64, against a candidate nominal 42.6 kg/s (50 % of capacity):
- 0.5 % → 11.9 mm equivalent diameter;
- 2 % → 23.8 mm;
- 10 % → 53.3 mm.

**D — Lumping.**
- Simscape's one-node-per-pipe form differs from the distributed solution by ≤ 4×10⁻⁶ of Δp, even for a single 30 km block.
- **Steady-state accuracy therefore does not require segmentation.** The earlier "≤ 1 km segments" proposal is justified only by transients (wave arrival, V7) and inertia, which need a MATLAB transient run.
- This corrects the rationale in `CANDIDATE_DESIGN.md` §2.
