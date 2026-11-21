# Raw Dataset Verification Report: H₂-SimNet against Yazan's Y1–Y8

**Branch:** `audit/preparation-integration` · **Base:** `main` @ `13c5512` · **Date:** 2026-11-10 · **Scope:** verification only. No model was trained and no ML experiment was run.
**Evidence directory:** `06_audit_preparation/raw_verification/`. Candidate corrections are in `06_audit_preparation/candidate_corrections/`.
Every statement below is labelled **CONFIRMED DEFECT**, **RESOLVED DISCREPANCY**, **VALID**, **UNVERIFIED** or **HUMAN REVIEW**.

## 1. Official source and exact version

| Field | Value (from the Zenodo REST API, saved in `raw_verification/ZENODO_SOURCE_PROVENANCE.json`) |
| --- | --- |
| Record | https://zenodo.org/records/17871393 |
| DOI | 10.5281/zenodo.17871393 (concept DOI 10.5281/zenodo.17871392) |
| Title | H2-SimNet Dataset: A Simulation-based Dataset for Anomaly Detection in Hydrogen Blend Transport Networks |
| Version / date / licence | **V2**, published 2025-12-09, CC-BY-4.0 |
| Published file | `H2-SimNet-Dataset.zip`, 509,236,976 bytes, `md5:15bc64a3afc9e2990c9db66eb37617de` |

## 2. Acquisition and checksum verification

- **No new download was needed.** An identical archive already existed at `~/Downloads/H2-SimNet-Dataset.zip`:
  - Size 509,236,976 bytes, equal to Zenodo.
  - MD5 `15bc64a3afc9e2990c9db66eb37617de`, **equal to the Zenodo checksum**.
  - SHA-256 recorded for local provenance: `3886e9457001abe3842d0ca46bb3b744d29ca0c0de50e7a625aa4d5611537c05`.
- Zip CRC test: PASS.
- Extracted with a path-traversal-checked extractor (330 members, 264 files) into `data/raw/H2-SimNet-Dataset/`. That path is gitignored (`.gitignore:51 data/raw/*`). The raw files are only read; none was modified.
- **Reconciliation with Yazan's `raw_checksums.sha256`** (`raw_verification/CHECKSUM_RECONCILIATION.csv`):

| Result | Files | Meaning |
| --- | ---: | --- |
| MATCH | 256 | Yazan's hash equals the official bytes |
| MISMATCH | 8 | `ReadME.txt`, `models_launcher.m` and 6 MATLAB normality CSVs. In every case Yazan's hash is reproduced exactly after converting the official CRLF line endings to LF. **CONFIRMED DEFECT (minor, provenance):** Yazan audited a copy whose text files had been modified (plan: "never alter raw files"). The data content is the same |
| Only in Yazan's list | 1 | `H2-SimNet-Dataset/.gitkeep`, a local placeholder that is not in the archive. Yazan's file count of 265 should be **264** |

## 3. Actual raw inventory (`raw_verification/FILE_STRUCTURE.csv`)

- 264 files: 123 CSV + 119 Parquet (242 tabular), plus Simscape models, MATLAB scripts and documentation.
- Rows per tabular file: 236 files have 20,000 rows; 4 have 22,223; 2 have 25,001.
- Export trees:
  - `H2-SimNet-clean/`: 60 CSV + 61 Parquet = **121 files, 2,420,000 rows**.
  - `anomalous-scenarios/` + `normality-scenarios/`: 57 CSV + 58 Parquet.
  - `MATLAB_SIMSCAPE_Simulation/`: 6 CSV.
- **RESOLVED DISCREPANCY:** the inherited claim "121 files / 60 CSV / 61 Parquet / 2.42 M rows" describes the clean subtree exactly. Yazan's REFUTED label is wrong; it should read REVISED (scope).

## 4. CSV/Parquet duplicate findings

