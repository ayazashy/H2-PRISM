# H₂-PRISM forensic findings report

- **Date:** 2026-11-11.
- **Scope:** diagnostic only. No new real-data experiment, no protocol change, no archived output modified.
- **Evidence:**
  - `03_results/diagnostics/forensics/`, produced by `tools/experiments/forensic_audit.py` and `tools/experiments/reproduce_offset_fold3_development.py`;
  - `03_results/diagnostics/PRIMARY_a10530f1fcf2/`.
- **Companion documents:** `06_audit_preparation/forensics/ROOT_CAUSE_REGISTER.csv` (FA-01 … FA-15) and `REMEDIATION_MATRIX.csv`.

## 1. Verified baseline

| Item | Verified state |
| --- | --- |
| Commits | HEAD `6f768a2`; R2 exact code `0a0a9e2` |
| Config | `f788b6d8…` |
| Runs | R2 `a10530f1fcf2` COMPLETED/VALID; R1 `db9acd23ef58` archived INVALID; 7 sensitivity/robustness runs VALID; `offset_invariant_features` incomplete |
| Hashes | all 10 output hash lists re-verified (R1 archive and every run) |
| Authorizations | 2 primary and 8 per-run sensitivity files, all passing the unchanged gate |
| Team plan | 58 requirements: 37 COMPLETE, 13 COMPLETE_WITH_LIMITATION, 7 BLOCKED_EXTERNAL_APPROVAL, 1 NOT_APPLICABLE |

**Method check:** the forensic tracer reproduces R2's stored D(x) and support flags **exactly for all 27,993 windows**. Every neighbourhood statement below therefore describes what the registered run actually computed.

## 2. The topology defect (FA-01, FA-02): what is affected

**Where the defect is.** The source package contains the simulation models and the scripts that exported them.

- Only the two `*_gest_down.slx` models log PS11, PS12 and MFS4 (12 pressure + 4 flow sensors). The center and up models log 10 + 3.
- The export scripts write each NORMAL file from its own model's output (`simOutCenter` → `normality_gest_center.csv`).
- In the release:
  - all 18 runs in the event folder `anom_gestcent` have the extended sensors **active**;
  - all 18 runs in `anom_gestdown` have them as **zero-variance padding** and the center-model PS4 ≈ PS8 signature.

**Which records.** 36 of 57 manifest runs (32 of 51 eligible) carry the other topology's simulation model: every Center- and Downstream-labelled **event** run. The three NORMAL runs and all Upstream runs are consistent.

**Where the error originates.** In the release's event-folder naming. It is **not** in our filenames, export or manifest code, and not in sensor mapping. The ReadME defines the topologies by withdrawal point (down, center, up) and does not resolve which folder is intended. Only the dataset authors can confirm it.

**Correction of the earlier project statement.** The first version of L12/R-18 said the two NORMAL files were swapped.

- Topology is only a grouping label, so both readings yield the same two groups. R2's numbers are unchanged.
- The physical attribution was wrong, and it is now corrected in L12, R-18 and the findings report, with explicit notes.

**Does the current assignment represent the simulated network?** No, for Center and Downstream. Each of these two folds mixes two sensor configurations, and its NORMAL run has a different sensor set from all of its event runs.

**Is the 7,972 / 8,012 association causal?** The evidence is mechanistic, not only correlational:

1. The errors occur only in the two folds the mechanism predicts, and in exactly the predicted direction: Center LEAK → NORMAL (7,307) and Downstream NORMAL → LEAK or FAULT (665).
2. The consistent fold (Upstream) is 100% correct.
3. Neighbour tracing shows that 85% of Center-LEAK and 99% of Downstream-NORMAL neighbours come from the same source model.
4. In the offset-invariant development reproduction, cross-prediction between Center and Downstream gets **0 of 18,662** windows right: classes invert exactly as the mechanism predicts.

Experimental confirmation requires a run on corrected data (option B), which needs approval.

