# Study C evidence enhancement — Methods

Additive, descriptive analysis of the published HY2RES package (`6a926de43f3283d9a995fbe0d8381a06c015344f`). No frozen file, split, mask, prediction, metric, model or rule was changed. Code: `analysis.py`, `report.py` and `test_enhancement.py` in this directory.

## M1 Source recovery and verification (Gate A)
- **No new download was needed.** The CSV committed at `abed1c1` (later removed in `6a926de`) is stored in Git with LF line endings: 38,321,178 bytes, MD5 `0352346b…`. Restoring CRLF line endings — a byte-level line-ending change only — gives exactly the official file: **38,621,947 bytes, MD5 `9a3c3e3b1668596854b43bfd790d3e0e`** (publisher value), SHA-256 `c9adf30dc1ac53e28c929505a23f84abc6e91185a4c07088adb49dd994601cdf`.
- `analysis.py` refuses any file whose size or MD5 differs.
- The verified file is kept outside version control (local dataset folder; a gitignored copy for the frozen script).
- The source path is configurable with `--source` or `HY2RES_SOURCE_CSV`.

## M2 Frozen benchmark reconciliation (Gate B)
MAE = (1/n)Σ|e| and RMSE = √((1/n)Σe²), recomputed from `test_predictions.csv.gz` overall and per operating regime. They are compared with `publication/TABLE_2_HELD_OUT.csv` at relative tolerance 1e-12: 60 checks, maximum absolute difference 9.0e-17.

## M3 Recording grid and resolution-normalised ratios
- **Grid:** for each channel, the distinct recorded values, the smallest positive step between them, and the fraction lying exactly on multiples of 0.1 (`rtol = 0`, `atol = 1e-9`).
- **Recording increment:** Δ_record = 0.1 bar for both pressures. This is quantization of the published CSV, not instrument resolution or accuracy, neither of which the source documents.
- **Normalised metrics:** MAE/Δ_record, RMSE/Δ_record and their Ridge − Persistence differences. These are dimensionless descriptive ratios.
- **Recorded target step:** k = round((y_t − y_{t−1}) / Δ_record), on the shared 43,168-row mask. Classes are 0, ±1, ±2 and ≥3. Squared error per class: SSE_c = Σ_{i∈c} e_i², and ΔSSE_c = SSE_c(Ridge) − SSE_c(Persistence).
- Ridge predictions are never rounded.

## M4 Chronology
Partitions come from the frozen `validity_mask.csv.gz` (`split_role`). Per partition and channel the analysis reports raw-value minimum, quantiles (1, 5, 50, 95, 99 %), maximum, valid and missing rows, segment counts, and the fraction of rows beyond the frozen rule's development support. No reordering or interpolation is used. In the drift figure, lines break at every causal segment boundary.

## M5 Frozen rule replica (Gate C)
`frozen_rule()` reproduces the decision part of `publication/distinguishability/build_distinguishability.py` line for line:
- **Inputs:** origin inputs are lag-1 values within the same segment; the power label comes from lag-1 `P_elec`, `P_comp` and `P_pila`.
- **Cells:** development quartile cells (positive-flow quartiles plus an exact-zero flow cell). A state is admitted to a cell when at least 2 development segments support it.
- **Support guard:** every feature must lie within its development min–max.
- **Decisions:** SPECIFIC, AMBIGUOUS or UNRESOLVED.

The replica must reproduce the published crosstab and the 32,002 "out of range or nonfinite" count before any attribution is computed. It does. The original script was also run unchanged, and its printed counts match.

## M6 Reason attribution (additive)
Frozen decision labels are kept. For each test row the analysis records, per channel, below-min, above-max and nonfinite flags, plus the excess beyond the boundary.
- **Exclusive primary reason** (unresolved rows only), in this precedence:
  1. `INVALID_INPUT` (any nonfinite origin input);
  2. `OUT_OF_SUPPORT` (tank, then buffer, then flow);
  3. `EMPTY_CELL` (inside support, but no state has ≥ 2 development segments in the cell).
- **Non-exclusive accounting** counts every violated condition and reports overlaps and exact combinations.
- `INSUFFICIENT_DISCRIMINATION` does not appear as an unresolved reason, because the frozen code reports within-support multi-state cells as AMBIGUOUS, not UNRESOLVED.

## M7 Operating states and distinguishability
- **State outcomes:** cross-tabulated by power-defined label. The majority baseline is a constant "electrolyzer only".
- **Rank probability:** P(B > A) + ½P(B = A), with B the compressor-powered rows and A the electrolyzer-only rows, computed from mid-ranks exactly as in the frozen script. It is reported for all finite rows and for rows with positive flow.

## M8 Temporal bins
Fixed 6-hour bins, declared in code before any binned result was examined. Each bin reports unresolved and out-of-support fractions, the median tank pressure and its row count.

## M9 Formal D(Y) qualification
The source and the Study C artifacts were searched for qualified observation bounds, qualified physical prediction bounds, a competing fault library, independent event labels and location truth. None exists. Formal D(Y) is therefore not evaluated.

## Environment
Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7. Figures use Segoe UI because IBM Plex Sans is not installed.
