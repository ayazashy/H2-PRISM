# Center evidence enhancement — Discussion

1. **Is there evidence of mechanism discrimination in Center?**
   Yes, descriptively, between the families of rivals. Operational pressure commands (SID 55, SID 59) produce 0.15–0.17 MPa pressure transients. Outlet withdrawals produce at most 5.6 kPa of pressure and a branch-flow step. The SID 55 query's nearest absent-self mechanism is the other operational rival, not a withdrawal (§3.2).

2. **Does it survive self-template removal?**
   Largely no. Without its own template, withdrawal at SID 213 or SID 215 is nearest to the zero residual, and SID 312 is a 1.9e-5 near tie. The 3/5 agreement rests on near-duplicates and that near tie. Withdrawal has no outlet-independent signature in this sensor layout (§3.2).

3. **Can controlled outlet locations be ranked?**
   Only for SID 213, the only outlet with a second realization: 2/2 top-1 across all sensor groups. SID 312 and SID 215 are unrepresentable once their own template is removed (§3.3).

4. **How strongly does ranking depend on flow sensors?**
   In B3, flow carries ≥ 0.9998 of every all-sensor outlet contrast, because each metered outlet moves exactly one branch meter by ~0.65–0.69 kg/s. This is partly B3's normalization by ~6 MPa absolute pressure (§3.4).

5. **Can pressure-only sensing distinguish the outlets?**
   In native units, yes in principle. The outlets differ by 1.1–5.5 kPa, and pressure-only ranking still places SID 213 first at 569× separation. Formally, pressure isolates SID 213 only if the total pressure bound is below 0.51 kPa. That precision is about 67× tighter than the observed 34 kPa solver-refinement difference (§3.5).

6. **Under what hypothetical conditions can rivals be excluded?**
   Exactly when ε < E for any channel kind, with E given per query–rival pair in TAB_C05. For SID 213 the correct-SPECIFIC window is [2.45e-6, 5.1e-4) MPa in pressure and [6.8e-4, 0.69) kg/s in flow. The lower edge is the realization discrepancy between the two SID 213 runs.

7. **Why did the original formal D(Y) remain unresolved?**
   For two independent reasons. The measurement contracts carried no error bounds (INVALID_UNCERTAINTY), and every declared hypothesis had `adapter=None`. Either one alone forces UNRESOLVED. The frozen result is therefore correct behaviour, not a defect.

8. **How do full and supported universes differ?**
   The full declared universe includes SID 222, COMPRESSOR_FAULT and ACTUATOR_DELAY without adapters, so it can never be SPECIFIC or AMBIGUOUS (336/336 UNRESOLVED). The restricted universe decides, but it can be confidently wrong when the true mechanism is unrepresented: SID 215 is called "Normal", and in flow-only sensing the timing case is called "pressure command". Restriction converts epistemic incompleteness into false specificity. That is the central caution of this study.

9. **What remains unsupported about FAULT and DELAY?**
   Everything physical. The pressure-command and command-issuance rivals are operational commands, not compressor faults or actuator lag. No FAULT/DELAY truth, adapter or bound exists.

10. **Relation to RQ1, RQ2 and RQ3.**
    RQ1 remains NOT_ESTIMABLE (registered R2). RQ2 remains negative (development ablation). RQ3 gains a conditional engine-level demonstration of the three outcomes and of their dependence on the declared universe (§3.6–3.7).

11. **Why H1 is not established.**
    There is no partition with independent families and nonzero attainable specific coverage. The Center evidence is one family, and its full-universe specific coverage is zero.

12. **Strongest honest proof-of-concept claim.**
    In a controlled air-like Center simulation, the frozen set-membership engine would, under declared hypothetical bounds, isolate a controlled withdrawal at SID 213 from every modelled rival within a finite precision window. Outlet separability is set by which branch flow meters exist. Without self-templates, B3 template matching does not generalize the withdrawal mechanism across outlets.

13. **What cannot be inferred about operational hydrogen systems.**
    Leak detection or localization accuracy, fault classification, field sensor adequacy, hydrogen behaviour (the gas model is air-like), and real-time performance.

14. **Limitations resolvable by code or analysis.**
    - A per-shift joint exclusion certificate would remove the hull bands (§3.5). It needs a new certificate type in the engine, which was not changed here.
    - Durable archiving of the captures, with your authorization.
    - A pre-registered location protocol for any future replicate captures.

15. **Limitations that need genuinely new evidence.**
    - Independent generating families.
    - Second realizations for SID 312 and SID 215.
    - Qualified sensor and model discrepancy bounds.
    - Physical FAULT/DELAY truth.
    - Network geometry.
    - Hydrogen-qualified properties.
    - Field or experimental data.

**Evidence levels, kept separate.**
- *Software-verified*: engine agreement with the closed form in 3,584 checks; 12 focused tests.
- *Simulation-based exploratory potential*: §3.2–3.4.
- *Conditionally demonstrated set-membership behaviour*: §3.5–3.6.
- *Experimentally validated diagnostic performance*: none.