**Other records with the same mechanism:**

- None beyond the 36 event runs: all 57 runs were fingerprinted.
- A second defect shares the root: absent sensors are released as exact constants (PS11 ≈ 3.34, PS12 ≈ 2.34, MFS4 = 0, zero variance even with "noise added"). That makes **24 of the 128 features** pure configuration fingerprints.

**Would correcting the map alter train/test composition or leak?**

- It moves runs between the Center and Downstream groups, so fold composition changes. That is a new protocol version, never a revision of R2.
- Families, runs and topologies stay disjoint, so no leakage is introduced.
- Labels are untouched.

Decision package: `01_dataset_audit/YAZAN_TOPOLOGY_DECISION_PACKAGE.md`.

## 3. Independent support (FA-03)

- **Counts:** 27,993 windows come from 51 runs, 39 families and **17 scenario ancestors**. Per class: NORMAL 1 ancestor, DELAY 1, FAULT 2, LEAK 13.
- **Pseudo-independent support:**
  - 1,260 of 16,009 flag-free windows (7.9%) pass the "≥ 2 families" safeguard only because the same scenario is simulated in two topologies;
  - this covers all 658 Center FAULT windows, 25 of 30 Center DELAY and 573 of 6,083 Downstream LEAK;
  - the 30 wrong Center DELAY → FAULT SPECIFIC decisions are supported by `BROKENC1_STRONG` in Downstream and Upstream: one scenario counted twice.
- **Is the support scientifically defensible?** Only for LEAK, and only within the three simulated configurations. For NORMAL and DELAY, "independent support" cannot exist in this dataset, whatever the code does.
- **Requires new simulations, not code:** at least 3 independently parameterised scenarios per thin class (proposal Section 2).
- **Code or protocol can do:** count support at ancestor level (candidate P2-C). Prospective only; the family map is not changed to increase coverage.

## 4. What D(x) measures (FA-04, FA-05, FA-06)

**Implementation, verified against the specification:**

- z-scores with reference-only mean and SD;
- Euclidean k = 25 nearest reference windows, tie-inclusive, excluding the query's family;
- uniform class shares q;
- D = q₍₁₎ − q₍₂₎.

No implementation defect was found:

- class alignment is correct;
- calibration does not enter D;
- prior correction behaves as specified.

**Why D ≈ 0.97 on wrong Center windows.** D measures **agreement within the reference neighbourhood**, not separation between event hypotheses.

- A Center LEAK window comes from the down model and shares its sensor configuration only with the down-model NORMAL run in the reference.
- 85% of its neighbours come from that run, so q_NORMAL ≈ 1 and D ≈ 1.
- The extended channels contribute 28–65% of the squared neighbour distance for Center event queries (LEAK 28%, FAULT 55%, DELAY 65%; NORMAL about 0%).

**Dependence on confidence:** moderate in Downstream (Spearman 0.69), weak elsewhere (below 0.2).

**Saturation:** D can only take multiples of 1/25. D = 1 for 86%, 75% and 67% of windows across the three folds, so D barely ranks windows.

**When a high D(x) is trustworthy.** All of the following must hold:

1. **Same configuration:** the reference contains windows of the query's own sensor configuration and generating model.
2. **Correct labels:** the reference labels and their topology attribution are correct.
3. **Independent support:** the top class is supported by ≥ 2 independent scenario *ancestors*, not cross-topology replicas.
4. **Agreement:** the D top class equals the classifier's label.

R2 violates (1)–(2) for Center and Downstream and (3) for thin classes. Condition (4) is not checked by the policy at all:

- 2,938 flag-free windows disagree with the classifier;
- every one of the 1,061 flag-free Center LEAK errors is among them, with the neighbourhood pointing to the **true** class.

**Where the safeguards work and where they fail:**

- They catch misleading support from a single run: 85% of Center LEAK errors are flagged.
- They miss misleading support spread over several runs of a mismatched configuration: 650 of 665 Downstream NORMAL errors are unflagged.

