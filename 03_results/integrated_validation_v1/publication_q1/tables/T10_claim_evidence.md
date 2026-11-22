### T10 — Claim-to-evidence matrix

Every claim of the integrated package with its evidence, number and qualification, quoted from the accepted study claim tables and the H1 qualification table.

| study | claim | evidence | numerical_result | qualification | limitation |
|---|---|---|---|---|---|
| Center | The 12 accepted captures and 410 frozen files are unchanged | baseline_freeze --verify (before and after) | 12 captures; 410 files matched | VERIFIED | integrity, not validity |
| Center | Center model is air-like | source SLX gas block R | R = 0.287 kJ/(kg·K), Z = 0.998386 | VERIFIED | no hydrogen material claim possible |
| Center | Mechanism recognition does not survive self-template removal | TAB C-02 | 3/5 supported queries agree; 2 unsupported; frozen library 7/7 with self or near-duplicate templates | DESCRIPTIVE (one family) | 7 queries, 1 family |
| Center | Withdrawal signatures are outlet-specific | TAB C-04, channel_signal.csv | SID 213→MFS3 0.691 kg/s; SID 312→MFS1 0.647 kg/s; SID 215 flow ≤3.9e-4 kg/s | DESCRIPTIVE | sensor configuration of one model |
| Center | Categorical location ranking with an independent same-outlet template | TAB C-03 | SID 213 ranked 1st for 2/2 supported queries (all four sensor groups); SID 312 and SID 215 unsupported | DESCRIPTIVE (2 queries, 1 outlet) | near-duplicate template |
| Center | Flow-dependent B3 localization; pressure contrasts exist in native units | TAB C-04 | B3 flow share ≥ 0.97 for every outlet pair; pressure contrasts 1.1–5.5 kPa; withholding MFS3 cuts the SID 213 margin 0.028→0.0021 while the correct/runner-up ratio rises 1,030×→2,676×; pressure alone 569× | DESCRIPTIVE | normalization by absolute level |
| Center | Conditional correct SPECIFIC window | TAB C-05/C-06 | pressure eps ∈ [2.5e-6, 5.1e-4) MPa; flow eps ∈ [6.8e-4, 0.69) kg/s | CONDITIONAL_HYPOTHETICAL_BOUNDS | hypothetical bounds; replicate template |
| Center | Restricted universe can be confidently wrong | TAB C-06 | 2 wrong vs 8 correct SPECIFIC cells (all sensors, 7 scenarios × 6 queries) | CONDITIONAL_HYPOTHETICAL_BOUNDS | true mechanism unrepresented |
| Center | Full declared universe never decides | TAB C-06 | 42/42 UNRESOLVED (INDETERMINATE_HYPOTHESES) | CONDITIONAL_HYPOTHETICAL_BOUNDS | unmodelled FAULT/DELAY/SID 222 |
| Center | Frozen 12/12 UNRESOLVED unchanged | TAB_13, research_evidence.json | 12/12 UNRESOLVED, INVALID_UNCERTAINTY; all hypotheses adapter=None | VERIFIED | — |
| Center | RQ1 (registered) | 03_results/primary_protocol/PRIMARY/rq1.csv | NOT_ESTIMABLE at 0.60/0.80/0.90 | REGISTERED RESULT | max Center coverage 0.258 |
| Center | H1 | PRIMARY + exploratory shared coverage | all intervals vs s_C−D include 0 | NOT ESTABLISHED | inspected partitions |
| Center | RQ2 (development) | PROTOCOL_2_ABLATION_REPORT.md | s_C = s_C−D = confidence at matched development coverage | NEGATIVE (exploratory) | 13 groups |
| Center | Leak localization / fault diagnosis in hydrogen pipelines | — | — | NOT ESTABLISHED | no field truth |
| MHC | Causal one-step prediction | frozen benchmark + bit-identical replay | 15,885 rows/channel, 3 runs | VALIDATED WITHIN SCOPE | prohibited: Generality beyond this apparatus |
| MHC | Reference error behaviour | replayed predictions | Ridge RMSE gain from rare large steps; MAE loss on unchanged rows | DESCRIPTIVELY SUPPORTED | prohibited: Practical superiority of Ridge |
| MHC | Measurement resolution | recorded values only | P-2 0.2 barg grid; MFC-3 0.01 ln/min grid | NUMERICALLY VERIFIED (observed grid) | prohibited: Certified accuracy statements |
| MHC | Controller role of MFC-3 | workbook notes + coupled P-2/MFC-3 data | P-2 ≤ outlet set pressure + 1 barg whenever MFC-3 = 0 (3/3 runs) | DESCRIPTIVELY SUPPORTED | prohibited: Modelling the control law (setpoint not recorded) |
| MHC | Operating-condition dependence | 3 runs, confounded settings | Run 29 carries 82 % of P-2 ΔSSE | DESCRIPTIVELY SUPPORTED | prohibited: Attribution to material, pressure or cycle time |
| MHC | Competing event hypotheses | operator notes (valve timing, safety valve, back-pressure error) | notes only | NOT ESTABLISHED | prohibited: Event labels |
| MHC | Fault classification / localization | none | — | BLOCKED BY EVIDENCE | prohibited: Any accuracy or localization metric |
| MHC | Formal D(Y) | none | — | BLOCKED BY EVIDENCE | prohibited: Exclusion or certified diagnosis |
| MHC | Independent equipment transfer | one apparatus | — | NOT ESTABLISHED | prohibited: Industrial generalization |
| HY2RES | Source identity | MD5/size of restored source | 38,621,947 bytes, MD5 9a3c3e3b… | VERIFIED WITHIN SCOPE | does not establish: Calibration or synchronisation |
| HY2RES | Pressure recording grid | TAB_H01 | both pressures 100 % on 0.1 bar grid | NUMERICALLY VERIFIED | does not establish: Instrument accuracy |
| HY2RES | Ridge vs persistence | TAB_H02/H03 | buffer ΔMAE +0.015 incr., ΔRMSE −0.028 incr.; tank −0.005/−0.099 | DESCRIPTIVELY SUPPORTED | does not establish: Practical superiority; new held-out claim |
| HY2RES | Tank-pressure drift | TAB_H04, FIG_H04 | dev max 106.6 bar; 71.8 % of test source rows above | DESCRIPTIVELY SUPPORTED | does not establish: Physical cause |
| HY2RES | Unresolved mechanism | TAB_H06 | 31,589 / 32,308 unresolved = tank out of support | NUMERICALLY VERIFIED (reconciled) | does not establish: That abstention is diagnostically correct |
| HY2RES | Minority state | TAB_H07 | 0 of 817 compressor rows specific | DESCRIPTIVELY SUPPORTED | does not establish: Compressor fault detection |
| HY2RES | Positive-flow distinction | TAB_H08 | flow rank probability 0.945 → 0.554 | DESCRIPTIVELY SUPPORTED | does not establish: Classification accuracy |
| HY2RES | Formal D(Y) | source scope | no qualified bounds, fault library, labels or locations | NOT ESTABLISHED | does not establish: Any exclusion or certified diagnosis |
| HY2RES | Fault / leak / localization / transfer | source scope | no truth | BLOCKED BY EVIDENCE | does not establish: Any accuracy, localization or generalisation claim |
| R2 / H1 | Registered RQ1 / H1 contrast (s_C vs s_C−D) | h1_validation | R2 rq1.csv: 12/12 rows; Center coverage 0.258 < 0.60 | NOT_ESTIMABLE | see H1_LIMITATIONS.md |
| R2 / H1 | D(x) neighbourhood statistic and s_C meta-model | h1_validation | 02_methodology/DISTINGUISHABILITY_MATHEMATICAL_SPEC.md | IMPLEMENTED, TESTED | see H1_LIMITATIONS.md |
| R2 / H1 | Reproduction of R2 selections and registered intervals | h1_validation | 161/161 checks (h1_verification.csv) | NUMERICALLY VERIFIED | see H1_LIMITATIONS.md |
| R2 / H1 | D(x) incremental value at development level | h1_validation | G1: s_C = s_C−D = confidence = 0.091 | NOT SUPPORTED (exploratory) | see H1_LIMITATIONS.md |
| R2 / H1 | s_C lower risk than s_C−D at shared coverage ≤ 0.25 | h1_validation | Δ ≤ 0 at 5/5 points; all intervals include 0; 0 errors outside disputed runs for both | EXPLORATORY EVIDENCE ONLY — INCONCLUSIVE | see H1_LIMITATIONS.md |
| R2 / H1 | Evidence guard withholds errors accepted by confidence abstention | h1_validation | 78.3 % of classifier errors blocked; ancestor CI < 0 at 3/5 points | EXPLORATORY, CONFOUNDED BY D1 DEFECT | see H1_LIMITATIONS.md |
| R2 / H1 | Three-outcome policy produces SPECIFIC / AMBIGUITY / UNRESOLVED | h1_validation | 0 wrong SPECIFIC of 11,198; 31/31 ambiguity sets include truth | DESCRIPTIVELY DEMONSTRATED (R2 folds 2–3) | see H1_LIMITATIONS.md |
| R2 / H1 | Formal D(Y) three outcomes on Center | h1_validation | restricted 48 correct / 11 wrong SPECIFIC; full universe 336/336 UNRESOLVED | CONDITIONALLY DEMONSTRATED (hypothetical bounds) | see H1_LIMITATIONS.md |
| R2 / H1 | Incomplete hypothesis library causes false specificity | h1_validation | 11/11 wrong SPECIFIC with unsupported truth; 0/48 with supported truth | CONDITIONALLY DEMONSTRATED | see H1_LIMITATIONS.md |
| R2 / H1 | Corrected-attribution replication | h1_validation | EXPERIMENT_F_PROPOSAL.md | BLOCKED (D1 not recorded) | see H1_LIMITATIONS.md |
| R2 / H1 | H1 independent confirmation | h1_validation | no untouched partition; 17 scenario ancestors | BLOCKED BY EVIDENCE | see H1_LIMITATIONS.md |
| R2 / H1 | Industrial / hydrogen-field transfer | h1_validation | simulated topologies; air-like Center model | NOT ESTABLISHED | see H1_LIMITATIONS.md |

Source: `center TAB_C08`; `study_b TAB_B08`; `hy2res TAB_H09`; `h1_validation/tables/H1-T07.csv` · Script: `publication_q1/scripts/build_tables.py`
