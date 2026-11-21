# H1 limitations

1. **Test reuse.** All 27,993 outer-test windows were inspected in R2 and reused by the R2 diagnostics and Protocol 2.0. Every comparison here is post hoc and exploratory.
2. **Independence.**
   - Each held-out topology has 13 families, but the 17 scenario ancestors are shared by all three topologies.
   - Windows within a run are serially dependent.
   - The discordant errors driving every s_C vs s_C−D difference come from 1–3 ancestors.
3. **Attribution defect.**
   - 36 of 57 runs carry the other topology's source model.
   - 91.7 % of classifier errors lie in those runs, and the remaining 8.3 % follow from the swapped training composition.
   - D1 is not recorded, so no corrected replication was run.
4. **Coverage.** The shared attainable coverage is only [0, 0.258]. The registered targets 0.60/0.80/0.90 lie outside it. Low-coverage points rest on few families and are unstable (Δ moves from −0.134 to −0.006 between 0.15 and 0.25).
5. **Class support.** LEAK is 78.3 % of windows. COMPRESSOR_DELAY and NORMAL each have one ancestor. COMPRESSOR_FAULT never received a SPECIFIC decision at the registered 0.60 target.
6. **Calibration.** The identity map was selected in every fold. "Calibrated" therefore means "calibration evaluated, none applied".
7. **Baseline scope.** The conventional baseline differs from s_C by the whole evidence layer (flags + meta-model + D). Its comparison does not isolate D(x).
8. **Formal D(Y).**
   - Only on Center: one controlled simulation family, an air-like gas model and hypothetical bounds.
   - The 672 cells are repeated views of 6 captures.
   - There is no comparison against a classifier on shared independent scenarios.
9. **Simulation scope.** H₂-SimNet topologies are simulated. No field, hydrogen-pipeline or industrial transfer claim is possible. MHC and HY2RES contain no event labels and cannot inform H1.
10. **Precision heuristic.** The ancestor counts in H1-T08 derive from inspected data, assume 1/√n scaling, and are planning inputs only.