**Conclusion:** D(x) is not defective; it behaves exactly as specified. Its specification simply does not cover configuration shift or mislabelled reference data.

## 5. RQ1 non-estimability (FA-07)

The coverage limits were reproduced independently (42/42 matches in the earlier diagnostics; `rq1_binding_constraints.csv`).

| Constraint | Evidence |
| --- | --- |
| Test coverage ceiling = flag-free share | Center 0.258, Downstream 0.722, Upstream 0.736. Identical for all six methods, so comparator eligibility never binds |
| Class ceilings | FAULT and DELAY are never flag-free in Downstream or Upstream; LEAK 0.83–0.85 in Downstream/Upstream but 0.145 in Center; NORMAL 0.97–0.99 |
| Development vs test | development attainability is 0.569 / 0.000 / 0.070 by fold, so threshold transfer is impossible in every fold |
| Discrete ranking / ties | not binding for estimability. At 0.60 in Upstream, 75% of the s_C−D selection is decided by the tie key; 20 alternative salts give identical risk (0.000) |

**Classification: E.** It is a combination of:

- **(B)** conservative safeguards, working as designed;
- **(C)** targets of 0.80 and 0.90 that exceed what 1–2 runs per thin class can support;
- **(D)** a design problem: threshold transfer needs a cross-topology development reference that the inner design cannot supply, and the topology defect (FA-01) depresses Center further.

It is **not (A)**: no implementation defect was found. The registered targets are unchanged. Any lower-coverage study is either exploratory (as reported) or part of a new prospective protocol whose targets are fixed by a development-only pilot (P2-E).

## 6. RQ2 decision quality

All counts below come from window-level decisions.

- **Registered 0.60:** Downstream and Upstream only; Center is absent because 0.60 is unattainable there.
  - SPECIFIC decisions: LEAK 10,701 of 14,614, NORMAL 497 of 1,330; all correct.
  - FAULT 0 of 2,656; DELAY 0 of 62.
- **Root causes of non-SPECIFIC outcomes** (`decision_root_causes.csv`):
  - support flags for all FAULT (2,656) and DELAY (62), and 2,308 of 3,913 LEAK;
  - the matched-coverage cut for 1,605 LEAK and 801 NORMAL.
  - Fig. 4(c) shows "single candidate rejected" because the runner keeps only the first reason token (FA-11).
- **The 989 wrong Center LEAK SPECIFIC decisions** (exploratory 0.25, `rq2_error_anatomy.csv`):
  - **Why eligible:** they are flag-free. Their top class (LEAK) is supported by two Upstream LEAK runs: 2 families, 2 ancestors.
  - **What drove them:** at 0.25, Center selection takes 97% of the flag-free pool, so scores barely matter. These windows actually rank low on s_C (mean percentile 0.14).
  - **Neither D nor confidence reinforced the error:** mean confidence 0.56; D's top class was the correct one. The error is the classifier's, issued because the policy does not check agreement.
- **"Easier cases":**
  - High selective correctness comes mostly from the flag-free pool. It excludes thin classes, and on Center it shifts the mix from 78% LEAK in the population to 42% LEAK and 28% FAULT (FAULT recall 99.8%).
  - On Downstream, s_C and s_C−D both exclude the 665 wrongly predicted NORMAL windows, while confidence includes them. **That advantage belongs to the meta-model, not to D.**
- **Scientifically meaningful reasons:** support-flag reasons are meaningful for thin classes. "Score below cut" is an artefact of the matched-coverage rule. "Single candidate rejected" is a consequence, not a cause.

## 7. The incomplete offset-invariant analysis (FA-08)

