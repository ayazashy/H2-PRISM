### TAB_C08 — Research claim qualification

Validation levels follow the project vocabulary. Registered RQ1/H1/RQ2 outcomes are preserved.

| claim | source_evidence | numerical_result | validation_level | limitation | poster | recommended_wording |
| --- | --- | --- | --- | --- | --- | --- |
| The 12 accepted captures and 410 frozen files are unchanged | baseline_freeze --verify (before and after) | 12 captures; 410 files matched | VERIFIED | integrity, not validity | yes | Frozen Center evidence re-verified byte for byte. |
| Center model is air-like | source SLX gas block R | R = 0.287 kJ/(kg·K), Z = 0.998386 | VERIFIED | no hydrogen material claim possible | yes | Controlled simulation with an air-like gas model. |
| Mechanism recognition does not survive self-template removal | TAB C-02 | 3/5 supported queries agree; 2 unsupported; frozen library 7/7 with self or near-duplicate templates | DESCRIPTIVE (one family) | 7 queries, 1 family | yes | Without self-templates, withdrawal at a new outlet is not recognised reliably. |
| Withdrawal signatures are outlet-specific | TAB C-04, channel_signal.csv | SID 213→MFS3 0.691 kg/s; SID 312→MFS1 0.647 kg/s; SID 215 flow ≤3.9e-4 kg/s | DESCRIPTIVE | sensor configuration of one model | yes | Each outlet excites a different branch sensor. |
| Categorical location ranking with an independent same-outlet template | TAB C-03 | SID 213 ranked 1st for 2/2 supported queries (all four sensor groups); SID 312 and SID 215 unsupported | DESCRIPTIVE (2 queries, 1 outlet) | near-duplicate template | yes, with caveat | SID 213 is ranked first when a replicate SID 213 template exists. |
| Flow-dependent B3 localization; pressure contrasts exist in native units | TAB C-04 | B3 flow share ≥ 0.97 for every outlet pair; pressure contrasts 1.1–5.5 kPa; withholding MFS3 cuts the SID 213 margin 0.028→0.0021 while the correct/runner-up ratio rises 1,030×→2,676×; pressure alone 569× | DESCRIPTIVE | normalization by absolute level | yes | B3 ranking is carried by flow; pressure differences are 1–5.5 kPa. |
| Conditional correct SPECIFIC window | TAB C-05/C-06 | pressure eps ∈ [2.5e-6, 5.1e-4) MPa; flow eps ∈ [6.8e-4, 0.69) kg/s | CONDITIONAL_HYPOTHETICAL_BOUNDS | hypothetical bounds; replicate template | yes, labelled conditional | Under declared bounds, SID 213 would be specific within a finite precision window. |
| Restricted universe can be confidently wrong | TAB C-06 | 2 wrong vs 8 correct SPECIFIC cells (all sensors, 7 scenarios × 6 queries) | CONDITIONAL_HYPOTHETICAL_BOUNDS | true mechanism unrepresented | yes | Restricting to modelled hypotheses yields wrong SPECIFIC decisions. |
| Full declared universe never decides | TAB C-06 | 42/42 UNRESOLVED (INDETERMINATE_HYPOTHESES) | CONDITIONAL_HYPOTHETICAL_BOUNDS | unmodelled FAULT/DELAY/SID 222 | yes | Formal D(Y) abstains whenever declared hypotheses lack adapters. |
| Frozen 12/12 UNRESOLVED unchanged | TAB_13, research_evidence.json | 12/12 UNRESOLVED, INVALID_UNCERTAINTY; all hypotheses adapter=None | VERIFIED | — | yes | Frozen formal outcome retained. |
| RQ1 (registered) | 03_results/primary_protocol/PRIMARY/rq1.csv | NOT_ESTIMABLE at 0.60/0.80/0.90 | REGISTERED RESULT | max Center coverage 0.258 | yes | RQ1 was not estimable under the registered protocol. |
| H1 | PRIMARY + exploratory shared coverage | all intervals vs s_C−D include 0 | NOT ESTABLISHED | inspected partitions | yes | H1 is not established. |
| RQ2 (development) | PROTOCOL_2_ABLATION_REPORT.md | s_C = s_C−D = confidence at matched development coverage | NEGATIVE (exploratory) | 13 groups | yes | No incremental value of D(x) was demonstrated. |
| Leak localization / fault diagnosis in hydrogen pipelines | — | — | NOT ESTABLISHED | no field truth | no | Not claimed. |
