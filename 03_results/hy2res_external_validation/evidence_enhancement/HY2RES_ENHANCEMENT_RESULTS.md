# Study C evidence enhancement — Results

All numbers come from `results/analysis/` and are regenerated from the verified source and the frozen artifacts. Full tables are in `results/tables/` (CSV and Markdown) and are bundled in `results/tables_bundle.md`. Figures are in `results/figures/` (3840 × 2160 PNG, SVG and a caption file each).

**The test period was inspected previously, so every result below is descriptive.**

## 3.1 Source and measurement qualification

**Question.** Is this the official source, and what do its channels record?

**Evidence.** The restored file is the official one: 38,621,947 bytes, MD5 `9a3c3e3b…`, 300,768 rows, 23 columns, a 5 s source clock and 2,793 causal segments (TAB_H01).
- **Buffer pressure:** 64 distinct levels, 28.0–34.3 bar.
- **Tank pressure:** 263 distinct levels, 84.5–110.7 bar.
- **Both pressure channels** lie 100 % on multiples of 0.1 bar, with one missing row each.
- **Electrolyzer H₂ flow** is not quantized at 0.1. It has 25,465 distinct values and a smallest step of 0.0005 NL/h.

**Frozen reconciliation.** The archived metrics reconcile exactly (Gate B: 60/60 checks, maximum difference 9e-17). The frozen decision rule is reproduced exactly (Gate C: 7/7 counts, including 32,002 out-of-range or nonfinite rows).

**Limitation.** The source documents no instrument resolution, accuracy or synchronization bounds.

## 3.2 Quantization and prediction-error interpretation

**Question.** How should the frozen MAE/RMSE differences be read against the recording grid?

**Results** on the shared mask (43,168 rows, 409 segments) (TAB_H02, TAB_H03; FIG_H01–H03):

| Channel | Persistence exact hits | Persistence MAE | Ridge MAE | ΔMAE | Persistence RMSE | Ridge RMSE | ΔRMSE |
|---|---:|---:|---:|---:|---:|---:|---:|
| Buffer (bar) | 41,457 (96.04 %) | 0.003964 (0.040 incr.) | 0.005500 (0.055 incr.) | +0.0154 incr. (+38.8 %) | 0.019909 (0.199 incr.) | 0.017138 (0.171 incr.) | −0.0277 incr. (−13.9 %) |
| Tank (bar) | 32,119 (74.41 %) | 0.025598 (0.256 incr.) | 0.025141 (0.251 incr.) | −0.0046 incr. (−1.8 %) | 0.050599 (0.506 incr.) | 0.040698 (0.407 incr.) | −0.0990 incr. (−19.6 %) |

**Error by recorded target step:**

| Channel | Step | n | Persistence SSE | Ridge SSE | ΔSSE (bar²) |
|---|---|---:|---:|---:|---:|
| Buffer | 0 (unchanged) | 41,457 | 0 | 3.23 | +3.23 |
| Buffer | ±1 increment | 1,711 | 17.11 | 9.45 | −7.66 |
| Tank | 0 (unchanged) | 32,119 | 0 | 15.17 | +15.17 |
| Tank | ±1 increment | 11,048 | 110.48 | 56.32 | −54.16 |
| Tank | ±2 increments | 1 | 0.04 | 0.02 | −0.02 |

- Every nonzero pressure step is a single 0.1 bar step, apart from one ±2 step in the tank channel.
- Persistence error is therefore exactly 0 or 0.1 bar.
- Ridge predictions never fall on the grid and never equal the recorded value.
- On step rows Ridge's mean error is about 0.07 bar instead of 0.1 bar. It partly anticipates the step.
- Neither model shows a persistent offset: |signed mean error| ≤ 0.00023 bar.

**Interpretation.** Ridge's RMSE gain comes entirely from partially anticipating rare single-increment transitions. It pays for this on the unchanged majority of rows. All differences are a small fraction of one recording step. The comparison concerns the predictability of 0.1 bar quantization steps, not physically resolved pressure accuracy.

## 3.3 Chronological pressure drift

**Question.** How do pressures evolve across the frozen partitions?

**Results** (TAB_H04; FIG_H04):

| Partition | Rows | Segments | Tank min | Tank median | Tank max | Tank rows above dev max |
|---|---:|---:|---:|---:|---:|---:|
| Development | 210,537 | 1,940 | 84.5 | 94.2 | 106.6 | — |
| Validation | 44,396 | 429 | 100.2 | 102.4 | 104.9 | 0 % |
| Embargo | 1,438 | 14 | 100.5 | 101.75 | 103.8 | 0 % |
| Test | 44,397 | 414 | 103.8 | 107.8 | 110.7 | 71.8 % |

- Buffer pressure and flow stay inside the development ranges in every partition. Test buffer pressure spans 28.9–34.0 bar against development's 28.0–34.3.
- The tank pressure rises over the three-week record and oscillates daily.
- Validation never exceeds development support, so the support failure first appears in the test period.