- **Error path:** `fit_combined_score` raises when all usable development rows share one correctness outcome. `logit(C)` is clipped at 1e-6, so confident rows are not lost: that hypothesis was tested and refuted.
- **Development-only reproduction:** fold 3 (development = Center + Downstream, offset-invariant statistics) gives **0 of 18,662 correct**:
  - Center events and Downstream events are predicted NORMAL;
  - both NORMAL runs are predicted LEAK (Downstream's partly FAULT).
- **Verdict:** a **valid degeneracy** of the development data caused by FA-01 and FA-02, under which the registered meta-model is mathematically undefined. It is not a numerical or software defect, and the registered experiment is infeasible on this data.
- **Can be fixed as engineering (with Faisal's approval):** record s_C/s_C−D as `NOT_ESTIMABLE (META_MODEL_UNDEFINED)` for the fold and let the other comparators complete (P2-F). Never substitute a fallback score, which would silently redefine the analysis.

## 8. Sensitivity evidence integrated

Seven valid runs plus the incomplete one. Only analyses on the same windows are compared quantitatively.

| Persistent under every comparable variant | Variant-dependent |
| --- | --- |
| Registered RQ1 NOT_ESTIMABLE (all 7 complete runs) | Attainable coverage: k = 10 and prior correction lower it; k = 50 raises it slightly; clean realization collapses it (0.105 / 0.328 / 0.128) |
| Center failure: 0.213 in k_10, k_50, prior_correction, extended_family_map and windows_60_60 | Center accuracy in the different-population or different-realization runs: 0.249 (pre-event NORMAL), 0.378 (clean), 0.035 (offset-invariant) |
| Calibration "none" in all 24 completed folds | Exploratory pooled risks at 0.25: reproduced by k_50, windows_60_60 and extended_family_map; not attainable in the others |
| Topology defect (FA-01) and padding (FA-02) | — |

No variation reverses any conclusion, and none was selected for being favourable.

## 9. Statistical challenge (FA-14, FA-15)

**Dependence and units:**

- Lag-1 autocorrelation of window features is 0.93–1.00, and windows overlap by 50%, so windows are not units.
- The bootstrap uses 39 families in 3 strata. Families are not independent across strata: they are 17 ancestors.
- With 3 topologies, one of which is compromised by FA-01, intervals are conditional descriptions, not generalisation intervals.

**Multiplicity:** 60 registered and 50 exploratory contrasts, with no adjustment. Under the SAP this is acceptable only because no significance claim is made.

**Post hoc:**

- The calibration rule was added after inspecting R1's outer-test output.
- The exploratory coverage grid was chosen after seeing non-estimability.
- Both are disclosed.

**Effect direction:** verified. The difference is s_C minus the comparator, so negative favours s_C.

**Reproducibility vs validity:**

- Software reproducibility is established: exact D and flag reproduction, 42/42 recomputations, hash-verified runs, and a passing test suite.
- Scientific validity of cross-topology conclusions is **not** established, because of FA-01, FA-02 and FA-03.

## 10. Impact map

| Item | Status after this audit |
| --- | --- |
| **RQ1** | Unanswerable under protocol 1.1. The exploratory contrasts are inconclusive and partly the meta-model's effect, not D's. They cannot be interpreted on Center or Downstream because of FA-01 |
| **RQ2** | Selective correctness holds only for Downstream/Upstream LEAK and Upstream NORMAL. The policy fails silently under configuration mismatch (FA-06) and does not check D/classifier agreement (FA-05). Thin-class outcomes are dictated by support limits |
| **D(x)** | Correct implementation of an agreement statistic. It is trustworthy only under the four conditions of Section 4, and no incremental value is demonstrated |
| **Manuscript** | Cannot claim D(x) value, cross-topology generalisation or a reliable policy. It can report a rigorously executed negative or non-estimable study and a documented dataset defect. It requires the R-18 decision first: under option B, the R2 results become historical and a protocol 2.0 run is needed |

## 11. Final verdict

**What is genuinely broken:**

1. The release's topology attribution of 36 event runs (FA-01).
2. Padded constant channels (FA-02).
3. Three reporting defects:
   - RQ2 scope not shown (FA-10);
   - reason truncation in Fig. 4(c) (FA-11);
   - registry labels (FA-12, **fixed**).
4. The project's own earlier attribution of the swap (FA-13, **fixed**).

**Working as designed:** the runner, the authorization gate, calibration (after the R1 fix), the D(x) computation, the support flags, PA-1 selection, the bootstrap, and the fail-closed stop of the offset-invariant run.

**Scientifically unsupported:**

- incremental value of D(x);
- a reliable policy under shift;
- cross-topology generalisation;
- independent support for NORMAL, DELAY and FAULT;
- any significance claim;
- any conclusion from Center or Downstream until R-18 is resolved.

**Fixable without changing the protocol:**

- FA-12 and FA-13 (done);
- documentation items FA-04, FA-06 and FA-15 (done in this report);
- FA-10 and FA-11, reporting changes that need Faisal's contract approval;
- FA-08, fail-closed engineering that needs Faisal's approval.

**Requires a new prospective protocol:** FA-01 (corrected grouping), FA-02 (common sensor set), FA-03 (ancestor units), FA-05 (agreement rule), FA-07 (pilot-fixed targets), FA-09 (finer scores).

**Requires new independent data:**

- ≥ 3 independently parameterised NORMAL, DELAY and FAULT scenarios per topology;
- a fourth topology or replicate network for any generalisation claim;
- independent confirmatory data for any rule motivated by R2 (FA-05).

**Next actions, in priority order:**

1. **Yazan** decides R-18 (A/B/C) using the decision package. Option C (asking the dataset authors) can run in parallel.
2. **Faisal** approves or rejects the reporting fixes FA-10/FA-11 and the fail-closed behaviour FA-08, and decides F-D18.
3. **Owners** decide which protocol-2.0 components (P2-A … P2-H) to adopt, and request new thin-class simulations (Section 2 of the proposal).
4. **Project lead** authorizes the protocol-2.0 development pilot (development data only), then a confirmatory run on accepted data.
5. **Named owners** complete PRIMARY_RESULTS_VALIDATION of R2 as a historical record, and the outstanding approvals (Section 12).

## 12. Owner decisions needed to close the 58 plan requirements

| Requirement(s) | Status | Decision needed | Owner |
| --- | --- | --- | --- |
| Y4-b | BLOCKED | record mapping review | Faisal, Ahmed |
| Y7-b | BLOCKED | readiness decision, now including R-18 | Yazan |
| Y-APPROVE | BLOCKED | adopt amendment, checksums and risk register; family sample review | Yazan, Ahmed |
| F-D18, A14-b | BLOCKED | accept A12–A16 and the A14 inner scheme; then authorize A14 | Faisal; project lead |
| A11 | BLOCKED | PRIMARY_RESULTS_VALIDATION and R-18, before manuscript, poster and publication manifest | named owners, Yazan |
| A-APPROVE | BLOCKED | approve review-drafted documents | Ahmed |
| Y1-a, Y3-a | LIMITED | R-18 decision (the audit gap is now explained) | Yazan |
| Y-GATES, F-D15, F-D16, A-D10 | LIMITED (waived) | named attestations, to convert waivers | Yazan / Faisal / Ahmed |
| F6-b, F10-b, F11-b, A15-b, A16-b | LIMITED (scientific) | none can become COMPLETE without protocol 2.0 or new data; accept as limited or adopt P2 | Faisal, Ahmed |
| A5-b, A9-c | LIMITED | evidence-status decision; methodology freeze sign-off | named owners |

Closing all 58 as COMPLETE is not possible on the current data. Up to 9 more could move to COMPLETE through decisions and attestations alone: Y4-b, Y7-b, Y-APPROVE, A-APPROVE, F-D18, Y-GATES, F-D15, F-D16 and A-D10. A14-b additionally needs an authorized run.
