# Scientific Claim and Limitation Register (A7)

- **Status:** PRE-EXPERIMENT. Consolidates `06_audit_preparation/phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md` and `phase6_resolution/SCIENTIFIC_LIMITATIONS_AND_CLAIMS.md` (items 1–11). Ahmed's approval NOT_RECORDED.
- **Claim classes:** PERMITTED (now), CONDITIONAL (permitted only with the stated evidence), UNSUPPORTED (prohibited).

| # | Claim | Class | Evidence required / reason |
| --- | --- | --- | --- |
| C1 | The dataset is simulated H₂-SimNet V2 with 57 runs, 3 topologies, 16 sensor channels | PERMITTED | verified audit |
| C2 | The pipeline is leakage-safe by design (family/topology-disjoint folds; development-only fitting) | PERMITTED (software property) | tests; this is not experimental validation |
| C3 | D(x) improves selective diagnosis beyond C/M/H | CONDITIONAL | authorized RQ1 run, Δ < 0 with an interval excluding 0, at matched coverage. Even then scoped to the 3 simulated topologies, and qualified by the offset-invariant sensitivity |
| C4 | The selective policy yields informative ambiguity sets | CONDITIONAL | RQ2 outputs: inclusion rate with size; LEAK restricted, other classes descriptive |
| C5 | Results generalise to other networks or field pipelines | UNSUPPORTED | L1, L2 |
| C6 | D(x) measures physical identifiability | UNSUPPORTED | empirical neighbourhood statistic only |
| C7 | Leak location / metric localisation | UNSUPPORTED | categorical valve-zone labels; annotation anomalies |
| C8 | Pure-hydrogen or a verified 10% blend | UNSUPPORTED | REPORTED_UNVERIFIED |
| C9 | DELAY detection reflects the delay event | UNSUPPORTED | L6 start-up confounding |
| C10 | Classifier evidence reflects physical event signatures | CONDITIONAL | consistent results under `offset_invariant_features` (L5 run fingerprint) |
| C11 | Statistical significance | UNSUPPORTED | effect sizes only (SAP) |
| C12 | Software testing = experimental validation | UNSUPPORTED | the passing test suite verifies software, not hypotheses |
| C13 | Ambiguity inclusion = specific-diagnosis accuracy | UNSUPPORTED | reported separately |
| C14 | Point estimates without intervals as conclusions | UNSUPPORTED | intervals mandatory |
| C15 | The legacy dashboard values (96% accuracy, 8.1% risk) | UNSUPPORTED | invented (ISS-03) |

**Mandatory limitations in any report:**
- L1: three topologies.
- L5: run fingerprint.
- L6: DELAY / start-up confounding.
- L3 and L4: thin classes, LEAK dominance.
- L7: unknown ancestry.
- L2: simulation only.

See `DATASET_LIMITATIONS.md`.
