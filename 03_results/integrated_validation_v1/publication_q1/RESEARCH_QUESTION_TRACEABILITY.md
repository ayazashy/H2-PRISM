# Research-question traceability

| Question | Registered source | Evidence in this package | Figures | Tables | Verdict |
|---|---|---|---|---|---|
| **H1 / RQ1**: at matched coverage, does the distinguishability assessment reduce selective risk vs conventional confidence abstention? | `02_methodology/STATISTICAL_ANALYSIS_PLAN.md`; R2 `rq1.csv` | R2 re-read (6 rows per variant); feasibility recomputed; exploratory shared-coverage reanalysis with family and ancestor intervals; attribution decomposition | H1-F01, H1-F02a, H1-F02b, H1-F03, H1-F05 | T08a, T08b, H1-T01–T04 | **NOT_ESTIMABLE** (registered); exploratory evidence only, inconclusive |
| **H1 root causes** | R2 diagnostics, forensics | Causal chain: attribution defect → single-family neighbourhoods → flags → Center coverage 0.258 | H1-F01, Q1_I05, Q1_I06 | H1-T01, H1-T02 | Observed causes quantified |
| **RQ2**: does D(x) add information beyond confidence, margin and entropy? | `05_documentation/PROTOCOL_2_ABLATION_REPORT.md` | Development ablation; R2 correctness AUROC | H1-F04a, H1-F04b | T09a, H1-T05a/b | **No incremental value demonstrated** |
| **RQ3**: are the SPECIFIC, AMBIGUOUS and UNRESOLVED outcomes valid and informative? | R2 `rq2.csv` (named RQ2 in the 2026-11-04 methodology); Center Experiment E | Registered decisions per class; classifier-error destination; formal D(Y) universe dependence | Q1_I08, H1-F05, H1-F06, Q1_C14, Q1_C15 | T09b, T07a/b, H1-T06a/b | Descriptively demonstrated (R2) and conditionally demonstrated (Center) |
| **Formal D(Y)** | Center enhancement Experiments D–E | Status matrices, exclusion onsets, universe dependence, library completeness | Q1_C12a–d, Q1_C13a–b, Q1_C14, Q1_C15, H1-F06, Q1_I07 | T07a/b, TS01, TS02 | **CONDITIONAL_HYPOTHETICAL_BOUNDS** |
| **Mechanism recognition** | Center enhancement Experiment B | Frozen vs leave-own-template-out | Q1_C07, Q1_C08, Q1_I04 | T05 | Descriptive; 3/5 supported agree |
| **Categorical localization** | Center enhancement Experiment C | Ranking with and without an independent replicate; sensor groups | Q1_C09, Q1_C10, Q1_C11 | T06a/b | Descriptive; no localization accuracy |
| **Reference prediction (MHC)** | Study B protocol | Frozen replay; error structure; resolution; control role | Q1_B01–B13, Q1_I02, Q1_I03 | T02, T03 | **Validated within scope** |
| **Reference and evidence validity (HY2RES)** | Study C protocol | Quantization, drift, support, unresolved taxonomy, state outcomes | Q1_H01–H14 | T02, T03, T04a/b | **Verified within scope**; no fault diagnosis |
| **Claims overall** | All accepted claim tables | Claim-to-evidence matrix | Q1_I09, H1-F07 | T10, H1-T07 | See T10 |
