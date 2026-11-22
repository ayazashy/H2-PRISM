# Scientific Claim and Limitation Register (candidate for A7; PENDING Ahmed adoption)

Categories: **VERIFIED_DATASET_FACT** · **IMPLEMENTED_CAPABILITY** · **TESTED_COMPUTATIONAL_PROPERTY** · **HYPOTHESIS** · **EXPERIMENTAL_OUTCOME** · **UNSUPPORTED**

| # | Claim | Category | Evidence / condition |
| --- | --- | --- | --- |
| 1 | The H₂-SimNet V2 archive used is the official, unaltered Zenodo release | VERIFIED_DATASET_FACT | MD5 equals Zenodo; `RAW_DATASET_VERIFICATION_REPORT.md` §2 |
| 2 | 57 simulated runs in 3 withdrawal topologies; 51 eligible for the 4-class task | VERIFIED_DATASET_FACT (counts); eligibility PENDING Y-D05 | `evidence/INVENTORY_RECONCILIATION.csv` |
| 3 | Clean and noise-added files are realizations of the same runs | VERIFIED_DATASET_FACT | `FAMILY_RELATIONSHIP_EVIDENCE.csv` |
| 4 | Sampling interval 1 s | VERIFIED_DATASET_FACT (Parquet index) | `TIME_AXIS_AUDIT.csv` |
| 5 | Pressure in MPa, mass flow in kg/s; no temperature channels | VERIFIED (channels); REPORTED (units, from the ReadME) | ReadME; channel audit |
| 6 | Hydrogen blend of 10% H₂ / 90% CH₄ | **UNSUPPORTED** (unverified) | Use only "hydrogen-blend (as described by the dataset publisher)" |
| 7 | Simulated with MATLAB R2025a Simscape Gas Fluids | REPORTED | ReadME (not independently verified) |
| 8 | Grouped evaluation without family, run or duplicate leakage | TESTED_COMPUTATIONAL_PROPERTY of the **candidate** folds only | 0 issues under 3 views; tests. The original `folds.csv` **leaks** |
| 9 | D(x), comparators, policy and metrics implement their stated definitions | TESTED_COMPUTATIONAL_PROPERTY | closed-form and synthetic tests; tie-inclusive neighbourhood noted |
| 10 | Pipeline is deterministic and cross-platform reproducible | TESTED_COMPUTATIONAL_PROPERTY | 13/13 identical hashes with a reverse-order build; Windows only |
| 11 | D(x) adds decision value beyond C, M, H (RQ1) | HYPOTHESIS | No experiment run |
| 12 | The policy yields meaningful three-outcome diagnoses (RQ2) | HYPOTHESIS | No experiment run |
| 13 | Any accuracy, selective-risk, calibration or coverage number | none exist | The quarantined demo figures are fabricated illustrations, **not** outcomes |
| 14 | Generalisation to an unseen withdrawal topology of this simulated network | HYPOTHESIS (testable, restricted) | LOTO design |
| 15 | Class-specific performance for NORMAL, FAULT, DELAY | DESCRIPTIVE only once outcomes exist | 3 runs each |
| 16 | Superiority or novelty of D(x) | **UNSUPPORTED** | — |
| 17 | Physical identifiability | **UNSUPPORTED** (D is empirical) | — |
| 18 | Metric leak localisation (G3–G6) | **UNSUPPORTED** (categorical labels; L1 annotation conflict) | — |
| 19 | Industrial deployment readiness, unseen real networks, field validation | **UNSUPPORTED** | simulated data only |
| 20 | Pure-hydrogen applicability | **UNSUPPORTED** | — |
| 21 | Historical Stage 1 metrics (95.2% balanced accuracy, ±650 m localisation, FPAR) | **UNSUPPORTED** as current results | `LEGACY_RESULTS_STATUS.md` |
| 22 | "Peer-reviewed dataset" (README) | UNVERIFIED | Cite the publications instead |

**Mandatory limitations for any manuscript:**
1. Simulated data only.
2. 3 topologies.
3. Thin classes (3 runs each).
4. Phase–event confounding by design.
5. Annotation conflicts L1 and L2.
6. Composition unverified.
7. Windows are not independent.
8. Thresholds are chosen on development folds whose thin classes rest on single runs.
