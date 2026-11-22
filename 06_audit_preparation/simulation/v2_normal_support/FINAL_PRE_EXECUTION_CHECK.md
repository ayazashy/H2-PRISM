# Final pre-execution check: V2 NORMAL package v2 (2026-11-13)

- **Nature of the check:** non-destructive. No simulation was run.
- **Preserved:** the authorization record (`960a7b7`), the hash-bound files, commits `484f58c` and `73e71f8`, and the released models are all unchanged.
- **Gate status:** `python tools/simulation/v2_normal_authorization.py` → `ACTIVE`.

## 1. Does the MATLAB preflight consume the one-attempt authorization?

| Source | What it says or does |
| --- | --- |
| Authorization record | "covers preflight and generation … at most ONE execution attempt"; void "after one execution attempt (success or failure)". **"Execution attempt" is not defined.** |
| `EXECUTION_CHECKLIST.md` §7.2 (original) | after a preflight failure, "fix the environment and repeat the preflight", which treats preflight as **non-consuming** |
| `EXECUTION_CHECKLIST.md` §7.6 | "a repeat attempt, even with unchanged files, needs a new record" |
| Gate code `v2_normal_authorization.evaluate` | checks the grant, scope, package version and bound hashes only. **No consumption state exists in code.** |
| MATLAB generator | **does not check any authorization** (it only writes the scope string into provenance). It refuses a non-empty output folder, which prevents a second run into the same folder but not into a new one. |
| Post-processing and validator | require an active (granted, hash-matching) record. They do not count attempts and can be re-run. |

**Finding.**

- No code consumes the authorization. Neither preflight nor run changes any state that the gate reads.
- The one-attempt rule is purely **procedural**: the history row plus the executor's discipline.
- The documents are ambiguous about preflight. **The documented behaviour therefore does not fully match the implementation**, but it does not weaken the integrity controls:
  - hash binding is enforced;
  - sealing requires full validation;
  - the confirmation data cannot be accepted without an active record.

**Interpretation in force until the project lead decides (conservative):** the single attempt is the whole sequence, starting with the first invocation of `generate_v2_normal_support` in **either** mode.

- A failed preflight therefore ends the attempt. A retry needs the project lead's written confirmation that preflight is non-consuming, or a new record.
- The recommended clarification is: "preflight (no simulation, no signals) does not consume; the first `'run'` invocation does". It needs the project lead's decision and **is not applied here**.

## 2. Which gas properties are active

The Gas Properties (G) block is SID 4 in every model, identical in all six released models. It stores the fields of all three specifications; only one set is active:

| Specification (`gas_spec`) | Active fields | Status in the released models |
| --- | --- | --- |
| **Perfect gas** (enumeration 1) | `R`, `Z`, `T_ref`, `h_ref`, `cp_ref`, `mu_ref`, `k_ref`; limits `T_min_perfect` = 1 K, `T_max_perfect` = inf, **`p_min_perfect` = 0.1 MPa**, `p_max_perfect` = inf; `p_atm` = 0.1 MPa | **stored `gas_spec = 1` → expected ACTIVE** (enumeration order perfect, semiperfect, real) |
| Semiperfect gas (2) | `R`, `Z` plus the temperature tables `T_TLU1`, `h_TLU1`, `cp_TLU1`, `mu_TLU1`, `k_TLU1`; semiperfect limits | expected inactive |
| Real gas (3) | the (T, p) tables `T_TLU2`, `p_TLU2`, `rho_TLU2`, …; limits 0.001–10 MPa, 150–2,000 K | expected inactive |

`properties_range_check = error` applies to the active specification. The block's XML cannot prove which specification is active; **step A of the handoff confirms it in MATLAB:**

```matlab
foundation.enum.gas_spec(str2double(get_param(g,'gas_spec')))
```

The expected output is `perfect`. The table fields (air-like; e.g. ρ = p/(R T) with R = 0.287 at 150 K) are then **inactive reference data**.

## 3. Physically inconsistent active parameters

Evidence for every row: each of the six models, block SID 4 `Gas Properties (G)`, parameters as stored. The compressor inlet uses the supply-reservoir input, subsystem SID 12, `Constant` = 288 K.

| Quantity (perfect-gas specification) | Value from the active fields | Physical reference | Consistent? |
| --- | --- | --- | --- |
| R | 0.287 kJ/kg/K | air 0.287; hydrogen 4.124 | air-like, **not hydrogen** |
| cv = cp − Z·R | 0.0604 kJ/kg/K | air 0.718 | no |
| γ = cp / cv | **5.75** | air 1.40; any gas ≤ 5/3 | **impossible** |
| Prandtl number cp·μ/k | **0.079** | gases ≈ 0.7 | **no** |
| μ, k | 10.98 µPa·s, 48.2 mW/m/K | air 18.2 / 25.9; hydrogen 8.8 / 180 | match neither gas |
| Isentropic outlet of Pressure Source (G)3 (power spec = isentropic), inlet 0.684 MPa at 288 K | **≈ 1,920 / 1,990 / 2,060 K** at lift 6.1 / 6.4 / 6.7 MPa (estimated: temperature is not logged) | air would give ≈ 555–568 K | **no** |

**Consequences:**

- The temperatures are estimated: no temperature is logged, and the perfect-gas specification has no upper temperature limit, so the simulation does not stop on them.
- Density (p = Z ρ R T), and with it every logged pressure and flow, inherits this gas definition.
- The released dataset was produced with exactly this definition. The new runs are therefore **comparable to the release**, and **neither represents hydrogen or physically consistent air**.

## 4. How the outputs must be described

> "Exploratory NORMAL-support simulations of the released H2-SimNet network models, using the released gas definition (air-like R = 0.287 kJ/kg/K; perfect-gas constants that are physically inconsistent, γ ≈ 5.75). Not hydrogen-specific, not a physical validation, and not an evaluation of any method."

This wording is mandatory in the execution note (handoff step 5) and in any later use. The generator's provenance cannot carry it, because the generator is hash-bound and unchanged; the execution note carries it instead.

## 5. Verdict

**The authorized package is technically usable within its disclosed scope:**

- **It reproduces the released simulation conditions**, gas definition included, at 9 new NORMAL operating points.
- **Integrity controls are in place:**
  - every bound hash is enforced;
  - the released models are checked before and after the run;
  - the confirmation partition is sealed only on full acceptance;
  - confirmation results are PASS/FAIL only.

**It is scientifically usable only for that scope:**

- NORMAL-support data comparable to the release, for the exploratory support-definability purpose (H-R1).
- **Not** for any hydrogen-specific or physically quantitative claim.

**Open items, none of which blocks a correct execution:**

1. **Executor environment.** MATLAB R2025a or later with Simulink and Simscape: not verifiable here, checked by handoff step A.
2. **Definition of the attempt.** The conservative interpretation (§1) applies unless the project lead clarifies.
3. **Gas definition and resampling questions** for the dataset owner.
4. **Executor acceptance:** not recorded, and not recorded on his behalf.
