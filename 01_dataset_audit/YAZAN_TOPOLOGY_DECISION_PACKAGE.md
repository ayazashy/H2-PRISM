# Dataset-owner decision package: topology attribution of H₂-SimNet event runs (R-18)

- **Owner:** Yazan (dataset). **Reviewers:** Faisal (technical), Ahmed (scientific).
- **Status:** DECISION REQUIRED.
- **Nothing in the manifest, the labels or the recorded runs has been changed.**
- **Evidence:** `03_results/diagnostics/forensics/` (regenerate with `python tools/experiments/forensic_audit.py --raw-parent data/raw`).

## 1. Finding

The source package contains the MATLAB/Simscape models and the scripts that exported them. Three independent pieces of evidence agree:

| Evidence | Center | Downstream | Upstream |
| --- | --- | --- | --- |
| Sensors logged by the source models (`simulation_model_sensors.csv`) | `*_gest_center.slx`: 10 pressure + 3 flow sensors | `*_gest_down.slx`: 12 pressure + 4 flow sensors (PS11, PS12, MFS4) | `*_gest_up.slx`: 10 pressure + 3 flow sensors |
| Export scripts `save_model_data_{center,down,up}.m` | `normality_gest_center.csv` from `simOutCenter`, 10 + 3 columns | `normality_gest_down.csv` from `simOutDown`, 12 + 4 columns | `normality_gest_up.csv` from `simOutUp`, 10 + 3 columns |
| Released NORMAL files | consistent with the center model | consistent with the down model | consistent with the up model |
| Released EVENT folders (`source_model_attribution.csv`) | `anom_gestcent`: **all 18 runs have PS11/PS12/MFS4 active**, the down-model signature | `anom_gestdown`: **all 18 runs have them as zero-variance padding and PS4 ≈ PS8**, the center-model signature | `anom_gestup`: consistent with the up model |

**Conclusion.** The event folders `anom_gestcent` and `anom_gestdown` carry each other's simulation model. That is **36 of 57 manifest runs, 32 of the 51 eligible runs.**

- The three NORMAL files and all Upstream runs are consistent with their models.
- The defect is in the published release. Our export, manifest and pipeline map the folders exactly as the release names them.
- **This corrects the earlier project statement** (L12 / R-18 of 2026-11-11), which located the inconsistency in the two NORMAL files. Topology is only a grouping label, so both readings give the same two groups of runs. The R2 numbers are therefore unaffected, but the physical attribution was wrong.

**Second, related defect.** Sensors that a model does not have are released as **exact constants**: PS11 ≈ 3.34, PS12 ≈ 2.34, MFS4 = 0, with zero variance even in the noise-added release (`padded_channel_evidence.csv`). 24 of the 128 model features (3 channels × 8 statistics) therefore describe sensors that do not exist in two of the three configurations.

## 2. What is not affected

- Class labels, event timing, scenario identities, families within a topology, run exclusions and window extraction.
- Every run's class is unaffected: the swap moves whole runs between topology groups, never changes a label.

## 3. Effect on the recorded experiment

- **Fold composition.** Under the source-model attribution:
  - the held-out "Center" fold contains down-model events with the center-model NORMAL run;
  - the held-out "Downstream" fold contains center-model events with the down-model NORMAL run.

  Each of these two folds therefore mixes two sensor configurations, and its NORMAL run has a different sensor set from all of its event runs.
- **Errors explained.** This explains 7,972 of the 8,012 R2 misclassifications (99.5%): Center LEAK predicted as NORMAL (7,307) and Downstream NORMAL predicted as LEAK or FAULT (665).
- **No leakage now or after correction.** Families and runs stay disjoint across folds under either attribution, because a correction only moves the two NORMAL runs (equivalently, the 36 event runs) between two topology groups.

## 4. Options for the dataset owner

| Option | What changes | Consequence | Approval needed |
| --- | --- | --- | --- |
| **A. Keep the release attribution** | Nothing | R2 and all sensitivity results stand as recorded. Every report must state L12 (corrected wording) and that Center/Downstream results reflect mixed configurations. No cross-topology generalisation claim | Yazan (decision), Ahmed (claims) |
| **B. Versioned correction (manifest v0.3)** (recommended) | New column `topology_source_model` and corrected `topology` for the 36 event runs. The release column is kept verbatim as `topology_release`. Labels untouched. New manifest hash | A **new protocol version** and a **new authorized primary run**. R2 stays the historical primary of protocol 1.1 and is not overwritten | Yazan (manifest), Faisal (folds and contract), project lead (new run) |
| **C. Ask the dataset authors** | Nothing until answered | Confirms which folder naming is intended before choosing A or B | Yazan |

Independent of A/B/C, the padded channels need a decision.

- **(i)** Restrict cross-topology features to the common sensor set (PS1–PS10, MFS1–MFS3), which would be a new protocol, or
- **(ii)** keep all channels and report the configuration fingerprint as a limitation.

Option (i) is the scientifically defensible one for leave-one-topology-out evaluation.

## 5. Acceptance tests for option B

1. **Consistency:** `source_model_attribution.csv` recomputed on manifest v0.3 has `consistent = True` for 57/57 runs.
2. **Integrity:** every run keeps its `label_mapped`, `eligible_primary` and family. The diff of manifest v0.2 and v0.3 touches only `topology` (36 rows) plus the new columns.
3. **Fold homogeneity:** each outer fold contains a single sensor configuration (`extended_sensors_active` constant within a fold).
4. **Disjointness:** `assert_group_disjoint` passes for family, run and topology in all folds.
5. **Separation of record:** R2 artifacts and hashes are unchanged; the new run is recorded under a new run key and protocol version.

## 6. Decision record (to be completed by the owner)

| Field | Value |
| --- | --- |
| Decision (A / B / C) | |
| Padded-channel decision (i / ii) | |
| Decided by, date | |
| Faisal technical review | |
| Ahmed scientific review | |