**Limitation.** This is a temporal association; no physical cause is inferred.

## 3.4 Operating-support validity

**Question.** Which channels violate the frozen development support?

**Results** (TAB_H05, TAB_H05b; FIG_H05), out of 44,397 test rows:
- **Tank pressure above 106.6 bar:** 31,589 rows (71.2 %), in 299 segments, by at most 4.1 bar.
- **Buffer pressure and flow:** no breaches in either direction.
- **Nonfinite inputs:** 413 rows. They are the same rows for all three channels: segment-start rows that have no lagged origin value.
- **No row violates more than one channel.**

## 3.5 Unresolved-decision decomposition

**Question.** Why does the frozen rule abstain on most rows?

**Results** (TAB_H06; FIG_H06, FIG_H07). Frozen decisions on 44,397 test rows:

| Outcome | Rows | Share |
|---|---:|---:|
| SPECIFIC | 10,762 | 24.24 % |
| AMBIGUOUS | 1,327 | 2.99 % |
| UNRESOLVED | 32,308 | 72.77 % |

Among labelled rows (43,984) the shares are 24.47 / 3.02 / 72.51 %, as published.

**Exclusive reasons for the 32,308 unresolved rows:**

| Reason | Rows | Share of unresolved | Segments |
|---|---:|---:|---:|
| OUT_OF_SUPPORT (tank pressure) | 31,589 | 97.77 % | 299 |
| INVALID_INPUT (nonfinite origin) | 413 | 1.28 % | 413 |
| EMPTY_CELL (inside support, no state with ≥ 2 development segments) | 306 | 0.95 % | 3 |

**By 6-hour bin:** the unresolved fraction runs from 0.24 to 1.00 and tracks the out-of-support fraction bin by bin. The six bins with median tank pressure ≥ 107.0 bar are 100 % unresolved. Bins with medians of 105.8–106.8 bar are 24–63 % unresolved.

**Interpretation.** The abstention reflects the domain shift of a single channel. It is not ambiguity between valid operating hypotheses, and no implementation error was found.

## 3.6 Operating-state discrimination

**Results** (TAB_H07, TAB_H08; FIG_H08, FIG_H09):

| State | Rows | Segments | Specific (all correct) | Ambiguous | Unresolved |
|---|---:|---:|---:|---:|---:|
| Electrolyzer only | 43,167 | 405 | 10,762 | 1,126 | 31,279 (30,973 out of support, 306 empty cell) |
| Electrolyzer + compressor | 817 | 12 | **0** | 201 | 616 (all out of support) |
| Unknown power | 413 | 413 | 0 | 0 | 413 (invalid input) |

- **Imbalance:** 53 : 1 in the test period, and 62 : 1 in development (205,281 vs 3,316 rows).
- **Majority baseline:** a constant "electrolyzer only" matches 43,167 of 43,984 labels and recognises 0 of 817 compressor rows. All of the rule's specific calls fall in the majority state.

**Rank probability** (compressor-powered vs electrolyzer only):

| Channel | All rows | Positive flow only |
|---|---:|---:|
| Flow | 0.945 | **0.554** |
| Buffer pressure | 0.583 | 0.465 |
| Tank pressure | 0.528 | 0.494 |

- Zero flow covers 87.6 % of electrolyzer-only rows and 0 % of compressor-powered rows.
- Compressor-state flow lies in 318.7–339.0 NL/h, inside the electrolyzer-only positive range.

**Interpretation.** The apparent separation is zero versus positive production. On positive-flow rows the states overlap almost completely, and the pressures add no separation.

## 3.7 H₂-PRISM evidence implications

- **Layer I** (causal processing, source identity, recording grid): verified.
- **Layer II** (reference prediction): verified within one pilot record. A support-validity diagnosis now explains when the empirical reference is inapplicable.
- **Layer III:** HY2RES has no qualified observation or model bounds, no physical fault library, no event labels and no location truth. **FORMAL D(Y): NOT ESTABLISHED FOR HY2RES.** The finding that drift makes state attribution unsupported is an empirical support statement, not a physical exclusion (TAB_H09; FIG_H10).

## 3.8 Scientific limitations

- One residential pilot over three weeks; the test period was previously inspected, with no access seal.
- Operating labels come from electrical draw; there are no fault or location labels.
- No instrument specification or uncertainty bounds; 0.1 bar is the recording grid only.
- Rows are serially dependent; no interval or significance statement is made.
- **Repository finding (not a Study C result defect):** merge `abed1c1` committed unresolved conflict markers into 11 shared files on the published HY2RES branch, including `src/h2prism/windows.py`. This breaks import of the shared pipeline module. Faisal's own commits are clean, and the archived Study C artifacts do not depend on these files.
