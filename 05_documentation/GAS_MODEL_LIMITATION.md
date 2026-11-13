# Critical scientific limitation: the gas model of the released H2-SimNet simulations

- **Status:** CRITICAL. It applies to the released dataset, every result in this repository, and any data generated with the released models.
- **Recorded:** 2026-11-13.
- **Released models:** unchanged.
- **Evidence:** `06_audit_preparation/simulation/v2_normal_support/FINAL_PRE_EXECUTION_CHECK.md` §2–3.

## Finding

All six released models (`Anomalous_/Normal_HNetwork_gest_{center,down,up}.slx`) contain the same `Gas Properties (G)` block (SID 4):

- Specification switch `gas_spec = 1`, expected to be the **perfect-gas** specification.
- The active perfect-gas constants are R = 0.287 kJ/kg/K, Z = 0.998386, cp = 0.3469 kJ/kg/K, μ = 10.98 µPa·s and k = 48.2 mW/m/K. Limits: p ≥ 0.1 MPa (error), no upper pressure or temperature limit.
- The tabulated (semiperfect and real-gas) fields are air-like and inactive under this specification.

| Check | Result |
| --- | --- |
| Gas identity | R is air's (0.287); hydrogen is 4.124. **Not hydrogen.** |
| Heat-capacity ratio γ = cp / (cp − Z R) | **5.75**; no gas can exceed 5/3. **Physically impossible.** |
| Prandtl number cp μ / k | **0.079**; gases are ≈ 0.7. **Inconsistent.** |
| Transport properties | μ and k match neither air nor hydrogen |
| Compressor outlet (isentropic source, 0.684 → 7.08 MPa, inlet 288 K) | ≈ 2,000 K estimated (air ≈ 560 K). Temperature is not logged. |

## Is the active gas specification physically consistent?

**No**, provided step A of the execution handoff confirms that `gas_spec` resolves to `perfect` in MATLAB.

- If it resolved instead to semiperfect or real gas, the active properties would be the tabulated air data: physically consistent **air**, but still not hydrogen.
- **In no case does the released simulator represent hydrogen.**

## Is an alternative, validated gas-model pathway required?

It depends on the claim:

| Intended claim | Released gas model adequate? | Requirement |
| --- | --- | --- |
| Method-level claims **about the released H2-SimNet simulator as a benchmark** (diagnostic decision quality, distinguishability, abstention on its signals) | **Yes, with disclosure.** Results hold only for "the released H2-SimNet simulations (air-like, physically inconsistent gas constants)". | Disclosure wording (below) in every artifact; no physical or hydrogen interpretation |
| Any **hydrogen-specific** claim (hydrogen pipeline behaviour, hydrogen leak detectability) | **No** | Validated hydrogen pathway (below) |
| Any **physically quantitative** claim (thresholds in MPa or kg/s, detectability limits, temperatures, transfer to real networks) | **No** | Validated gas pathway (below) plus model validation |

**Required pathway for hydrogen-specific or physical claims.** None of these steps is done; each needs the dataset owner, the model authors and a separate authorization.

1. A **new model version**; the released models stay unchanged. Its Gas Properties (G) block must use hydrogen properties:
   - a real-gas specification with (T, p) tables from a reference equation of state (e.g. the Leachman hydrogen EOS via NIST REFPROP or CoolProp);
   - covering at least 0.1–10 MPa and 250–2,500 K, or an isothermal/heat-transfer configuration that keeps temperatures realistic;
   - tables, source and version recorded.
2. **Property validation** against reference data at the operating points: density, cp, γ, viscosity and conductivity, within stated tolerances.
3. **Compressor and let-down model review.** The isentropic Pressure Source at a pressure ratio of about 10 implies multi-stage compression with intercooling in practice; this needs an explicit thermal assumption.
4. **Regeneration of all classes** under the new version, with full provenance: NORMAL, LEAK, COMPRESSOR_FAULT and COMPRESSOR_DELAY.
5. **Re-running the evidence chain** on the new data: R2-equivalent runs, development arms, diagnostics. Every existing result is conditional on the released air-like model.

## Mandatory description of the released simulator and of data generated from it

> "Simulations of the released H2-SimNet network models, using the released gas definition (air-like R = 0.287 kJ/kg/K; perfect-gas constants that are physically inconsistent, γ ≈ 5.75). Not hydrogen-specific and not physically validated."

## Consequence for the pending NORMAL-support generation (package v3)

- The package uses the released gas model **by design**: it adds NORMAL support comparable to the released data.
- Its output is therefore useful **only for benchmark-level (first-row) claims**.
- If H2-PRISM's intended confirmatory claims are hydrogen-specific or physical, generating this package does not advance them. The validated pathway above must come first.
- This is a scope decision for the project lead, together with the dataset owner.
