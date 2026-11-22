# Independent Verification of Yazan's Tasks Y1–Y8

**Branch:** `audit/preparation-integration` · **Base commit:** `13c55125a2588cfb2708d7c0e58bc9454996b933` (main) · **Date:** 2026-11-10
**Plan used:** `assets/Yazan new plan.pdf`. Its SHA-256 (`6f0a7868…`) is identical to `~/Downloads/Yazan new plan.pdf`. No "Yazan New Plan 2" exists.
**Scope limit:** the raw H2-SimNet archive (`data/raw/`, about 1 GB, Zenodo 17871393) is **not present** in this checkout. So the audit scripts in `audit/` could **not be re-executed**. Everything below comes from (a) reading the scripts, (b) cross-checking Yazan's own committed outputs against each other, and (c) the 4 tracked sample files. Every count quoted here was recomputed from the committed CSVs with pandas; the commands are in `TEST_AND_VALIDATION_REPORT.md` §3.

> **Verdict: the claim that Yazan has completed the whole plan is not supported.** The package is useful and much of the work is real: an inventory with SHA-256 for 265 files, per-file statistics, a pairwise duplicate audit, row-level onset extraction, and a versioned provisional freeze. But two acceptance-critical defects invalidate the evaluation handoff (folds that violate family independence, and a byte-identical scenario on both sides of fold 3). Several Gate-1/2 claims are also contradicted by Yazan's own data. Nothing in Yazan's files was changed. Each correction below needs Yazan's action and review.

## Summary table

| Task | Claimed | Existing evidence | Verified status | Main unmet criteria | Decision |
| --- | --- | --- | --- | --- | --- |
| Y1 Inventory and integrity | COMPLETED | `FILE_LEVEL_AUDIT.csv` (265 rows), `raw_checksums.sha256` (265), `SENSOR_CHANNEL_AUDIT.csv`, `DUPLICATE_EXPORT_AUDIT.csv` (1,423 pairs), `DATASET_INVENTORY.md`, `Y1_AUDIT_LOG.md`, `audit/01_inventory_integrity.py` | PARTIALLY_IMPLEMENTED; outputs present but not re-executable here | Misclassified preliminary claims (Y1-a); a false sampling claim (Y1-b); cross-tree relationship misreported (Y1-c) | **REQUIRES CORRECTION** |
| Y2 Scenario and family construction | COMPLETED | `DATASET_SCENARIO_MAP.csv`, `SCENARIO_RELATIONSHIP_EDGES.csv` (481), reports | NOT SATISFIED | A duplicate scenario was given a separate ID (Y2-a); families are built from filename labels, not evidence (Y2-b); no signal comparison; no Ahmed sample review | **REQUIRES CORRECTION** |
| Y3 Conditions, timing, confounding | COMPLETED | `EVENT_TIMING_AUDIT.csv`, `OPERATING_CONDITIONS_AUDIT.csv`, 2 reports | PARTIALLY_IMPLEMENTED | Phase comes from directory names only, with no signal check (steps 31, 34); report text contradicts its own tables; onset "seconds" are row indices | **REQUIRES CORRECTION** |
| Y4 Labels and mapping | COMPLETED (FROZEN) | Inventory, overlap matrix, `LABEL_MAPPING_SPEC.md`, `class_mapping.yaml` | PARTIALLY_IMPLEMENTED | Inconsistent exclusion of two-leak scenarios; NORMAL rule not mutually exclusive; no Faisal or Ahmed review record before "FROZEN" (step 57) | **NOT FROZEN; review needed** |
| Y5 Feasibility and leakage | COMPLETED | `FAMILY_CLASS_DISTRIBUTION.csv`, `folds.csv` (276), 3 reports | NOT SATISFIED | Families on both sides of every fold; content-duplicate leak in fold 3; no inner splits enumerated (step 66); incomplete leakage pathways | **REJECT FOLDS; redo** |
| Y6 Provenance supply (rest transferred to A10) | IN_PROGRESS (Ahmed) | Checksums, audit CSVs, exclusions, manifest version | Supply side SATISFIED | none on Yazan's side; A10 documents do not exist (Ahmed) | **Yazan part complete** |
| Y7 Readiness decision | COMPLETED (READY_WITH_EXCLUSIONS) | `DATASET_READINESS_REPORT.md` | NOT SATISFIED | The decision rests on Y2/Y5 evidence that fails; it states Ahmed's approval with no approval record | **WITHDRAW; re-issue after Y2/Y5** |
| Y8 Provisional freeze | COMPLETED | `provisional/` (4 files, `v0.1-provisional-2026-10-30`) | SATISFIED for development use, with caveats | Notes repeat false sampling and phase statements; it inherits Y2-a | **USABLE for interface development only** |

