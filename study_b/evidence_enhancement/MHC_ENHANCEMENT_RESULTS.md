# Study B evidence enhancement — Results

All numbers come from `results/replay/` and `results/analysis/`, which are regenerated from the verified archive. Full tables are in `results/tables/` (CSV and Markdown) and in `results/tables_bundle.md`. Figures are in `results/figures/`, each as a 3840 × 2160 PNG, an SVG and a caption file.

## 3.1 Source and experimental qualification

**Question.** What exactly is evaluated, and how independent is it?

**Data.** The verified MHC v1.2 archive contains 29 workbooks. 8 dual-stage runs are eligible: development runs 22, 23, 25, 26 and 27, and held-out runs 24, 28 and 29. The two targets are P-2 Stage II hydrogen pressure (barg) and MFC-3 outlet hydrogen flow (ln/min). There are 15,885 scored one-second pairs per channel (TAB_B01; FIG_B01).

**Dependence.**
- All runs use one apparatus.
- The held-out runs come from 2 recording dates: run 24 on 26 May, and runs 28 and 29 together on 22 July.
- Runs 28 and 29 start "from an undefined state".

**Source notes**, quoted verbatim and recorded as metadata only, never as event labels:
- **Run 24:** Stage I "surpassed the safety valve set pressure of 90 bar. Some hydrogen might have been released through it", and the run was stopped after a repeat.
- **Run 27:** "error in back pressure control, pressure too low".
- **Runs 22, 23, 25 and 26:** "outlet valve opened too late".
- **Run 27 conflict:** the header says "Cycle time 15 min", but the overview half-cycle is 10 min and the logged switch-overs are 10 min apart.
- **Run 26:** the note refers to "Experiments 67 and 68".
- **Run 25:** inherits a fully absorbed Stage I from excluded run 5.

## 3.2 Frozen benchmark replay

**Question.** Can the accepted Ridge be reproduced at observation level?

**Result.** All 24 frozen per-run values (3 runs × 2 channels × 2 models × MAE/RMSE) are reproduced **bit-identically**, with an absolute difference of 0 in every case, on the frozen counts of 4,940, 5,002 and 5,943 pairs (TAB_B02). The development set has 25,757 pairs.

Run-mean values:

| Channel | Persistence MAE | Ridge MAE | Persistence RMSE | Ridge RMSE |
|---|---:|---:|---:|---:|
| P-2 (barg) | 0.158993 | 0.173660 | 0.381001 | 0.378997 |
| MFC-3 (ln/min) | 0.031649 | 0.042411 | 0.287644 | 0.287410 |

**Fitted model** (standardized inputs; scaler mean 104.98 barg and 1.711 ln/min):
- Ridge intercepts: **+0.01444 barg** and −0.00013 ln/min per step.
- Coefficients: P-2 change = +0.0031·z_P + 0.0114·z_F; MFC-3 change = −0.0218·z_P − 0.0176·z_F.

**Interpretation.** Observation-level predictions are now auditable. Every analysis below rests on predictions that reproduce the accepted benchmark exactly.

## 3.3 Prediction error distribution

**Results** (TAB_B04; FIG_B04 for each channel), pooled over 15,885 rows per channel:

| Channel | Model | Median | P90 | P95 | P99 | Max | Exactly zero | Signed mean |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| P-2 (barg) | Persistence | 0 | 0.60 | 1.00 | 1.20 | 8.80 | 70.6 % | +0.0149 |
| P-2 (barg) | Ridge | 0.0237 | 0.630 | 0.979 | 1.181 | 8.777 | 0 % | −0.0016 |
| MFC-3 (ln/min) | Persistence | 0 | 0 | 0.02 | 0.99 | 13.11 | 90.7 % | +0.0008 |
| MFC-3 (ln/min) | Ridge | 0.0121 | 0.0277 | 0.042 | 0.973 | 13.117 | 0 % | −0.0007 |

**Interpretation.**
- Persistence is exactly right whenever the recorded value does not change. That covers 70.6 % (P-2) and 90.7 % (MFC-3) of rows.
- Ridge is never exactly right, because its predictions fall off the recording grid on 99.8 % and 99.6 % of rows.
- Ridge is slightly smaller only at P95 and above.
- Ridge's intercept removes persistence's mean lag during compression: the P-2 signed bias falls from +0.0149 to −0.0016 barg.

## 3.4 Extreme-error attribution

**Squared-error concentration**, with each model ranked by its own errors (TAB_B05; FIG_B05):

| Channel | Model | Top 0.1 % (16 rows) | Top 1 % (159 rows) | Top 5 % (795 rows) |
|---|---|---:|---:|---:|
| P-2 | Persistence | 16.7 % | 30.7 % | 59.1 % |
| P-2 | Ridge | 16.8 % | 30.4 % | 59.3 % |
| MFC-3 | Persistence | 55.0 % | 93.6 % | 99.99 % |
| MFC-3 | Ridge | 54.9 % | 93.4 % | 99.7 % |

**Paired attribution** of ΔSSE (Ridge − Persistence), with rows ranked by |persistence error| (TAB_B05b):

| Channel | Total ΔSSE | Inside top 1 % | Outside top 1 % | Inside top 5 % | Outside top 5 % |
|---|---:|---:|---:|---:|---:|
| P-2 (barg²) | −28.95 | −14.97 | −13.98 | −24.14 | −4.81 |
| MFC-3 ((ln/min)²) | −2.63 | −5.43 | **+2.80** | −6.62 | **+4.00** |