- **VALID:** re-running Yazan's script reproduces `DUPLICATE_EXPORT_AUDIT.csv` exactly by key: 1,423 pairs; DIFFERENT_CONTENT 1,292, NUMERICALLY_EQUIVALENT_EXPORT 113, EXACT_BYTE_DUPLICATE 12, NUMERIC_EQUIVALENT_DIFF_COLUMNS 6 (`raw_verification/AUDIT_RERUN_KEYED_COMPARISON.csv`). Within one tree, each CSV is numerically equivalent to its Parquet.
- **RESOLVED DISCREPANCY (previous ISS-04):** the two trees are **not** different simulations. In all 58 clean-vs-release Parquet pairs (`raw_verification/CROSS_TREE_COMPARISON.csv`):
  - labels are identical (58/58);
  - the residual has a mean of at most 0.004, a median lag-1 autocorrelation of about 0, and the clean file is smoother (57/58).
  The release tree is therefore **the clean simulation plus white noise**, consistent with the dataset ReadME ("Gaussian white noise … added"). Keeping both versions under **one Scenario_ID is correct**. Two things remain wrong: Yazan's description of them as "identical", and loading both versions at once (`folds.csv` lists both), which double-counts every run as noise augmentation.
- **CONFIRMED DEFECT:** `H2-SimNet-clean/anomalous-scenarios/parquet/leakG4.parquet` (inside the clean tree) is byte-identical to the **noisy** release file `anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet` (SHA-256 `d44b4200…` for both). It is a misfiled duplicate of the Upstream transient leakG4 run, not an "Unknown" scenario.
- `leakG5G6_overlapped_noisy` is the same run as `leakG5G6_overlapped` plus noise (labels identical, residual SD about 5×10⁻⁴, no autocorrelation). Yazan's merge into one scenario is **VALID**.

## 5. Sampling and sensors (`raw_verification/TIME_AXIS_AUDIT.csv`)

| Time source | Files | Step |
| --- | ---: | --- |
| Parquet stored index named `Timestamp` | 119 | **exactly 1.0 s** (0 … 19,999) |
| CSV `Timestamp` column (normality, clean and release) | 6 | 1.0 s |
| CSV `Timestamp` column (`MATLAB_SIMSCAPE_Simulation/`) | 6 | 0.8 s or 0.9 s |
| No time information (anomaly CSVs) | 111 | — (each is numerically equivalent to a Parquet that has a 1.0 s index) |

- **RESOLVED / VALID (correction to my earlier ISS-06):** Yazan recorded `Index_implied_1s`, but the Parquet files *store* a 1.0 s time index. So the 1 s sampling is **VERIFIED** for every modelling file, because the Parquet files carry the index and the CSVs are equivalent to them.
- **CONFIRMED DEFECT** in wording only: "all timestamps advance by exactly 1.0 s" is false for the 6 MATLAB CSVs.
- The MATLAB CSVs are raw solver exports: variable step, only PS1–PS10 and MFS1–MFS3, no labels. Interpolated to 1 s, they match the clean normality Parquet to within about 1% of range (PS1 max |Δ| 0.033 MPa on a 3.37 MPa range). They are the same runs and are **not suitable as model input**.
- Channels PS1–PS12 and MFS1–MFS4 are present in all 236 labelled files. The units MPa and kg/s come from the dataset ReadME (REPORTED). No temperature channel exists (**VALID**).
- **UNVERIFIED:** the "10% H₂ / 90% CH₄" composition. It appears in neither the ReadME, the `.m` scripts nor the `.slx` model XML. Only the Zenodo title says "Hydrogen Blend".

## 6. Scenario_ID verification

