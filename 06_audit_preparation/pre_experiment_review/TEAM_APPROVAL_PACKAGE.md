# Team Approval Package: CANDIDATE_NOT_APPROVED

No approval has been recorded for anyone. Each item names the evidence to review and the decision required.

## Yazan: dataset authority

| # | Decision | Evidence | Options |
| --- | --- | --- | --- |
| Y-A | Accept the run/realization model (57 runs; clean, noise-added, noisy-variant, solver-export and misfiled realizations) | `DATASET_RECONCILIATION_REPORT.md`, `CANDIDATE_FILE_INVENTORY.csv` | accept / amend |
| Y-B | Accept the Scenario_ID scheme and the merge of the misfiled leakG4 copies into the Upstream transient run | `FAMILY_RELATIONSHIP_EVIDENCE.csv` (MISFILED_BYTE_IDENTICAL_COPY) | accept / amend |
| Y-C | Choose a family view as the dataset definition: primary (45), extended (35) or conservative (3); resolve the 19 short-segment relationships | `CANDIDATE_FAMILY_MAP.csv`, `EVALUATION_FEASIBILITY_REPORT.md` §1 | primary / extended / conservative |
| Y-D | Rule on the label conflicts L1 (G5G6 file labelled G4+G6), L2 (brokenC1G5_weak), L3 (delay offset at 1000 s) | `LABEL_AND_TIMING_CORRECTIONS.md` | per item |
| Y-E | Replace folder-derived phase with verified onset plus documented phase | same, L4–L5 | accept / amend |
| Y-F | Issue v0.2 of the manifest and re-issue the Y7 readiness decision; keep v0.1 traceable | — | — |
| Y-G | Fix portability in `audit/` (or adopt `dataset_manifest.py`) | `CROSS_PLATFORM_REPRODUCIBILITY.md` | — |

## Faisal: technical and experimental authority

| # | Decision | Evidence |
| --- | --- | --- |
| F-A | Modelling realization: clean or noise-added (exactly one, fixed before any run) | `DATASET_RECONCILIATION_REPORT.md` §3 |
| F-B | Evaluation design: candidate leave-one-topology-out, or another family-disjoint design; inner scheme (`LOTO_within_train` or `grouped_by_family_primary_k3`) | `CANDIDATE_OUTER_FOLDS.csv`, `CANDIDATE_INNER_FOLDS.csv`, `EVALUATION_FEASIBILITY_REPORT.md` |
| F-C | Window length, stride and `min_samples`; `label_mode = row_level`; pre/post-event policy (joint with Yazan and Ahmed) | `CANDIDATE_LABEL_MAPPING.yaml` `open_decisions` |
| F-D | Treatment of the descriptive-only classes in the primary comparison (pooled vs per-class reporting) | Feasibility report §2, §5 |
| F-E | D(x) design (k given 26–34 training runs per fold, weighting, flags, scenario balancing) | `02_methodology/D_STATISTIC_IMPLEMENTATION_SPEC.md` |
| F-F | Accept the `io.build_time_axis` index fix and the new `dataset_manifest.py` module; write `configs/frozen_evaluation_config.yaml` | `MODEL_INTERFACE_COMPATIBILITY.md` |

## Ahmed: scientific authority

| # | Decision | Evidence |
| --- | --- | --- |
| A-A | Final class definitions: is a multi-location leak still LEAK; are post-delay rows NORMAL; compound events exploratory only | `CANDIDATE_LABEL_MAPPING.yaml`, L3/L6/L7 |
| A-B | Accept the estimand "generalisation to an unseen withdrawal topology" and its limits (3 topologies; descriptive-only classes) | Feasibility report §4–5 |
| A-C | Claim restrictions: RQ1 is pooled and LEAK-dominated; RQ2 exploratory; no localisation, field or pure-H₂ claims; H₂ fraction unverified | Feasibility report §5; `../RAW_DATASET_VERIFICATION_REPORT.md` §5 |
| A-D | Re-record Gates 1–3 in `00_governance/GATE_DECISIONS.md` from this evidence | — |
| A-E | Correct README / `FIGURE_SPECIFICATION.md` (still describe quarantined fabricated figures and the old folds) | `../SCIENTIFIC_AND_TECHNICAL_ISSUES.md` ISS-03 |
