# H2Net v1 — engineering execution status (2026-11-14)

Coordinated by Ahmed (project lead). **No owner decision has been recorded.**
- `PARAMETER_DECISIONS.yaml` is unchanged (`OWNER_DECISIONS_REQUIRED`).
- Nothing here is approved by Yazan, Faisal or a designated modeller.
- No MATLAB model was built, loaded or simulated.
- No dataset was generated and no model was trained.

## 1. Ready for owner approval

`candidate/PARAMETER_DECISIONS_PROPOSED.yaml` holds exact entries for S2–S6, S8 and V8. The owner copies an entry into `PARAMETER_DECISIONS.yaml` and sets `decided`, `decided_by` and `date`.

| Entry | Proposal | Recommendation |
|---|---|---|
| M1 / S3 | supply 3.0 MPa; C1 discharge 6.5 MPa; C2 discharge 6.5 MPa | AMEND |
| M1 / S3 representation | **`power_spec = isentropic` kept**, plus an aftercooler. This amends my earlier P9: `none` adds no energy and leaves V3 with no power to check. | — |
| M2 / S4 | demand G3 4, G5 4, G4 5, G6 5, END 2 kg/s (total 20) | AMEND |
| M3 / S4 | controlled Flow Rate Source (G) sinks replace the four orifices and the end vent | APPROVE |
| M4 / S6 | roughness 0.045 mm | APPROVE (source to cite) |
| M5 / V8 | isothermal reference 313.15 K; 3–8 MPa; 20 m/s at outlets | AMEND |
| Deferred | U-value (S2), segmentation and inertia (S5), let-down representation (P15), leak severity definition (A/B) | DEFER |

## 2. Reference calculations executed (provisional, not X06 targets)

Source: `tools/simulation/h2net_v1_provisional_network.py` → `candidate/PROVISIONAL_STEADY_STATES.json`.
- Provenance records the SHA-256 of the proposed parameters, the network graph, the H2 tables and `gas_physics.py`.

**Base case, all three topologies:**
- **Feasible.**
- **Mass conservation exact** at every node: supply 20.00 kg/s equals the sum of the sinks.
- RK4 200 vs 800 steps: node pressures agree within 2×10⁻⁸ Pa.
- Pipe pressures 6.487–6.500 MPa; down model 3.996–6.500 MPa after a let-down to 4 MPa.
- Maximum outlet velocity 4.2 m/s (5.3 m/s in the down model), against a 20 m/s limit.

**Compressors (real-gas h/s tables):**

| Quantity | C1: 3.0 → 6.5 MPa, 20 kg/s |
|---|---|
| Isentropic discharge temperature | 390.3 K |
| Isentropic power | 22.8 MW |
| Discharge at η = 0.75 | 416 K |
| Aftercooler duty at η = 0.75 | 30.0 MW |

C2 needs only about 11 kPa at nominal demand.

**Let-down (down model):** isenthalpic 6.49 → 4.0 MPa warms the gas by 0.87 K (inverse Joule–Thomson).

**Sensitivity, center model:**

| Parameter | Range | Result |
|---|---|---|
| Demand | ×0.5 – ×1.5 | feasible; trunk Δp 2.9–23.5 kPa |
| T_ref | 283 vs 313 K | C1 discharge 353 vs 390 K |
| Roughness | 0.02–0.1 mm | trunk Δp 10.2–11.8 kPa |
| Discharge set-point | 4–8 MPa | feasible; minimum pipe pressure 3.98–7.99 MPa |
| Supply pressure | 3–4 MPa | C1 power 22.8 → 13.7 MW |

**Finding for the owners.** With demand limited by the 0.355 m end pipe, the 1.2 m trunk runs at about 4 m/s, under 20 % of its capacity, and loses only about 11 kPa. Pressure signatures of events will therefore be weak. The owners should weigh demand against detectability: the noise budget and leak classes.

## 3. Model components: implemented vs specified

| Component | State |
|---|---|
| Real-hydrogen gas properties on a copy | **implemented** (`h2prism_apply_h2_gas_to_copy`, gated; not run). Interface verified statically against the installed R2026b source. |
| Roughness and initial-state parameters on copies | **implemented** in the stage-1 builder `h2prism_build_h2net_v1.m` (gated G1–G5; not run) |
| Controlled demand sinks (G3–G6, END) | **specified** (`H2NET_V1_BUILD_SPEC.json`, library path, ports, nets, signals) |
| Compressor and aftercooler (Pipe (G) + Temperature Source) | **specified**; duty and temperatures from §2 for V3 |
| Leak branches (6 mid-pipe positions, Local Restriction (G) variable, Cd 0.64) and labels | **specified** |
| Sensor and topology mapping | **implemented** as data (sensor id → SID → net → provisional steady pressure) |
| Let-down (down model) | **deferred** (P15) |

Structural edits (adding and replacing blocks and connections) must be implemented and checked in the first authorized MATLAB session.

One correction to the sensor picture: Flow Rate Sensor (G)1 (MFS2) feeds a **single-port** Constant Volume Chamber. The chamber's other connection is a thermal port on a Perfect Insulator. MFS2 therefore reads only chamber filling, 0 kg/s in steady state.

## 4. Tests and checks

`tests/test_h2net_v1_execution_prep.py` (4 tests), `test_h2net_candidate_evidence.py` and `test_matlab_readiness.py` pass: 33 tests. They cover:
- the proposed record is not a decision and the real record is untouched;
- steady states are current, mass-conserving and feasible;
- compressor heating is positive and the let-down warms;
- the build spec is consistent with the released SIDs;
- the builder is gated and saves only copies.

## 5. Blockers to the first valid H2Net v1 simulation

1. **Owner decisions** M1–M5, plus the S2/S5/S8 entries or an explicit deferral, recorded in `PARAMETER_DECISIONS.yaml` by Yazan with the modeller. Faisal reviews the V4 rule and leak labels.
2. **X06:** regenerate the build spec from the decided values and compute V2 targets (the gate opens with item 1).
3. **R0 MATLAB readiness:** E4 memory gate. MATLAB with the Simscape libraries needs about 4.6 GB, so run with MATLAB alone or on a ≥ 16 GB executor.
4. **Executor** designated under the grant ("Yazan or a designated modeller").
5. **Structural edits** implemented and checked in MATLAB; then V2–V8.

## 6. Next executable action

Owner review of `candidate/PARAMETER_DECISIONS_PROPOSED.yaml` (M1–M5 first). Nothing else on the critical path can proceed without it.
