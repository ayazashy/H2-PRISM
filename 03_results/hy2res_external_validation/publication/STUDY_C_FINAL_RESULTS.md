# Study C final results

**Scope.** One residential pilot, 27 March–15 April 2024. The five-second reference task compares persistence with one fixed contextual ridge on a chronological test period, 12 April 12:13:56–15 April 02:00:00. Times use the source clock. Figures and new stratifications are descriptive. The original protocol, predictions and metrics remain preserved.

## Table 1 · Dataset and validity

Official CSV MD5 `9a3c3e3b1668596854b43bfd790d3e0e`, 38,621,947 bytes, 300,768 rows and 23 columns. The 20 OPEN and 20 CLOSE markers form paired recording periods. The reconstructed 2,793 causal segments start at OPEN, after CLOSE, or at an interval other than 5 s. There were 297,975 five-second intervals, 21 duplicate intervals, 32 short positive intervals, and 2,739 longer intervals, including four over 60 s. Source order is preserved. Timezone, calibration and synchronization bounds are unspecified. Electrolyzer flow is normalized volumetric production associated with the preceding sample interval. Tank pressure is `pres_comp`. [Publisher source](https://zenodo.org/records/15166733)

The chronological roles contain 210,537 development, 44,396 validation, 1,438 embargo and 44,397 test rows. Lags of 5, 10 and 15 s precede the target and stay within one segment. The fit and scalers use development for selection and development plus validation for final fitting. Earlier embargo measurements can serve as context at the first eligible boundary. No interpolation is used.

| Test denominator | Varying targets, each | Fuel-cell targets, each |
|---|---:|---:|
| Source rows | 44,397 | 44,397 |
| Finite target | 44,396 | 44,397 |
| Standalone persistence scorable | 43,984 | 43,984 |
| Shared ridge/persistence scored | 43,168 | 43,168 |
| Shared scoring segments | 409 | 409 |
| Shared coverage of finite targets | 97.234% | 97.232% |
| Finite targets lacking contiguous three-lag history | 1,228 | 1,229 |

Standalone persistence coverage is approximately 99.07%. Its wider eligibility is reconstructed from source rows. Its errors on that wider mask were outside this benchmark. [Validity table](TABLE_1_VALIDITY.csv) · [Complete source schema](CHANNEL_SCHEMA.csv)

## Table 2 · Held-out prediction

| Channel [unit] | Persistence MAE | Ridge MAE | Change | Persistence RMSE | Ridge RMSE | Change |
|---|---:|---:|---:|---:|---:|---:|
| Buffer pressure [bar] | 0.003964 | 0.005500 | +38.8% | 0.019909 | 0.017138 | −13.9% |
| Tank pressure [bar] | 0.025598 | 0.025141 | −1.8% | 0.050599 | 0.040698 | −19.6% |
| Electrolyzer H₂ flow [NL/h] | 0.032730 | 0.178005 | +443.9% | 1.256965 | 1.185259 | −5.7% |
| Fuel-cell pressure [bar] | 0 | 0 | Undefined | 0 | 0 | Undefined |
| Fuel-cell H₂ flow [NL/h] | 0 | 0 | Undefined | 0 | 0 | Undefined |

Tank pressure shows the largest relative RMSE reduction. Its MAE difference is 0.000456 bar in absolute terms. Fuel-cell channels are constant zero throughout the source. The complete CSV preserves all channels, state-level results, relative differences, valid counts and coverage.

Electrolyzer-only state accounts for 42,367 rows across 405 scored segments. Multiple-active accounts for 801 rows across 12 segments. Flow RMSE in that smaller state rose from 0.134692 to 0.646516 NL/h (4.80×). Unknown states have zero scored rows. A recording segment can contribute to multiple strata. [Complete held-out table](TABLE_2_HELD_OUT.csv)

## Table 3 · Scientific evidence and claims

Layer I verifies checksum-matched measurements, chronological processing and reference computability. Layer II supports fixed reference comparisons and exploratory pressure–flow contrasts across power states. Layer III mechanism hypotheses remain indeterminate. Fault diagnosis, formal exclusions, leak localization and independent transfer lack qualifying evidence. [Evidence matrix](STUDY_C_EVIDENCE_MATRIX.csv) · [Discussion](STUDY_C_DISCUSSION.md)

## Publication figures

| Figure | PNG | Editable SVG |
|---|---|---|
| 01 · Pilot architecture | [PNG](FIG_01_MEASUREMENT_ARCHITECTURE.png) | [SVG](FIG_01_MEASUREMENT_ARCHITECTURE.svg) |
| 02 · Causal preparation and validity | [PNG](FIG_02_CAUSAL_VALIDITY.png) | [SVG](FIG_02_CAUSAL_VALIDITY.svg) |
| 03 · Held-out traces and residuals | [PNG](FIG_03_HELD_OUT_TRACES.png) | [SVG](FIG_03_HELD_OUT_TRACES.svg) |
| 04 · MAE and RMSE | [PNG](FIG_04_ERROR_COMPARISON.png) | [SVG](FIG_04_ERROR_COMPARISON.svg) |
| 05 · Operating-state dependence | [PNG](FIG_05_OPERATING_STATE.png) | [SVG](FIG_05_OPERATING_STATE.svg) |
| 06 · Evidence qualification | [PNG](FIG_06_EVIDENCE_QUALIFICATION.png) | [SVG](FIG_06_EVIDENCE_QUALIFICATION.svg) |
| 07 · Exploratory state overlap | [PNG](FIG_07_EXPLORATORY_STATE_OVERLAP.png) | [SVG](FIG_07_EXPLORATORY_STATE_OVERLAP.svg) |

[Contact sheet](CONTACT_SHEET.png) · [Acceptance](STUDY_C_FINAL_ACCEPTANCE.md) · [Reproduction](STUDY_C_REPRODUCE.md)
