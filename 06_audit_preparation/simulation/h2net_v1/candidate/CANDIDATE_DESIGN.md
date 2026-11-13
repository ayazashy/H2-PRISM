# H2Net v1 — candidate engineering design (action X03 support)

**Status: CANDIDATE — NOT DECIDED.**
- Every entry below is a proposal with a validation test.
- The decision belongs to Yazan (dataset/model owner) with the modeller; Faisal reviews it.
- `PARAMETER_DECISIONS.yaml` is unchanged: `status: OWNER_DECISIONS_REQUIRED`.
- No MATLAB model was built or run.

Date: 2026-11-13. Screening tool: `tools/simulation/h2net_v1_envelope_screening.py`. Output: `ENVELOPE_SCREENING.csv` (144 rows).

## 1. Steady-state envelope screening (released geometry, hydrogen tables)

**Inputs**
- Pipes: the 8 released pipes (SIDs 47, 48, 49, 106, 107, 108, 221, 309). Lengths are 3–30 km; hydraulic diameters are 0.355–1.2 m.
- Roughness: the proposed 0.045 mm.
- Temperatures: the proposed 283.15 K and 313.15 K.
- Inlet conditions: inlet pressure 2, 5 and 8 MPa × inlet velocity 5, 10 and 20 m/s.
- Method: isothermal RK4 pipe integration with the hash-verified CoolProp H2 tables.

| Finding | Value | Consequence for the decision |
|---|---|---|
| Pressure drop at 20 m/s inlet, 2 MPa, 313 K | 14 kPa (4 km, 1.0 m) to 85 kPa (30 km, 1.2 m) | Hydrogen's low density gives **small** frictional pressure signatures in the released large-bore pipes. Leak and fault signatures in pressure will be weak unless velocities or pipe lengths are larger. This is an input to S4 (leak sizes) and to the sensor-noise budget. |
| Velocity growth along the pipe | v_out up to 20.9 m/s for v_in = 20 m/s | A 20 m/s limit has to be applied at the **outlet**, or set with margin at the inlet. |
| Max Mach | ≈ 0.015 | Kinetic-term neglect is justified. The Mach number uses the γ = 1.4 approximation inside `gas_physics` for tabulated gases; the H2 tables give γ ≈ 1.40–1.41. |
| Inlet at the lower envelope bound (2 MPa) | outlet always < 2 MPa | The supply set-point needs margin above the 2 MPa lower bound. This is a trivial boundary effect, not a feasibility problem. |
| Throughput at 20 m/s and 5 MPa | ≈ 86 kg/s (1.2 m pipe) | Use this to size nominal demands (S4) as a fraction of the velocity-limited capacity. |

## 2. Candidate values with the test that would accept each

| Item | Candidate | Acceptance test (before model build) |
|---|---|---|
| S2 thermal boundary | Soil at 283.15 K. U-value: **source not yet cited**. | A literature value for buried steel pipe is recorded in `LITERATURE_REGISTER.csv`, and V4 (energy balance) is computed. |
| S3 compressor | Ideal pressure rise plus an aftercooler to 313.15 K | Supply set-point ≥ 2.5 MPa, so the screening shows every outlet inside 2–8 MPa. |
| S4 demand | Nominal demand ≤ 50 % of the velocity-limited capacity of the feeding pipe | Screening at the decided demand: v_out ≤ 20 m/s on every pipe. |
| S4 leaks | Orifice areas giving 0.5, 2 and 10 % of local throughput | The independent orifice model gives these fractions at nominal pressure within 5 %. Needs the γ of H2 from the tables, not 1.4. |
| S5 discretisation | ≤ 1 km segments | V6 (segment-halving changes the steady state by less than tolerance). |
| S6 roughness | 0.045 mm | Source cited. Sensitivity to 0.02–0.1 mm reported with the screening tool. |
| S8 numerics | ode15s, RelTol 1e-6 reference | V6. |
| V8 envelope | 2–8 MPa; v ≤ 20 m/s at the outlet; 270–330 K | Screening table has every row inside at the decided operating points. |

## 3. What this does not do

- It does not compute X06 V2 reference targets. `--targets` refuses until every item in `PARAMETER_DECISIONS.yaml` is decided; tested by hand on 2026-11-13, exit code 2.
- It does not change the released models or the authorized H2Net v1 scope.

## 4. Evidence update 2026-11-14 (see `SIMSCAPE_SOURCE_EVIDENCE.md`, `REFERENCE_CALCS.json`)

Everything below is still **PROPOSED**. Owner decision: Yazan with the modeller; Faisal reviews.

| Item | Revised candidate | Basis |
|---|---|---|
| S4 demands | **Replace the open terminal vent** and the four atmospheric withdrawal orifices with controlled mass-flow sinks at G3–G6 and at the network end. | With hydrogen, the released vent would pass 3.3–3.5× the velocity-limited capacity, and the orifices give pressure-dictated, uncontrollable demand (A-06). |
| S4 leaks | Separate orifice branches with equivalent diameters of about 12 / 24 / 53 mm, giving 0.5 / 2 / 10 % of a 42.6 kg/s nominal at 5 MPa (Cd 0.64; recompute at the decided nominal). | Reference calcs C |
| S5 discretisation | Segment length is to be chosen for **transients only** (V7 wave arrival, inertia). A single block per pipe is accurate to < 10⁻⁵ in steady state. | Reference calcs D. The earlier rationale is corrected. |
| S6 roughness | One value for all pipes in 0.02–0.1 mm. The pressure-drop effect is about ±10 % within that range; a literature source must still be cited. | Reference calcs B; A-08 |
| S3 compressors | Released `power_spec = isentropic` without efficiency or cooling. Keep the proposal: an explicit aftercooler to 313.15 K, and decide the efficiency treatment. | installed pipe/pressure-source source; A-05 |
| V2 comparison | Include `length_add` in the effective length. The friction correlation is confirmed identical (Haaland). | `pipe_friction.ssc` |
