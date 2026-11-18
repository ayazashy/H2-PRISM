# 09 — Scientific misinterpretation register

Each entry gives:
- the asset;
- the risky reading;
- why it is wrong;
- the required qualification (text that must accompany the asset if it is shown).

| # | Asset(s) | Risky reading | Why wrong | Required qualification |
|---|---|---|---|---|
| 1 | AV-F07, V2-F03, V2-T04, A16b | "14/15 pairs separable" = 93% diagnostic accuracy | Template-level property of 6 hypotheses under hypothetical bounds; no observation is classified | "Formally separable template pairs at REF bounds; not classification accuracy" |
| 2 | Q1_C14, Q1_C15, TAB_C06, T07b | "8 correct / 2 wrong" = 80% accuracy | 42 cells = 6 single captures × 7 declared bound scenarios; repeated views of 6 observations from one source family | State "42 decision cells from 6 captures; counts, not rates" |
| 3 | Q1_I01 ("48 correct, 11 wrong SPECIFIC"), T07a | Larger sample than Q1_C15 | Pooled over sensor groups and clock bounds; same 6 captures | Cite the denominator, or use the all-sensor ±1 s count (8/2) |
| 4 | Q1_C12–C15, V2-F03, V2-F04, AV-F04–F10, V2-F02 | Bounds are sensor specifications; results are safety guarantees | All bounds hypothetical; REF is a solver-refinement delta (`v2 01_audit/BOUND_ORIGIN_AUDIT.csv`) | Keep the "CONDITIONAL HYPOTHETICAL BOUNDS" stamp |
| 5 | Any Center figure | Hydrogen-pipeline evidence | Center gas is air-like (R = 0.287 kJ/(kg·K), γ = 5.75); one simulation family | "Controlled air-like simulation" |
| 6 | Q1_I08, T09b ("0 of 11,198 wrong") | H₂-PRISM makes no specific errors | Center fold excluded (0.60 unattainable); Downstream includes disputed-label runs; window counts are dependent | Name the fold exclusion, the 2-fold pooling and the label dispute |
| 7 | H1-F02a, AV-F01, AV-F02 | s_C halves the error of confidence, so H1 is supported | Exploratory, post hoc, inspected windows; registered H1 NOT_ESTIMABLE; s_C vs s_C−D intervals include 0; all s_C errors in disputed runs | "Exploratory; not a test of the registered H1" |
| 8 | AV-F11, A11a | 0 false LEAK = zero false-alarm rate | All NORMAL windows come from one scenario template (1 independent unit) | "One NORMAL template; no rate estimable" |
| 9 | V2-F01 panel (b), V2-T02 | D(x) helps when the classifier is blind | Synthetic method check; says nothing about H2-SimNet | Keep the SYNTHETIC stamp; never cite as evidence for D(x) |
| 10 | V2-F02, V2-T03 | Robust to sensor faults | Synthetic faults in units of ε_obs; wrong-specific risk rises at moderate faults | "Synthetic; fault counts do not increase wrong decisions but selective risk rises" |
| 11 | AV-F06, Q1_C09, A07 | Localization demonstrated | One outlet (SID 213) with near-duplicate captures; Levels 3–5 not demonstrated | "Categorical ranking, one outlet" |
| 12 | Q1_C04 (XGBoost recall 39/39) | Strong archive classifier | Constant "LEAK" rule ties it; all 39 scored holdouts are LEAK | Show with the constant-rule line |
| 13 | V2-F05, V2-T06 | Cross-domain diagnostic generalization | Level A software portability only; labels are electrical power states; zero hypothetical observation half-width; previously inspected test | "Software portability; no diagnostic transfer" |
| 14 | Q1_H*, Q1_B*, Q1_I02, Q1_I03 | Diagnostic validation on hydrogen hardware | Forecasting (persistence vs Ridge) of quantized signals; no fault labels | Present as measurement-resolution context only |
| 15 | AV-F12, A14a/b | Real-time industrial performance | Laptop CPU, single process, ranges measured only; D(x) rows on synthetic arrays | "Measured on one laptop CPU; not a deployment benchmark" |
| 16 | AV-F13, V2-T07 | Sensor-cost savings | No prices; relative hypothetical units | Never report savings; "sensor count only" |
| 17 | AV-F14 | Pure-H2 support (level A "provider resolves") | Property tables only; no transient model; no diagnostic transfer | "No diagnostic transfer for any gas" |
| 18 | AV-F15 | The engine cannot run on HY2RES | Superseded by V2-F05 (Level-A port executed) | Use V2-F05 or mark AV-F15 historical |
| 19 | AV-F16, H1-F07 ("D(Y) refuses with incomplete declared library") | The engine is safe against missing mechanisms | Refusal applies to declared-but-unmodelled rivals; removing the true mechanism gives wrong SPECIFIC (H9 CONTRADICTED) | Pair with AV-F04 |
| 20 | CE TAB_C05 onset 3.85e-4 kg/s vs V2-T04 λ* = 0.080 | Conflicting thresholds for Normal vs SID 215 | Different quantities: observation-to-template (single sensor kind) vs template-to-template (joint scale) | Do not place side by side without definitions |
| 21 | AV-F08 "pressure only: 2 correct" vs CE §3.4 "pressure alone ranks SID 213 first" | Contradiction | Formal certified decision vs B3 nearest-template ranking | Name the method |
| 22 | Q1_I05, V2-T08 (Center accuracy 0.213) | The model fails on Center topology | Center errors are the disputed-attribution runs (LEAK → NORMAL 7,307 windows) | "Disputed labels (D1 pending)" |
| 23 | V2-F06 colour cells | Quality scores | Criterion statuses (PASS/FAIL/BLOCKED/NA) with recorded reasons | Legend names the statuses |
| 24 | V2-F01 panel (a) symlog axis | Visual magnitudes comparable across the axis break | Symlog is linear below 0.1 and logarithmic above | Keep the axis label and the median annotation |
| 25 | R2 figure-system fig2 and other run-key variants | Multiple independent replications | Same run re-rendered under different run keys and build states | Only `_b200fcdac/final` is approved |
