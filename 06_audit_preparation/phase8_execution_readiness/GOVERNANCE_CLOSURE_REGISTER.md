# 04 Governance Closure Register (the 7 Phase-7 items)

No signature or date is filled in on anyone's behalf. "Waived" requires an explicit project-lead statement; none has been given.

| ID | Requirement | Technical work done (Phase 8) | Evidence | Remaining human action | Execution-blocking? |
| --- | --- | --- | --- | --- | --- |
| Y-D10 | Checksums from the untouched archive | **Done:** `RAW_CHECKSUMS_OFFICIAL_ARCHIVE.sha256` (264 files, CRLF bytes preserved, no `.gitkeep`); Yazan's original file untouched | this folder | Yazan adopts it (replace or annotate `01_dataset_audit/raw_checksums.sha256`) | No (the runner verifies per-file hashes from manifest v0.2) |
| A-D11 | Authoritative plans in `assets/` | **Done:** `Ahmed New Plan 2.pdf` (`0d838036…`), `Faisal New Plan 2.pdf` (`ce419091…`) added; hashes match the Phase-4 record | `assets/` | Ahmed acknowledges | No |
| F-D15 | Code acceptance of the new modules | Tests: 193 passed / 2 expected skips; regression tests for 2 real defects; runner tests cover 17 cases | `INTEGRATION_VALIDATION_REPORT.md` | **Faisal code review and acceptance** (cannot be automated) | **Yes, unless waived** |
| F-D18 | Acceptance of A12–A16 | Tests pass; A12 executed (33/33) | Phase 6/8 reports | Faisal acceptance | No for the primary run (A14–A16 are supporting); yes for using them |
| F-D16 | Interface contract amendments | Not applied (the contract is Faisal-owned). The runner reads manifest v0.2 directly and validates its schema | `MODEL_AND_EXPERIMENT_READINESS.md` (proposed amendments) | Faisal updates `configs/interface_contracts.yaml` or accepts the v0.2 schema as the contract | **Yes, unless waived** (the contract document is stale relative to the executed schema) |
| A-D09 | README / figure-spec corrections | Replacement text prepared (Phase 6 `AHMED_RESOLUTION.md` C5); not applied to team-owned files | — | Ahmed applies it | No for execution; yes before any publication |
| A-D10 | Gate records re-recorded | Not done (requires Ahmed's attestation) | — | **Ahmed re-records Gates 1–3** | **Yes, unless waived** (Phase 7 gate rule) |

**Summary:**
- 2 items completed technically (Y-D10, A-D11), each pending owner adoption.
- 5 items need a named owner. Of those, 3 block execution unless the project lead explicitly waives them: F-D15, F-D16, A-D10.
- No item is waived.