Gates (`00_governance/GATE_DECISIONS.md`): Gate 1 = **CONDITIONAL**, Gate 2 = **FAIL / revise**, Gate 3 = **FAIL**. The ledger records all three as PASS.

## Y1: Dataset inventory and integrity

**Verified:**
- Each of the 265 files has one row and one SHA-256.
- All files are marked readable.
- 242 tabular files: 123 CSV and 119 Parquet.
- The 4 tracked `data/sample/*.parquet` files match their `raw_checksums.sha256` entries (A12 validator, 4/4 PASS). So the samples really are unmodified copies of `H2-SimNet-clean/.../anom_gestcent/...` and `normality_gest_center`.
- The duplicate audit is genuinely pairwise and uses a documented tolerance (1e-4).

**Defects:**
- **Y1-a: preliminary claims misclassified.** The inherited claim "121 files; 60 CSV / 61 Parquet; ≈2.42 M rows" is marked **REFUTED**. Yazan's own `FILE_LEVEL_AUDIT.csv` shows that the `H2-SimNet-clean/` subtree contains exactly **60 CSV + 61 Parquet = 121 files and 2,420,000 rows**. The claim describes the curated subtree. It should be **REVISED (scope)**, not refuted, and it is direct evidence about which tree is the canonical release.
- **Y1-b: sampling claim false as stated.** `DATASET_INVENTORY.md` says "All timestamps advance monotonically by exactly 1.0 s … CONFIRMED". In fact:
  - 230 of 242 data files have **no time column**: `time_col = Index_implied_1s` means 1 s was *assumed*.
  - 6 MATLAB normality CSVs have dt = 0.8 s or 0.9 s (25,001 or 22,223 rows).
  - So the 1 s interval is **REPORTED_UNVERIFIED** for most files and **REFUTED** for 6. `PROVISIONAL_DATA_FREEZE_NOTES.md` repeats "strictly 1 Hz".
- **Y1-c: cross-tree relationship misreported.** Every one of the 252 file pairs that share a `Scenario_ID` but sit in different export trees (`H2-SimNet-clean/` vs `anomalous-scenarios/` / `normality-scenarios/` / `MATLAB_SIMSCAPE_Simulation/`) is classed `DIFFERENT_CONTENT` (max sensor difference around 1 MPa). None is equivalent. Equivalence holds only *within* a tree (CSV↔Parquet: 111 numerically equivalent pairs and 10 byte duplicates). The documents say the mirrors "represent identical physical simulation runs". That is false across trees. 57 of 58 Scenario_IDs therefore combine two non-identical data versions. Which tree is canonical is an **open decision** that was never recorded.
- Units MPa and kg/s are correctly labelled VERIFIED_FROM_DOCS, which means reported in documentation, not derived from the data. Treat them as REPORTED. The H₂ fraction is correctly marked REPORTED_UNVERIFIED.

**Reproducibility:** NOT RE-VERIFIED (the raw data is absent). `Y1_AUDIT_LOG.md` records Python 3.14.2 on darwin. Python 3.14 is also why `dashboard.py` worked for the author, although it fails on 3.12.

## Y2: Scenario identification and families

