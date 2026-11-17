# Dataset Description (A3)

> **Correction (2026-11-13).** The released models define an **air-like** gas (R = 0.287 kJ/kg/K), not a 10% H₂ / 90% CH₄ blend, and their active constants are physically inconsistent. The blend statement is **refuted**. See `05_documentation/GAS_MODEL_LIMITATION.md` and `00_governance/MASTER_ISSUE_REGISTER.csv` (B-14).

- **Status:** PRE-EXPERIMENT DRAFT from verified audit outputs. Ahmed's approval and Yazan's verification NOT_RECORDED.
- **Evidence tags:** [VERIFIED: source], [REPORTED, UNVERIFIED], [INFERRED].

**Source.**
- H₂-SimNet, Zenodo record 17871393, version 2. Archive `H2-SimNet-Dataset.zip`, 509,236,976 bytes, MD5 `15bc64a3afc9e2990c9db66eb37617de`. [VERIFIED: raw_verification/ZENODO_SOURCE_PROVENANCE.json]
- The data are **simulated**, not field measurements. [VERIFIED: dataset ReadME]
- Simulator: Simscape Gas Fluids; gas: 10% H₂ / 90% CH₄ blend. [REPORTED, UNVERIFIED: not present in data columns]

**Files, runs and families.**
- **Files:** the archive holds 264 files. [VERIFIED: RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256]
- **Release trees:**
  - `H2-SimNet-clean/` holds 60 CSV and 61 Parquet files (2,420,000 rows).
  - A noise-added tree holds the same runs with added white noise. [VERIFIED: RAW_DATASET_VERIFICATION_REPORT §3–4]
  - CSV and Parquet are exports of the same runs, not independent experiments. Modelling uses Parquet, which stores a 1.0 s time index. [VERIFIED: Y1 amendment]
- **Runs:** 57 underlying simulation runs, each available in a clean and a noise-added realization. [VERIFIED: manifest v0.2]
- **Families:** groups of runs kept together in evaluation.
  - 39 primary families, 13 per topology, each nested in one topology. [VERIFIED: manifest v0.2]
  - The extended map (32) and conservative map (3) exist for sensitivity analysis.
- **Topologies:** three withdrawal configurations (Center, Downstream, Upstream). [VERIFIED]

**Channels.**
- Pressure PS1–PS12 and mass flow MFS1–MFS4. [VERIFIED]
- Units MPa and kg/s. [VERIFIED_FROM_DOCS]
- No temperature channels. [VERIFIED]

**Labels.**
- Row-level step functions from the label columns (`Leak`, `CompressorFault`, `CompressorDelay`, `leak_G3`–`leak_G6`, `label_anomaly`). [VERIFIED: LABEL_CONSISTENCY.csv]
- Primary 4-class target: NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY. [VERIFIED: CANDIDATE_LABEL_MAPPING.yaml]
- `leak_G3`–`leak_G6` are **categorical valve-zone labels, not metric locations**. No localisation analysis is performed.

**Eligible primary data.**
- 51 runs: per topology NORMAL 1, LEAK 13, COMPRESSOR_FAULT 2, COMPRESSOR_DELAY 1.
- 6 runs excluded (annotation conflict ×3, simultaneous events ×3).
- 60 s / 30 s windows: 27,993 per realization (NORMAL 1,995; LEAK 21,921; FAULT 3,984; DELAY 93).
- LEAK is 78.3% of windows in every topology. [VERIFIED: preflight 2026-11-11]

**Supported analyses** (`DATASET_LIMITATIONS.md` gives the full table):
- pooled 4-class selective diagnosis under leave-one-topology-out;
- per-class NORMAL/FAULT/DELAY results (descriptive only);
- the clean realization as robustness.
