# H₂-PRISM scientific results atlas

[Research report](REPORT.md) · [Poster](poster/POSTER.md) · [Reproduction](REPRODUCE.md) · [Claims](claims.json)

## FIG_01_controlled_response — Controlled withdrawal under the alternate profile

Both twins share the +5 kPa reservoir profile. The atmospheric outlet area steps at 1,000 s only in the intervention.

[SVG](figures/FIG_01_controlled_response.svg) · [PDF](figures/FIG_01_controlled_response.pdf) · [PNG](figures/FIG_01_controlled_response.png) · [PNG](poster/FIG_01_controlled_response.png)

## FIG_02_timing_alignment — One-second command shift and retrospective alignment

Both commands move from 3.0 to 6.4 MPa on their recorded knots. Event alignment is retrospective and does not diagnose actuator lag.

[SVG](figures/FIG_02_timing_alignment.svg) · [PDF](figures/FIG_02_timing_alignment.pdf) · [PNG](figures/FIG_02_timing_alignment.png) · [PNG](poster/FIG_02_timing_alignment.png)

## FIG_03_archive_ml — Oracle-onset benchmark and class support

All 39 scored holdouts carry LEAK. The constant rule ties XGBoost. No multiclass accuracy is reported.

[SVG](figures/FIG_03_archive_ml.svg) · [PDF](figures/FIG_03_archive_ml.pdf) · [PNG](figures/FIG_03_archive_ml.png)

## FIG_04_detection — Detection delay and false-alarm burden

Cumulative clean replay uses all events in the denominator. Different decision cadences are shown in separate panels.

[SVG](figures/FIG_04_detection.svg) · [PDF](figures/FIG_04_detection.pdf) · [PNG](figures/FIG_04_detection.png) · [PNG](poster/FIG_04_detection.png)

## FIG_05_robustness — Hypothetical sensor stresses and persistent alarms

Each metric uses its own scale. Noise, bias, drift, stuck and delayed sensors are simulated perturbations without industrial calibration.

[SVG](figures/FIG_05_robustness.svg) · [PDF](figures/FIG_05_robustness.pdf) · [PNG](figures/FIG_05_robustness.png) · [PNG](poster/FIG_05_robustness.png)

## FIG_06_location_geometry — Location contrasts depend on sensor group

B3 normalized RMS, 30 s prefix, assumed ±1 s. Panel color scales are independent. Values do not constitute formal exclusion.

[SVG](figures/FIG_06_location_geometry.svg) · [PDF](figures/FIG_06_location_geometry.pdf) · [PNG](figures/FIG_06_location_geometry.png) · [PNG](poster/FIG_06_location_geometry.png)

## FIG_07_mechanism_evidence — Reference, timing and sensor ablations

The alternate case is one held-template query, not a set of independent trials. NRES (B4) weighting changes units of the numerical margin, not observed decision accuracy.

[SVG](figures/FIG_07_mechanism_evidence.svg) · [PDF](figures/FIG_07_mechanism_evidence.pdf) · [PNG](figures/FIG_07_mechanism_evidence.png)

## FIG_08_formal_decisions — Empirical evidence and qualified decisions

The schematic shows an evidence gate, not an automatic promotion of template ranks. No qualified exclusions were recorded.

[SVG](figures/FIG_08_formal_decisions.svg) · [PDF](figures/FIG_08_formal_decisions.pdf) · [PNG](figures/FIG_08_formal_decisions.png) · [PNG](poster/FIG_08_formal_decisions.png)

## TAB_01 — Accepted capture registry

All twelve captures belong to one Center source family.

[CSV](tables/TAB_01.csv) · [MD](tables/TAB_01.md)

## TAB_02 — Mass accounting across fixed integration steps

Mass in kg; residual is storage change minus signed integrated boundary flow.

[CSV](tables/TAB_02.csv) · [MD](tables/TAB_02.md)

## TAB_03 — Historical event-window model comparison

All 39 scored scenarios carry LEAK annotations; recall denominator is fixed.

[CSV](tables/TAB_03.csv) · [MD](tables/TAB_03.md)

## TAB_04 — Frozen 120 s decision replay

Episode counts and rates use the archived observation duration.

[CSV](tables/TAB_04.csv) · [MD](tables/TAB_04.md)

## TAB_05 — One-second causal replay and stress tests

Perturbations are hypothetical; duty is a fraction, rates are per inactive archive hour.

[CSV](tables/TAB_05.csv) · [MD](tables/TAB_05.md)

## TAB_06 — Command timing sensor residuals

Pressure MPa, signed mass flow kg/s. Clock and event alignment are separate.

[CSV](tables/TAB_06.csv) · [MD](tables/TAB_06.md)

## TAB_07 — Location and mechanism geometry

Normalized RMS on a 30 s prefix with hypothetical ±1 s alignment.

[CSV](tables/TAB_07.csv) · [MD](tables/TAB_07.md)

## TAB_08 — Matched-reference baselines on the alternate profile

One alternate profile; settings are repeated views of the same observation.

[CSV](tables/TAB_08.csv) · [MD](tables/TAB_08.md)

## TAB_09 — Sensor-withholding sensitivity

The margin is normalized RMS. Ranking establishes no exclusions.

[CSV](tables/TAB_09.csv) · [MD](tables/TAB_09.md)

## TAB_10 — Focal competing-mechanism routing

The focal controlled queries include self-templates; only one withdrawal used a held template.

[CSV](tables/TAB_10.csv) · [MD](tables/TAB_10.md)

## TAB_11 — Full routing sweep and retained withdrawal queries

Counts repeat settings across a shared family. Eligibility gate disposition is REVISE_OR_REJECT.

[CSV](tables/TAB_11.csv) · [MD](tables/TAB_11.md)

## TAB_12 — Intervention observation windows

Matched controlled simulations. The CSV retains original units and precision.

[CSV](tables/TAB_12.csv) · [MD](tables/TAB_12.md)

## TAB_13 — Formal decisions and localization

Localization L0 for all observations. Selective risk undefined at zero specific coverage.

[CSV](tables/TAB_13.csv) · [MD](tables/TAB_13.md)

## TAB_14 — Signed timing-pair boundary flows

Boundary accounting from the accepted timing pair; command timing is distinct from actuator response.

[CSV](tables/TAB_14.csv) · [MD](tables/TAB_14.md)