- **Y2-a (CRITICAL): a duplicate became a separate scenario.** `H2-SimNet-clean/anomalous-scenarios/parquet/leakG4.parquet` and `anomalous-scenarios/parquet/leakG4.parquet` (topology "Unknown") are **EXACT_BYTE_DUPLICATE**s of `anomalous-scenarios/parquet/anom_gestup/assestment_transient/leakG4.parquet` (`DUPLICATE_EXPORT_AUDIT.csv`, 0-based data rows 68, 69 and 90, which are file lines 70, 71 and 92). They were still given their own ID, `SCEN_UNKNOWN_UNKNOWN_LEAKG4`. Root cause: `audit/02_scenario_family_mapping.py:116-140` builds Scenario_ID from `(topology, phase, filename stem)` taken from the *path*. It never uses the content evidence from Y1, which breaks plan step 17 ("start from Y1 duplicate classes").
- **Y2-b (MAJOR): families are filename labels.** `extract_event_metadata` (`audit/02…py:30-109`) maps every filename stem to `FAM_<event>`. Families are therefore identical to event labels by construction. Specifically:
  - All 242 map rows have `relationship_confidence = HIGH` and the single `evidence_reference = FORMAT_NUMERIC_AUDIT_Y1`.
  - The 63 `CROSS_TOPOLOGY_IDENTICAL_EVENT_CONFIG` edges are marked `requires_joint_grouping = False`, yet the families group them anyway.
  - No pre-event or initial-state signal comparison exists (step 20).
  - Steps 23–24 prohibit merging on metadata similarity alone.
  - A reviewer cannot reconstruct *why* a family exists beyond the filename, so the acceptance criterion fails.
- No record of Ahmed's sample review (step 28). The relationship between weak and strong variants, and between `start_transient`, `constant_segment` and `assestment_transient` files of the same event, is asserted but not evidenced.

## Y3: Timing, phase, and confounding

- Row-level onset and offset extraction is real and useful (`audit/03_04…py:83-119`). Units are **row indices**, labelled as seconds.
- Phase is taken purely from directory names (`audit/01…py:50-70`: `start_transient` → Initial Ramp-up, `constant_segment` → Steady State, `assestment_transient` → Transient). No metadata-vs-signal agreement was recorded (steps 31 and 34).
- `PHASE_CONFOUNDING_REPORT.md` states that compressor faults occur "predominantly during Initial Ramp-up". Its own table shows CompressorFault = 0 in Initial Ramp-up and 6 in Steady State. The sentence is hard-coded in `audit/03_04…py:283`.
- `LABEL_ANNOTATION_AUDIT.md` gives one onset per label (for example leak_G3 at t = 4000). `EVENT_TIMING_AUDIT.csv` shows leakG3 under `start_transient` with onset 100. Timing differs per file and must be used per file.

## Y4: Labels and mapping

- The inventory and overlap matrix are consistent with each other (58 scenarios).
- Rolling `leak_G3–G6` up into the `Leak` umbrella is supported by the overlap matrix: `Leak` is 1 whenever a location column is 1.
- **Inconsistent exclusion:**
  - `leakG3G5_overlapped` and `leakG5G6_overlapped` contain two simultaneous leaks and no compressor event. They are excluded with reason `COMPOUND_FAULT_RESERVED_FOR_SECONDARY_MULTILABEL`.
  - `leakG3G4_*` and `leakG3G6` are also simultaneous two-leak events but are kept as LEAK.
  - The trigger is the `_overlapped` filename suffix (`variant_type = combined_event`), not the label content.
- The `class_mapping.yaml` NORMAL rule ("label_anomaly == 0 **or** all fault columns == 0") is not mutually exclusive with the fault rules.
- Whether pre-onset rows of fault scenarios count as NORMAL is not decided. That choice changes NORMAL from 1 family to roughly all families, which overturns the Y5 feasibility argument.
- The file is marked `FROZEN_FOR_FAISAL`, but step 57 requires Faisal's technical review and Ahmed's scientific review first. Neither is recorded.

## Y5: Feasibility and leakage

The F4 validator was run read-only against `folds.csv`, using Yazan's own duplicate evidence. Output files: `06_audit_preparation/FOLD_VALIDATION_ISSUES.csv` and `FOLD_VALIDATION_SUMMARY.csv`.