- **VALID:** re-running `audit/02_scenario_family_mapping.py` on the official data reproduces Yazan's Scenario_ID and family for all 242 files. Only the `duplicate_class_id` numbering differs (36 rows), because it depends on path sort order.
- **CONFIRMED DEFECT:** `SCEN_UNKNOWN_UNKNOWN_LEAKG4` must be merged into `SCEN_UPSTREAM_TRANSIENT_LEAKG4` (section 4). With that fix there are **57 scenarios**, not 58.
- **CONFIRMED DEFECT (portability and determinism):**
  - Paths are written with the OS separator.
  - The "canonical" Parquet in `EVENT_TIMING_AUDIT.csv` and `OPERATING_CONDITIONS_AUDIT.csv` depends on path sort order: 58/58 clean-tree files in Yazan's run versus 3/58 here. Onsets are unaffected because the labels are identical across trees.
  - Yazan's run is otherwise reproducible (`raw_verification/AUDIT_RERUN_COMPARISON.csv`).

## 7. Scenario_Family_ID verification (`raw_verification/PRE_EVENT_SHARED_SEGMENTS.csv`)

Pre-event signals of all 1,830 clean-tree file pairs were compared:
- **0 of 1,260 cross-topology pairs** share an identical pre-event segment. The three withdrawal topologies are distinct simulations.
- **24 within-topology pairs** share byte-identical pre-event segments:
  - weak/strong variants: 2,500–5,000 identical rows;
  - `leakG3` start vs constant segment: 100 rows;
  - leakG4 vs leakG4brokenC1, and brokenC1 vs startdelayC1: 25 rows, i.e. only the initial state.

**CONFIRMED DEFECT:** Yazan's families merge the same event label *across* topologies, and no signal relationship supports that. They also equate family with class, which is what produces the "LOFO is mathematically invalid" conclusion. The within-topology weak/strong grouping is **VALID**. Short shared initial segments (25–100 rows) are recorded as **HUMAN REVIEW** rather than as merges (plan Y2 step 23).

## 8. Label-mapping assessment (`raw_verification/LABEL_CONSISTENCY.csv`; row-level, clean tree)

