# H₂-PRISM: Final Audit and Readiness Report

Branch `audit/preparation-integration` (from `main` @ `13c5512`). Uncommitted; nothing pushed.

## Verdict

**Ready for controlled development: yes. Ready for primary experiments: no.**
- The repository now has a tested, leakage-guarded preparation pipeline (F3–F9 primitives and A12–A16) and an honest results folder.
- The dataset handoff it depends on is not acceptable as it stands:
  - the outer folds put every Scenario_Family_ID on both sides of every split;
  - fold 3 contains byte-identical data in train and test;
  - the families themselves are filename labels rather than evidenced relationships.
- Yazan's claim that the whole plan is complete is **not supported**. RQ1 and RQ2 remain open research questions; **no result of any kind exists**.

## Key findings

1. CRITICAL: fold leakage at the family level and at the content level (ISS-01, ISS-02).
2. CRITICAL: fabricated figures and KPIs were committed as results. They are now quarantined (ISS-03).
3. MAJOR: the two export trees differ in content but share Scenario_IDs (ISS-04). The "121 files" claim was misclassified (ISS-05). The sampling claim is false as stated (ISS-06).
4. MAJOR: gate PASS records and "approved by Ahmed & Faisal" statements have no supporting evidence (ISS-11).
5. MAJOR (scientific): each test fold holds a single scenario for NORMAL and COMPRESSOR_DELAY and two for COMPRESSOR_FAULT. Per-class family-level inference is not justified for those classes (ISS-20).

## Claims needing qualification (input for A7)

| Claim (location) | Classification | Required evidence or correction |
| --- | --- | --- |
| "zero scenario or topology leakage … Scenario_Family_ID independence unit" (README §7, Y5/Y7) | UNSUPPORTED | Family-disjoint, content-disjoint folds |
| "Mathematically proven: LOFO invalid / 3-fold topology CV feasible" | UNSUPPORTED as stated | Evidence-based families; feasibility re-evaluated |
| "Sampling strictly 1 Hz" | REFUTED for 6 files; UNVERIFIED for 230 | Per-file time source |
| "10% H₂ / 90% CH₄, Simscape R2025a" | REPORTED_UNVERIFIED | Dataset documentation citation |
| "Peer-reviewed H2-SimNet" (README) | PENDING VERIFICATION | Citation of the publication |
| Figures 3–6 and dashboard KPIs | FABRICATED → quarantined | Real F5/F6/F10 outputs |
| D(x) adds value beyond C/M/H (RQ1) | PENDING (hypothesis) | F10/F11 with family-level uncertainty |
| Selective policy produces meaningful three outcomes (RQ2) | PENDING (hypothesis) | F9/F10 outputs |
| Leak G3–G6 labels give localisation | UNSUPPORTED as metric localisation (correctly stated in README) | n/a |

## Remaining work (blocked, deferred, or awaiting approval)

- **Blocked:** F4 design and frozen config; F5–F7 execution; F10 and F11; A14–A16 execution; A3, A8, A11.
- **Not started:** F10 meta-model and runner; F11 statistics; A1, A2, A7, A10 documents; risk registers (ISS-15).
- **Approval-dependent:** every item in `TEAM_HANDOFF_MATRIX.md`.
- **Unverified:** the Y1 outputs against the raw archive (raw data absent); `download_data.py` and `setup_data.py` (not run).

## Next execution sequence

| Track | Now (can run in parallel) | After the Y corrections |
| --- | --- | --- |
| Yazan | Y-1 (content-based Scenario_IDs), Y-2 (canonical tree), Y-4 (sampling/phase text), Y-6 (family assertion in tests) | Y-3 families, then regenerated folds, then re-issued Y7 |
| Faisal | Review F3/F7/F9 code; decide `label_mode`, `pre_event_policy` (with Yazan) and window/stride; F12 contract amendments; meta-model design | F4 decision and frozen config; build the feature table; development runs |
| Ahmed | A-1 (README / figure spec), A-2 (gate ledger), A4 review, A10 provenance draft from the existing evidence | A3 dataset description; submit A14–A16 for acceptance |

**Single most important next action:** Yazan rebuilds Scenario_IDs from the content-equivalence evidence and picks one canonical export tree. Then the folds are regenerated and checked with `h2prism.splits.validate_outer_folds`. Every downstream experiment depends on this.

## Final readiness gates

| Question | Answer |
| --- | --- |
| Is Yazan's data audit genuinely complete? | No. Y6 (supply side) and Y8 (development use) are satisfied; Y1, Y3 and Y4 need correction; Y2, Y5 and Y7 are not satisfied |
| Is the final dataset approved? | No. Only a provisional package exists; `class_mapping.yaml` was never reviewed |
| Are the grouped splits scientifically defensible? | No. Families appear on both sides of every fold, and fold 3 has a content leak |
| Is baseline preparation complete? | The code is complete and tested on synthetic data. Execution is blocked by F3/F4 |
| Is D(x) implemented correctly? | It matches the written definition and passes 17 hand-calculated and property tests. Its design parameters are undecided and it has not been run on project data |
| Are Ahmed's supporting components ready? | A12 and A13 are implemented, tested and executed (A13 as a clean failing dry run). A14–A16 are implemented and tested; Faisal's acceptance is pending |
| Are the experiment interfaces compatible? | Yes within the new code (one shared runner and one prediction schema). `interface_contracts.yaml` still needs the proposed amendments |
| Can primary experiments begin? | **No** |
| Which approvals remain? | Yazan corrections; Faisal acceptance of F3–F9 and A12–A16 plus the F4 freeze; Ahmed approval of the frozen config, the Y4 mapping and the gate re-records |
