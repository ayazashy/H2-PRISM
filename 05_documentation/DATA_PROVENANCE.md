# Data Provenance (A10)

> **Correction (2026-11-13).** The released models define an **air-like** gas (R = 0.287 kJ/kg/K), not a 10% H₂ / 90% CH₄ blend, and their active constants are physically inconsistent. The blend statement is **refuted**. See `05_documentation/GAS_MODEL_LIMITATION.md` and `00_governance/MASTER_ISSUE_REGISTER.csv` (B-14).

- **Status:** PRE-EXPERIMENT. Machine-readable register: `PROVENANCE_REGISTER.csv`. Ahmed's approval NOT_RECORDED.
- **Tags:** VERIFIED, REPORTED_UNVERIFIED, INFERRED, PENDING, UNKNOWN.

| Field | Value | Status |
| --- | --- | --- |
| Dataset | H₂-SimNet, Zenodo record 17871393, version 2 | VERIFIED |
| Archive | `H2-SimNet-Dataset.zip`, 509,236,976 bytes, MD5 `15bc64a3afc9e2990c9db66eb37617de` | VERIFIED |
| Acquisition | a pre-existing local copy of the archive was verified in Phase 2 (MD5 and size equal the Zenodo record; zip CRC test PASS); record published 2025-12-09, licence CC-BY-4.0 (`raw_verification/ZENODO_SOURCE_PROVENANCE.json`); original download date | VERIFIED (date UNKNOWN) |
| Authors / citation | per the dataset ReadME (Acampora et al., 2025) | REPORTED_UNVERIFIED (not checked against the publisher record) |
| Nature | simulated network data (not field measurements) | VERIFIED (ReadME) |
| Simulator | Simscape Gas Fluids (version as stated in the ReadME) | REPORTED_UNVERIFIED |
| Gas composition | 10% H₂ / 90% CH₄ | REPORTED_UNVERIFIED |
| Noise-added release | the clean simulation plus white noise (residual analysis) | VERIFIED (consistent with ReadME) |
| Units | MPa (PS), kg/s (MFS) | VERIFIED_FROM_DOCS |
| Local storage | `data/raw/` (gitignored, unmodified; 264/264 checksums) | VERIFIED |
| Checksums | `RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256`; Yazan's original list is preserved and superseded for the archive | VERIFIED |
| Exclusions | 6 runs (annotation conflict ×3, compound ×3) with reasons in manifest v0.2 | VERIFIED |
| Unreadable files | none among the modelling files | VERIFIED |

**Responsible owners:**
- Yazan: source, checksums, manifest, exclusions.
- Faisal: derived tables, configurations, runs.
- Ahmed: this record and change control (`00_governance/CHANGE_CONTROL_LOG.csv`).
