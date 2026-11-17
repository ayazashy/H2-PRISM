# H2Net v1: status under MODEL_DEVELOPMENT:H2NET_V1_PROPERTIES_AND_STEADY_STATE

- **Authorization:** project lead, 2026-11-13 (`AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml`, status ACTIVE).
- **Executor acceptance for the MATLAB parts:** not recorded.

| Part | Status | Evidence |
| --- | --- | --- |
| (a) Pinned CoolProp in an isolated environment, hydrogen tables, V1 | **DONE** | `.venv-h2props/` (git-ignored); `properties/ENVIRONMENT.txt` (CoolProp 7.2.0, git revision recorded); `properties/H2_REALGAS_TLU2.json`, `H2_REALGAS_TLU2_params.m`; `properties/V1_REPORT.json`; hashes in `properties/OUTPUT_HASHES.sha256`; `tests/test_h2net_v1_properties.py` |
| (b) Build the H2Net v1 model copies (S1–S8) | **BLOCKED** | engineering decisions S2–S6, S8 and the envelope (`PARAMETER_DECISIONS.yaml`), plus MATLAB R2025a or later |
| (c) Validation simulations V2–V6 | **BLOCKED** | (b), plus V2 reference targets, which need the decided parameters (`tools/simulation/h2net_v1_reference.py` loads the tables into the independent solver) |

## V1 summary (normal hydrogen; envelope 250–400 K × 0.1–10 MPa; 240 off-grid points)

| Quantity | Result | Criterion |
| --- | --- | --- |
| Interpolation error: ρ / cp / μ / k | 0.036% / 0.009% / 0.004% / 0.017% | ≤ 0.1% / 0.5% / 1% / 1% |
| γ = cp / cv | 1.399–1.433 | (1, 5/3] |
| Prandtl number | 0.67–0.69 | 0.5–1.0 |
| Compressibility Z | 1.0002–1.067 | real-gas effect up to about 7% at 10 MPa |
| Density anchor (273.15 K, 1 atm) | 0.08988 kg/m³ | 0.0899 ± 0.3% |

The tables reproduce the reference equation of state. They do **not** validate the equation of state itself; that rests on the cited publications.

## MATLAB steps once the decisions are fixed (for the executor)

1. Copy the released models to `H2Net_v1_{center,down,up}.slx`. Never modify the originals.
2. **S1:**
   - run `properties/H2_REALGAS_TLU2_params.m`;
   - on Gas Properties (G) (SID 4) of each copy, select the **real-gas** specification (the enumeration value is to be confirmed in the R2025a documentation);
   - `set_param` each `*_TLU2` field and the limits from the `H2` struct;
   - read every value back.
3. **S2–S8** as decided, with a parameter diff against the released SIDs.
4. **V2–V6.** Simulate to steady state at the prespecified operating points, compare with the reference targets, and record against the thresholds in `HYDROGEN_MODEL_SPECIFICATION.md` §4. Those thresholds are fixed before running.

No dataset generation, noise, labels, events, training or evaluation is covered by this authorization.