| Fold (test topology) | Families in BOTH train and test | Content duplicate across split | Test scenarios per class (N/L/CF/CD) | Test families per class |
| --- | --- | --- | --- | --- |
| 1 (Downstream) | 9 of 9 | none | 1 / 11 / 2 / 1 | 1 / 6 / 1 / 1 |
| 2 (Center) | 9 of 9 | none | 1 / 11 / 2 / 1 | 1 / 6 / 1 / 1 |
| 3 (Upstream) | 9 of 9 | **`SCEN_UNKNOWN_UNKNOWN_LEAKG4` (train) ≡ `SCEN_UPSTREAM_TRANSIENT_LEAKG4` (test), byte-identical** | 1 / 11 / 2 / 1 | 1 / 6 / 1 / 1 |

- `zero_leakage_assertion_passed = True` checks Scenario_ID intersection only (`audit/05…py:110`). The test `tests/test_dataset_audit.py::test_folds_zero_leakage` checks scenarios and topology only, so it passes while the declared independence unit is violated.
- The "mathematical proof" that LOFO is invalid follows from Y2-b: if family ≡ label, holding out a family removes its class. It is not a property of the data.
- The design reports 17 test and 34 train scenarios per fold; `folds.csv` contains 15 and 31.
- Every scenario appears twice (two trees). Combined with Y1-c, that means two different data versions per scenario.
- No inner (development) grouped splits are enumerated (step 66).
- Leakage pathways listed: 6. Not addressed: shared initial conditions and pre-event segments across weak/strong/phase files, pressure-level fingerprinting, and the duplicate in Y2-a.
- **Scientific consequence:** even after the leak is fixed, NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY each have a single test scenario per fold. Any per-class estimate for them is a single-scenario descriptive observation. Inference at family level is not justified for those classes under any split of this archive unless the label-granularity decision (Y4) changes the picture.

## Y6: Provenance supply

Satisfied on Yazan's side. Checksums, audit CSVs, exclusions and the manifest version string are all present and citable. The A10 documents do not exist yet, and they are Ahmed's responsibility.

## Y7: Readiness decision

`READY_WITH_EXCLUSIONS`, "UNBLOCKED FOR PRIMARY PIPELINE", and "APPROVED FOR SCIENTIFIC PROVENANCE & CLAIMS" (attributed to Ahmed) are **not supported**. Y2 and Y5 fail, and no approval record exists. Under the plan's own outcome vocabulary, the defensible current status is **EXPLORATORY_ONLY** for any model run, or "decision pending" until Y2 and Y5 are corrected. Yazan, Faisal and Ahmed make that call; this audit does not make it for them.

## Y8: Provisional freeze

Versioned (`v0.1-provisional-2026-10-30`), explicitly PROVISIONAL, with unresolved questions listed: the plan's criteria are met for *interface development*. Caveats: the notes repeat the false 1 Hz statement and the inverted phase statement, and the manifest carries Y2-a. Faisal can keep using it for pipeline and interface work; it must not feed any fold-based estimate.

## Minimal corrections requested from Yazan (none were applied on this branch)

1. Assign Scenario_IDs from the content-equivalence classes in `DUPLICATE_EXPORT_AUDIT.csv`. `h2prism.splits.content_equivalence_groups` implements the union-find, read-only. `SCEN_UNKNOWN_UNKNOWN_LEAKG4` then merges into `SCEN_UPSTREAM_TRANSIENT_LEAKG4`.
2. Decide and document the canonical export tree, with evidence: the clean tree matches the 121-file / 2.42 M-row release description. Emit one file per Scenario_ID in the manifest and in the folds.
3. Rebuild families from evidence: signal or initial-state comparison and the parameter-variant relationship. Report conservative and strict views. Do not equate families with labels.
4. Correct the sampling and phase statements. Record onsets in both row and second units.
5. Make the two-leak exclusion rule consistent, and resolve the NORMAL rule and pre-event policy together with Faisal.
6. Regenerate folds and check them with `h2prism.splits.validate_outer_folds` (family, scenario and content-duplicate assertions). Add the family-level assertion to `tests/test_dataset_audit.py`.
7. Re-issue Y7 only after Faisal's technical review and Ahmed's scientific approval are recorded.
