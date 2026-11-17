# H₂-PRISM Center baseline research report

## Scope and methods

The study combines a checksum-pinned Center source model, six controlled pairs (12 accepted captures), and retrospective replay of the archived H₂-SimNet release. The controlled captures use ode14x with a 0.2 s step over 20,000 s and ten pressure plus three signed mass-flow sensors. Controlled case truth is the configured intervention. Shared Center ancestry makes the pairs unsuitable as independent confirmation. Source execution and numerical accounting support reproducibility within the modeled system. Hydrogen material fidelity and release-processing provenance remain unqualified.

## Controlled experiments

The SID 213, 312 and 215 outlet openings increased onset withdrawal by 0.691269, 0.646769 and 0.600544 kg/s, respectively. Extra withdrawal over the recorded horizon was 13,064.834, 12,139.528 and 11,043.399 kg. The alternate-profile traces show a distinct received outlet-area change and a measured flow response with its paired control. The SID 55 command reduction is an operational pressure change. SID 59 moves the same 3.0 → 6.4 MPa command from 25 to 26 s. Its 30 s normalized residual RMS falls from 0.027781 on the shared clock to 0.000121924 with retrospective event alignment (about 228×). The timing case supplies neither actuator-delay nor compressor-fault truth. [Mass accounting](tables/TAB_02.md) · [Timing residuals](tables/TAB_06.md) · [Intervention windows](tables/TAB_12.md).

## Historical replay and robustness

The oracle-onset model benchmark scored 39 LEAK-annotated observations. Logistic regression, random forest, XGBoost, linear SVM and RBF SVM matched 30, 36, 39, 33 and 23, respectively. A constant LEAK prediction also matches 39. Class-wise precision, multiclass accuracy and calibration are unestablished. [Model comparison](tables/TAB_03.md).

Clean one-second EWMA replay raised new alarms for 39/48 archived events, 30 within five seconds. It generated 42 false starts across 65.63 inactive archive hours. Persistent alarms under hypothetical noise make episode counts alone misleading. Capped CUSUM generated 45 false episodes under white noise and 226 under correlated noise. The 120 s replay detected 48/48 events with random forest and 37/48 with linear SVM, with 16 and two false episodes respectively. These different cadences support separate exploratory comparisons and provide limited evidence for operational use. [120 s replay](tables/TAB_04.md) · [One-second replay and stresses](tables/TAB_05.md).

## Diagnostic mechanism screening and localization

Time-aligned matched residuals (B3) are the primary controlled baseline. The complete mechanism library is an exploratory reference comparator. An unavailable matched observation remains BLOCKED_REFERENCE. On the alternate-profile query, B3 and NRES (B4) each ranked SID 213 first in 560/560 repeated settings. With all sensors, the full-library margin was 0.028358. Withholding MFS3 reduced it to approximately 0.000141. Neither repeated settings nor sensor contrasts establish independent localization performance. The eligibility gate routed 164/1,792 non-withdrawal settings incorrectly versus 165/1,792 for the full-library nearest mechanism. Gate disposition is REVISE_OR_REJECT. NRES showed no incremental decision benefit under the evaluated evidence. [Sensor contrasts](tables/TAB_09.md) · [Screening](tables/TAB_11.md).

## Claims and limitations

All 12 controlled observations remain UNRESOLVED, with zero qualified exclusions and localization L0. Specific coverage is zero and selective risk is undefined. [Formal outcomes](tables/TAB_13.md). Confirmatory multiclass accuracy, added distinguishability value, localization performance and industrial hydrogen performance are not established. Qualification requires independent run families, authenticated mechanism and location truth, independent calibration, synchronized signed pressure/flow, and traceable measurement, initial-state, boundary, parameter and prediction-discrepancy bounds. Any future selective-risk comparison must match coverage on a prospectively locked test partition.

The atlas identifies numeric sources by SHA-256 and includes the observed negative results. The acceptance gates and frozen benchmark configuration remain in the baseline freeze directory.
