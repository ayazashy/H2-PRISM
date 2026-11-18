# Comprehensive scientific results (v2)

All values are generated from the files cited; the hypothesis statuses come from `02_design/HYPOTHESIS_REGISTRY.csv`.

## Diagnostic performance (R2, exploratory)
- Window accuracy is 0.714 on all 27,993 windows. Balanced accuracy is 0.749 and macro-F1 0.708.
- In the 19 undisputed runs (10,661 windows) accuracy is 0.938.
- Run-level majority accuracy:

  | Runs | Accuracy |
  |---|---|
  | Disputed (32 runs) | 0.562 |
  | Undisputed (19 runs) | 0.947 |

- Event runs called NORMAL: 13 of 13 lie in disputed runs.
- Tables: V2-T08 and V2-T09.
- NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY each come from one or two ancestors, so the class-wise rates are not generalisable.

## H1 — selective risk
Registered RQ1 NOT_ESTIMABLE in 12/12 PRIMARY rows (60/60 incl. secondary comparators). Exploratory at coverage 0.25: risk s_C 0.146 vs s_C-D 0.152, confidence 0.238, unguarded confidence 0.422; s_C errors in undisputed runs: 0; 7347/8012 classifier errors in disputed runs. s_C vs s_C-D at 0.25: ancestor bootstrap [-0.044, 0.023], family [-0.049, 0.034] (17 ancestors, 39 families).

## H2 — D(x)
Adding D worsened out-of-template log-loss: conf 0.906 -> 0.995; conf+margin+entropy 0.693 -> 0.828; worse in 10/16 and 10/16 held-out templates. In Center, 1-D identifies disputed-attribution windows with AUROC 0.084 vs error AUROC 0.393. Synthetic check: D helps only when the classifier is blind to an informative feature (Δ log-loss -0.006, -0.023, -0.046). Verdict: **no demonstrated improvement** (exploratory). Figure V2-F01.

## H3 — formal evidence integrity
0 forbidden transitions in 25,024 hypothesis-status checks (4,032 paired decisions); exclusion certificates re-verified 11,061/11,061; witnesses 1,552/1,552; adversarial tests: forged certificate rejected, NaN/negative bounds/duplicate sensors/broken clock never SPECIFIC, contradictory sensors -> MODEL_MISMATCH. Proof: `02_design/DY_MONOTONICITY_PROOF.md`.

## H4 — sensor robustness
Masks: all 8 correct/2 wrong; flow-only 8/4; pressure-only 2/0. SYNTHETIC faults (408 decisions, 33 fault settings): max wrong per setting 1 vs baseline 1, but wrong-specific risk rises from 0.200 to 0.333 (bias 2.0 eps_obs) because correct SPECIFIC decisions are lost first; large faults degrade to MODEL_MISMATCH; ±1-sample jitter outcomes identical to baseline: True. Figure V2-F02.

## Isolability (Normal vs SID 215)
- All channels: λ* = 0.080. The pair becomes isolable only once the bounds fall below about 0.080 × REF, i.e. 2.76e-03 MPa and 1.46e-03 kg/s.
- The limitation is the bound, not intrinsic identity: λ* > 0, so no admissible shift makes the two templates identical.
- The SID 215 template exceeds 2 ε_REF on 0 channels; its largest ratio is 0.081 on PS4.
- Pairs isolable at REF (of 15): all channels 14, pressure-only 9, flow-only 14.
- Figures V2-F03 and V2-F04.

## H5 — localization
DEMONSTRATED FOR ONE OUTLET; D(Y) location-specific coverage 0.500 with 0 wrong; supported independent locations 1.

## H6 — generalization; H7 — gas; H8 — cost; H9 — library; H10 — traceability
- **H6:** Out-of-template: untested (no held-out template). HY2RES Level-A port of the frozen rule reproduced it exactly (True); certified SPECIFIC 0 vs frozen singleton 10,762; ambiguous 1,327 = 1,327; wrong certified SPECIFIC 0.
- **H7:** Air-like legacy (Center): B/C: NOT QUALIFIED; Natural-gas reference: B/C: NOT AVAILABLE; H2/CH4 blends (e.g. 80–95 % H2): B/C: NOT AVAILABLE; Pure H2: B/C: NOT AVAILABLE
- **H8:** see V2-T07: Pareto membership depends on the hypothetical flow/pressure cost ratio; no monetary saving is quantified
- **H9:** minus_true: 2 wrong SPECIFIC, 4 ambiguous sets without the truth, 36 MODEL_MISMATCH of 42; full universe: 42/42 UNRESOLVED (unmodelled hypotheses are indeterminate).
- **H10:** in engine certificate 12/16; in frozen serialized record 7/16; certificate re-verification: 11,061/11,061 exclusions, 1,552/1,552 witnesses

## Status summary
- EXPLORATORY_ONLY: 4
- CONTRADICTED: 2
- NOT_ESTIMABLE: 1
- SUPPORTED_WITHIN_SCOPE: 1
- BLOCKED_BY_DATA: 1
- BLOCKED_BY_PHYSICS: 1
