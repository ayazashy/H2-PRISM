# Candidate Dataset Freeze Specification: v0.2-candidate (CANDIDATE_NOT_APPROVED)

This is **not** a freeze. It becomes one only when Yazan (Y-D01…Y-D08) and Ahmed (interpretation) record approvals in `TEAM_SIGNOFF_CHECKLIST.md`.

## Pinned source

| Item | Value |
| --- | --- |
| Dataset | H₂-SimNet V2, DOI 10.5281/zenodo.17871393, CC-BY-4.0 |
| Archive | `H2-SimNet-Dataset.zip`, 509,236,976 B, MD5 `15bc64a3afc9e2990c9db66eb37617de` (equals Zenodo), SHA-256 `3886e9457001abe3842d0ca46bb3b744d29ca0c0de50e7a625aa4d5611537c05` |
| Local extract | `data/raw/H2-SimNet-Dataset/` (gitignored; 264 files; per-file hashes in `06_audit_preparation/raw_verification/CHECKSUM_RECONCILIATION.csv`) |

## Pinned candidate artifacts (`06_audit_preparation/pre_experiment_review/`)

| Artifact | SHA-256 |
| --- | --- |
| CANDIDATE_FILE_INVENTORY.csv | `6b56c846a1039b1ebcb09484307c15bdfdb12cea102ab412022b685c4e48dfe2` |
| CANDIDATE_SCENARIO_MANIFEST.csv | `29b8b3cc018a043e6d03aa0413e9453d8f4302543800328f3710561d2c025e6b` |
| CANDIDATE_FAMILY_MAP.csv | `950cef8b321732830d9fee4000db78aea9608ede9c0ff450b0dbb9bde04b1ebb` |
| FAMILY_RELATIONSHIP_EVIDENCE.csv | `47898bd681b273bf48347a7d659460e55f836f0cc36ffdb4ed62d19e5c612329` |
| CANDIDATE_LABEL_MAPPING.yaml | `61a3182b04e0fd7c9728945f07ab7eee13fe8fb75a8f4b55a999244cb49c1f18` |
| CANDIDATE_OUTER_FOLDS.csv | `3b21d8231a40245140f32aa6cb5193e3f45b05bd57cbb079ccccd69aafa8b1dd` |
| CANDIDATE_INNER_FOLDS.csv | `ebff65da38a5e70e45e1f1e0c4303b518ba13f9874aed06a3a191bf9c0963c5b` |
| Generator `tools/dataset/build_pre_experiment_package.py` | `7cbf422998431aba4e1f6d39e566f82354bae14138396b93978237c5d1c149df` (was `5ac8bac2…` before the LF portability fix; only the JSON writing changed) |
| Module `src/h2prism/dataset_manifest.py` | `4f315b7435cef9bc8e4e262f665a543a33716ba7c7f2901d9bfd448114329f74` |
| BUILD_SUMMARY.json | `07fd071ca9a01d4a3965d09f02da7be77c005b8ad2908c4e0dcea611343e774a` (canonical LF bytes; the earlier `511576b5…` was a CRLF-written, platform-dependent file) |

Regenerate with `python tools/dataset/build_pre_experiment_package.py --raw-parent data/raw --out <dir>`. The result must reproduce `OUTPUT_HASHES.json` (verified twice, including the reverse-order / Windows-separator run).

All hashes are of **canonical LF bytes**. `.gitattributes` forces `eol=lf` for these artifacts, so a fresh checkout on any platform (including Windows with `core.autocrlf=true`) reproduces them; this was verified in an isolated clone.

## Field mapping to the Y8 / F12 manifest contract

| Contract field | Candidate source |
| --- | --- |
| Scenario_ID | `Scenario_ID` (`CS_<TOPOLOGY>_<SEGMENT>_<RUN>`) |
| Scenario_Family_ID | `family_primary` (sensitivity: `family_extended`, `family_conservative`), **pending Y-D04** |
| Realization_ID / source file | inventory `file` + `realization_type`; manifest `canonical_clean_file`, `canonical_noise_added_file` |
| Raw label | `raw_active_label_columns`, `event_types_rowlevel`, `leak_locations_rowlevel` |
| Proposed mapped label | `candidate_primary_class` (pending Y-D05, A-D05) |
| Topology | `topology` (from path; verified distinct simulations) |
| Phase | `readme_phase` (REPORTED, per event type); folder kept as `segment_dir` (not phase) |
| Timing status | `onset_s_verified`, `delay_last_active_s`, `onset_vs_readme` |
| Inclusion / exclusion | `eligible_primary_candidate`, `class_note` |
| Evidence reference | `FAMILY_RELATIONSHIP_EVIDENCE.csv` edge IDs (family map `dependence_edges`) |
| Version / generation | `status`, generator hash above |

## Supersession

`01_dataset_audit/provisional/` v0.1 and `01_dataset_audit/folds.csv` stay unchanged as historical records. After approval, record them as **superseded for experimental use** in a change-control entry (F-D16 / F12).
