# Executed cases and numerical evidence

Accepted controlled captures (6): A:normal, A:outlet_opening, sid312:normal, sid312:outlet_opening, sid215:normal, sid215:outlet_opening. The three historical refinement runs remain available in the Phase 11 package.

| Opening | Onset delta (kg/s) | Peak delta (kg/s) | Final delta (kg/s) | Extra outlet mass (kg) | Final event-aware residual, control / opening (kg) |
|---|---:|---:|---:|---:|---:|
| SID 213 | 0.691269 | 0.694549 | 0.588247 | 13,064.834 | -0.939 / -1.306 |
| SID312 | +0.646769 | +0.646769 | +0.611832 | +12,139.528 | -1.207 / -1.331 |
| SID215 | +0.600544 | +0.600544 | +0.560493 | +11,043.399 | -1.333 / -0.956 |

## Sensor-subset comparison

The 30 s rows give dimensionless RMS separations after normalizing each channel by its own matched control pre-event RMS. Each case uses its own control. The pairing uses only exact saved knots.

| Pair | All sensors | Pressure only | Flow only | Without MFS3 |
|---|---:|---:|---:|---:|
| NORMAL vs SID213 | 0.0283582 | 2.32127e-05 | 0.0590323 | 0.000141069 |
| NORMAL vs sid312 | 0.0294074 | 8.92199e-05 | 0.0612161 | 0.0306082 |
| NORMAL vs sid215 | 0.00218504 | 0.000390126 | 0.0044924 | 0.00227426 |
| SID213 vs sid312 | 0.0408506 | 8.37896e-05 | 0.0850371 | 0.0306035 |
| SID213 vs sid215 | 0.0284344 | 0.000388542 | 0.0591867 | 0.00215289 |
| sid312 vs sid215 | 0.0293892 | 0.000358104 | 0.061175 | 0.0305893 |

## Formal outcomes and coverage

The consistency engine leaves each tested opening observation UNRESOLVED with L0. Each hypothesis remains indeterminate because the measurement uncertainty and physical prediction enclosures are unqualified. Neither accuracy nor selective risk has an eligible denominator. This numerical sensor comparison supplies no independent location claim.

See sensor_integrals.csv for native-unit residuals, pre/post metrics, descriptive onset and time integrals. The case registry includes exact source, preflight, approval and captured-file hashes. The comparative figure uses the same actual rows as subset_separability.csv.
