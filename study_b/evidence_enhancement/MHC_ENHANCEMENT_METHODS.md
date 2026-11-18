# Study B evidence enhancement — Methods

Additive analysis of the accepted Study B benchmark (`research/mhc-validation` at `2f36d156f4fab9d00c1030b214039afe4b97175a`). No frozen file, split, feature, target, horizon, α, metric definition or acceptance decision was changed. Code lives in `study_b/evidence_enhancement/`: `replay.py`, `analysis.py`, `report.py` and `test_enhancement.py`.

## M1 Source verification
The official MHC v1.2 ZIP was verified by the frozen `verify_source.inventory`: 377,874,239 bytes, MD5 `64cbe2a68c0af5dc2e4a0a9690003eac`, SHA-256 `91755fb1e555e0eb32d160ac140a4261b6bb47d24944c7e717b723fe2a641e32`, safe member names. The frozen `verify_publication.py` also passed: archive, eligibility counts and persistence recomputation.

## M2 Frozen replay
`replay.py` imports the frozen `read_run`, `pairs` and `score` from `study_b/benchmark.py` and the frozen `protocol.json`. It does not reimplement them.
- **Pairs:** adjacent rows whose Seconds counter increments by 1 and whose wall-clock step lies within [0.8, 1.2] s, with both P-2 and MFC-3 finite at both ends.
- **Model:** `StandardScaler → Ridge(α = 100)`, fitted on the concatenated development pairs (runs 22, 23, 25, 26, 27; 25,757 pairs), in the frozen run order. Inputs are x_t = [P-2_t, MFC-3_t]; the target is x_{t+1} − x_t (both channels jointly).
- **Predictions:** persistence ŷ = x_t; Ridge ŷ = x_t + f(x_t).
- **Gate (declared before comparison):**
  - persistence metrics must equal the frozen values exactly;
  - Ridge |Δ| ≤ 1e-12 or relative ≤ 1e-9;
  - the row count must match.

  If the gate fails, no predictions are written and the analysis refuses to run.

## M3 Metrics
For one run and channel, with n scored rows and e_i = ŷ_i − y_i:

- MAE = (1/n) Σ |e_i|
- RMSE = sqrt((1/n) Σ e_i²)
- SSE = Σ e_i²

Run means are the frozen unweighted mean over the three held-out runs. ΔX = X_Ridge − X_Persistence; relative change = ΔX / X_Persistence.

**Quantiles.** Quantiles of |e| use the inverted-CDF rule, so every reported quantile is an observed value.

**Tail concentration.** Sort one model's squared errors in descending order, s_(1) ≥ … ≥ s_(n). For a fraction f, take k = ⌈f·n⌉ and report

  share(f) = Σ_{i≤k} s_(i) / Σ_i s_(i).

**Paired tail attribution.** Rank rows by |e_persistence| and split

  ΔSSE = Σ (e_R² − e_P²)

into the part inside the top k persistence rows and the part outside.

## M4 Error versus observed change
Δy_t = y_t − y_{t−1}, computed only within a valid frozen pair (same run, aligned).

The observed recording increment q is the smallest positive difference between distinct recorded values: 0.2 barg for P-2 and 0.01 ln/min for MFC-3.

Bins are fixed as decades of q *before* any error statistic is computed: 0 | 1 q | 2–10 q | 11–100 q | >100 q.

This analysis is retrospective. Δy uses the outcome, so it cannot be used as a deployment gate.

## M5 Resolution and controller role
- **Resolution evidence:** the observed increment, distinct-value counts, on-grid fraction, exact-match rates, and errors expressed in increments.
- **Source search:** the workbook "Sensor Overview" sheets and protocol blocks were searched for instrument resolution or accuracy. **None is documented**, so no manufacturer tolerance is used.
- **Controller role:** taken from the workbook notes ("that back pressure is controlled by MFC-3", "MFC3 is used as back pressure control"). It is tested descriptively by P-2's distribution while MFC-3 = 0 versus MFC-3 > 0.
- **Representative cycles:** the trace windows are the "Representative Cycle" Start/End clock times written in each workbook's protocol block, read before plotting.

## M6 Metadata
The full protocol block above each raw-data header was extracted verbatim (`replay_manifest.json → source_notes`). Conflicts are recorded in TAB_B01 and not corrected.

## M7 Cross-run evidence
There are 3 held-out workbooks from 2 recording dates on one apparatus. Rows are serially dependent, so no row bootstrap, interval or p-value is reported. Stability is described by sign consistency across runs and by each run's share of ΔSSE.

## Environment
- Python 3.12.1, NumPy 2.3.1, scikit-learn 1.7.0, pandas 2.3.3 and Matplotlib 3.10.7, all matching `study_b/requirements.txt` except openpyxl.
- **openpyxl 3.0.10** (a local Anaconda copy placed on `PYTHONPATH`) was used instead of the pinned 3.1.5, because no installation was performed. The bit-identical replay of all counts and metrics shows that the reader produced identical data.
- Figures use Segoe UI, because IBM Plex Sans is not installed.