| Finding | Evidence | Class |
| --- | --- | --- |
| Labels are row-level, onset-based step functions; onsets per file: G3 4000, G4 2500, G5 5000, G6 7000, start-transient leakG3 100, transient leakG4 / G5G6 400, C1 fault and delay 25 | per-file first onset row | VALID (Yazan's timing table is correct) |
| `CompressorDelay` is active only on rows 25–1000 and then returns to 0. The ReadME says anomalies last "until the end of the simulation" | label transitions at rows 25 and 1001 | HUMAN REVIEW (post-event windows would be NORMAL) |
| `leakG5G6_overlapped*` files carry location labels **leak_G4 + leak_G6**, not G5 + G6 | active columns | CONFIRMED annotation/filename mismatch. Yazan's `event_label_raw = Leak_G5_G6` is wrong |
| `brokenC1G5_weak`: `leak_G5` active while `Leak = 0` (39,000 rows across 3 files) | `rows_location_without_leak` | CONFIRMED: refutes Yazan's "Leak is the umbrella of leak_G*". Under the row rules these rows would map to COMPRESSOR_FAULT |
| `leakG4brokenC1`: Leak and CompressorFault active together (59,700 rows) | `rows_multi_type` | VALID exclusion as compound |
| Phase: compressor files are in `constant_segment/` but their onset is t = 25 (ramp-up per ReadME); Yazan's directory-derived phase = "Steady State" | onset vs directory | CONFIRMED DEFECT (phase metadata) |
| Two-leak files: `_overlapped` ones excluded, others kept | provisional manifest | CONFIRMED inconsistency. Candidate rule: treat every multi-location, single-type leak as LEAK (alternative: exclude all), pending review |

## 9. Original vs candidate folds

| | Yazan `folds.csv` | Candidate `CANDIDATE_FOLDS_LOTO.csv` |
| --- | --- | --- |
| Design | 3 folds, test = one topology | 3 folds, test = one topology (same idea) |
| Family definition | Event label, spans topologies | Strict: within-topology components of evidenced dependence. Conservative: whole topology |
| Family overlap train/test | **9/9 families in every fold** | **0** (both views) |
| Byte-identical data across split | **Yes, fold 3** | **No** (misfiled duplicate merged into its Upstream scenario) |
| Files per scenario | 2 (clean + noisy, both loaded) | 1 scenario row carrying both paths; **exactly one version to be used (Faisal)** |
| Eligible scenarios | 46 (15 test / 31 train) | 51 (17 test / 34 train) |
| Inner development splits | not enumerated | Leave-one-topology-out inside outer-train: 2 per fold; all 4 classes in every inner train (`CANDIDATE_INNER_SPLITS.csv`) |
| Validator result | FAIL (`FOLD_VALIDATION_ISSUES.csv`) | **No issues** (`CANDIDATE_FOLD_VALIDATION_ISSUES.csv` is empty) |

Honest counts (`CANDIDATE_CLASS_FAMILY_COUNTS.csv`):

| Class | Scenarios | Strict families | Scenarios / families per test fold |
| --- | ---: | ---: | --- |
| NORMAL | 3 | 3 | 1 / 1 |
| COMPRESSOR_DELAY | 3 | 3 | 1 / 1 |
| COMPRESSOR_FAULT | 6 | 3 | 2 / 1 |
| LEAK | 39 | 30 | 13 / 10 |

Excluded: 3 × `leakG4brokenC1` (compound) and 3 × `brokenC1G5_weak` (annotation inconsistent, pending review).

**Restriction:** NORMAL, COMPRESSOR_DELAY and COMPRESSOR_FAULT have one independent run (or one weak/strong pair) per topology. Per-class results for them are **descriptive only**, and cross-family inference for these classes is **infeasible** with this archive. Pooled window-level numbers must not be presented as generalisation evidence.

## 10. Leakage findings and status

| Finding | Status |
| --- | --- |
| Family overlap in every fold (original) | CONFIRMED on raw data; candidate fix produced; **awaiting approval** |
| Byte-identical scenario in train and test, fold 3 (original) | CONFIRMED (identical SHA-256); candidate fix produced; awaiting approval |
| Double loading of clean and noisy versions of one run | CONFIRMED; the candidate keeps one row per scenario; version choice pending (Faisal) |
| Within-topology weak/strong dependence | Handled in both the original and the candidate (same fold) |
| Cross-topology dependence | Not found (0 shared segments); topology hold-out is a test of generalisation to an unseen network configuration |
| Leakage through preprocessing, calibration, D reference or thresholds | Guarded in code (runner and policy assertions); not exercised on real data (out of scope) |

## 11. Independent verification of Y1–Y8 (with raw data)

| Task | Verdict | Basis |
| --- | --- | --- |
| Y1 | **Reproducible; partially correct.** Counts, hashes (256/264 exact; 8 differ only by CRLF→LF) and the duplicate audit are VALID. Defects: modified raw copy; 265 vs 264; 121-claim misclassified; "identical" cross-tree wording; time index missed | Sections 2–5 |
| Y2 | **Not satisfied:** duplicate Scenario_ID; cross-topology families without evidence. Weak/strong grouping VALID | Sections 6–7 |
| Y3 | **Partial:** onset table VALID; phase metadata wrong for compressor files; CompressorDelay offset not reported | Section 8 |
| Y4 | **Not frozen:** G5G6↔G4G6 mismatch; "Leak umbrella" refuted; inconsistent compound rule; NORMAL / pre-event policy undecided | Section 8 |
| Y5 | **Not satisfied:** fold leakage confirmed on raw data; no inner splits | Sections 9–10 |
| Y6 | Supply side satisfied (with the CRLF provenance caveat) | Section 2 |
| Y7 | **READY_WITH_EXCLUSIONS not supported** by the evidence | All |
| Y8 | Usable for interface development only; carries the defects above | — |

**Overall:** Yazan's audit is real, deterministic and largely reproducible, but it is **not complete or correct for evaluation purposes**.

## 12. Remaining scientific limitations

- Only 3 independent runs each for NORMAL and COMPRESSOR_DELAY.
- Simulated data only, with no field validation.
- Composition unverified.
- Phase is confounded with event type by design (compressor events at t = 25, leaks at t ≥ 100–7000).
- Onset positions are fixed per event type, so time-in-run is a potential shortcut. Windows must not carry absolute time.
- Absolute-level fingerprints across topologies are untested.
- The clean vs noisy choice changes the difficulty of the task.

## 13. Recommended corrections requiring Yazan's approval

1. Merge the misfiled root `leakG4` files into `SCEN_UPSTREAM_TRANSIENT_LEAKG4`, and set the file count to 264.
2. Re-hash from the untouched archive (CRLF preserved) and record the archive MD5/SHA-256.
3. Describe the trees as "clean simulation" vs "noise-added release of the same runs"; mark the MATLAB CSVs as raw solver exports that are not modelling input.
4. Replace label-based cross-topology families with evidence-based within-topology families (candidate provided), or justify the merge with evidence.
5. Correct the phase metadata for compressor files; report the CompressorDelay offset (row 1000).
6. Record the annotation anomalies (G5G6 file labelled G4+G6; `brokenC1G5_weak` without `Leak`) and decide their eligibility.
7. Apply one consistent multi-location leak rule.
8. Make the scripts OS-portable: POSIX paths, a deterministic canonical-file rule, and `newline=""` hashing of untouched bytes.
9. Withdraw READY_WITH_EXCLUSIONS until items 1–7 are reviewed.

## 14. Decisions requiring Faisal's technical approval

1. Evaluation design: leave-one-topology-out (candidate) or another family-disjoint design.
2. Data version for modelling: clean or noisy release (one, never both).
3. Label granularity (row-level labels exist) and the pre-/post-event window policy, including post-delay rows.
4. Treatment of NORMAL / DELAY / FAULT as descriptive-only classes, or a reduced task definition.
5. Inner split scheme (candidate: leave-one-topology-out inside outer-train).
6. Strict vs conservative family view for any resampling-based uncertainty.

Ahmed: review the scientific implications (claim restrictions in section 12; descriptive-only classes; composition wording).

## 15. Dataset-readiness verdict

- **Raw data:** the official archive (V2) is **intact and verified**.
- **Yazan's package:** **not approvable** as a final dataset freeze.
- **Candidate corrections:** they show that a **leakage-free, family-disjoint grouped design is feasible**, with class coverage reported honestly.

Status: **READY FOR OWNER REVIEW OF CANDIDATE CORRECTIONS, NOT READY FOR PRIMARY EXPERIMENTS.**

## 16. Exact next actions before primary experimental execution

1. Yazan reviews `candidate_corrections/` and accepts or amends items 13.1–13.8, then issues a versioned manifest (v0.2) and re-issues Y7.
2. Faisal decides items 14.1–14.6 and writes `configs/frozen_evaluation_config.yaml`. The folds must pass `validate_outer_folds`.
3. Ahmed approves the scientific implications and the frozen configuration (Gate 3), and re-records `GATE_DECISIONS.md`.
4. Only then, with the user's authorisation: build the feature table (F3) and run development-only work (F5–F9) before any outer-test evaluation.

### Commands executed (all read-only on raw data)
`curl …/api/records/17871393` (metadata) · `md5sum`/`sha256sum` of the archive · `safe_extract.py` · `sha256sum` of 264 extracted files · `audit/run_all_audits.py` in an isolated scratch copy (junction to `data/raw`; the repo's `01_dataset_audit/` is untouched) · `raw_verification/investigate_raw.py` · `raw_verification/build_candidate_corrections.py` · `pytest` (128 passed, 2 skipped; raw-dependent loader tests now pass).