**Run decomposition** (TAB_B03; FIG_B03):
- **P-2 ΔSSE:** run 24 −2.90 (10 %), run 28 −2.26 (8 %), run 29 −23.79 (**82 %**).
- **MFC-3 ΔSSE:** run 24 +0.25 (Ridge worse), run 28 −1.29, run 29 −1.59.

**Interpretation.**
- MFC-3's RMSE is set almost entirely by its largest 1 % of steps, under both models.
- Ridge's MFC-3 RMSE gain lies entirely in those rare large steps. It is partly offset by losses on the 99 % of quiet rows.
- P-2's net gain is dominated by run 29 and by the top 5 % of changes.

## 3.5 Error dependence on observed change (retrospective)

**Results** (TAB_B06; FIG_B06), pooled over three runs:

| Channel | Observed change | n | Persistence MAE | Ridge MAE | ΔSSE |
|---|---|---:|---:|---:|---:|
| P-2 | no change | 11,211 | 0 | 0.0225 | +5.94 |
| P-2 | 1 increment (0.2 barg) | 2,036 | 0.200 | 0.194 | −3.66 |
| P-2 | 2–10 increments | 2,616 | 0.791 | 0.787 | −28.69 |
| P-2 | 11–100 increments | 22 | 4.03 | 4.01 | −2.54 |
| MFC-3 | no change | 14,409 | 0 | 0.0117 | +3.72 |
| MFC-3 | 1 increment (0.01 ln/min) | 626 | 0.010 | 0.020 | +0.26 |
| MFC-3 | 2–10 increments | 382 | 0.0466 | 0.0393 | −0.16 |
| MFC-3 | 11–100 increments | 363 | 0.529 | 0.522 | −0.92 |
| MFC-3 | >100 increments | 105 | 2.817 | 2.810 | −5.52 |

**Interpretation.** Persistence wins on steady rows, which are the majority. Ridge's fixed drift correction helps slightly when the signal is moving. This is retrospective characterization; Δy is not available at decision time.

## 3.6 Measurement resolution and controller role

**Resolution** (TAB_B07; FIG_B07):

| | P-2 | MFC-3 |
|---|---|---|
| Observed increment | 0.2 barg (994 distinct values, 100 % on grid) | 0.01 ln/min (411 distinct values, 100 % on grid) |
| Persistence MAE | 0.81 increments | 3.2 increments |
| Ridge MAE | 0.88 increments | 4.3 increments |
| Run-mean ΔMAE | 0.073 increment | 1.08 increments |
| Run-mean ΔRMSE | 0.010 increment | 0.023 increment |
| Median Ridge correction | 0.0228 barg (0.11 increment) | 0.0105 ln/min (1.0 increment) |

No instrument resolution or manufacturer accuracy is documented in the source. The increment is observed quantization, not certified accuracy.

- **P-2:** the Ridge–persistence differences are a small fraction of one recorded step.
- **MFC-3:** the MAE penalty is about one recorded step per row.

**Controller role** (FIG_B08; `analysis/controller_role.csv`). While MFC-3 reads zero, P-2 never exceeds the nominal outlet pressure by more than 1 barg:

| Run | Nominal outlet pressure | P-2 max while MFC-3 = 0 | Fraction of rows with MFC-3 flowing |
|---|---:|---:|---:|
| 24 | 180 bar | 181.0 barg | 19 % |
| 28 | 140 bar | 140.6 barg | 42 % |
| 29 | 180 bar | 180.8 barg | 41 % |

**MFC-3 is the controlled outlet (release) flow that holds P-2 at the outlet set pressure.** Its setpoint and valve command are not recorded. Forecasting MFC-3 therefore forecasts a controller's output, and P-2's plateau is a regulated value, not a free process response.

## 3.7 Cross-run variation

There are 3 independent workbooks from 2 dates.
- Persistence has the lower MAE in **6/6** run–channel cells.
- Ridge has the lower RMSE in **5/6**: run 24 MFC-3 is the exception, at +0.05 %.
- Relative MAE penalties are +5.6 % to +15.6 % (P-2) and +22.7 % to +82.7 % (MFC-3).
- Relative RMSE changes are −0.20 % to −1.02 % (P-2) and +0.05 % to −0.15 % (MFC-3).

Run 29 (MmNiFe/TiCrMn, 30→180 bar, 10-min cycles, undefined start) carries 82 % of the P-2 ΔSSE. Material, set pressure, cycle time and initial state are confounded, so no factor can be attributed. No interval or test is reported.

## 3.8 Contribution to H₂-PRISM

- **Layer I:** causal timestamped pairing, run separation, units and channel semantics are verified, and the controller role of MFC-3 is now documented.
- **Layer II:** the reference comparison is explained mechanistically, and its limits are quantified relative to recording resolution.
- **Layer III:** nothing is validated. There are no qualified competing event hypotheses, uncertainty bounds, incident labels or locations. The operator notes are not qualified labels. Formal D(Y) is **BLOCKED BY EVIDENCE** (TAB_B08; FIG_B09).

## 3.9 Scientific limitations

- 3 held-out workbooks, 2 recording dates, one apparatus, undefined initial states.
- No instrument specification; MFC-3 is a controlled variable whose setpoint is not recorded.
- Retrospective change bins.
- No fault, leak, localization or formal D(Y) evidence.
- openpyxl 3.0.10 was used instead of the pinned 3.1.5; the outcome was verified identical.
