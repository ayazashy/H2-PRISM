# Git, Backup and Change Review (G-D01: PENDING user approval; nothing committed)

## State (read-only inspection)

| Item | Value |
| --- | --- |
| Branch | `audit/preparation-integration` (local only, no upstream) |
| HEAD | `13c55125a2588cfb2708d7c0e58bc9454996b933` (= `main`; no new commits) |
| Remote | `origin https://github.com/ayazashy/H2-PRISM.git` (nothing pushed) |
| Staged | 5 renames (`git mv` of the fabricated demo figures and dashboard into `03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/`) |
| Unstaged | 11 tracked files: 6 source/test files plus the 5 regenerated quarantined demo files |
| Untracked | 140 files (at review time), about 2 MB in total (largest group `06_audit_preparation/`, 1.9 MB) |
| Ignored and confirmed excluded | `data/raw/` (`.gitignore:51`), `.venv/`, `__pycache__/` |

## Sensitive-file review

- No credentials, keys, tokens or `.env` files.
- No archives, no Parquet, no raw data, no files over 1 MB untracked.
- One machine-specific path was found in `06_audit_preparation/REPOSITORY_BASELINE.md` (local user path) and **redacted**.
- Remaining references to `~/Downloads/...` in the provenance JSON and reports are generic home-relative paths with no username.
- The quarantined demo PNGs and HTML are binary (2.2 MB). They are kept because deleting them is Ahmed's decision (A-D09).

## Backup (outside the repository)

`<home>\Documents\H2-PRISM_backups\phase4_20261110_213044\` contains:
- `files/`: 127 modified, staged and untracked files at their repository paths;
- `staged.patch`, `unstaged.patch` (binary diffs), `git_status.txt`, `HEAD.txt`;
- `RAW_DATA_REFERENCE.json`: source, archive hash, per-file checksum file; the 1 GB raw data is not copied;
- `BACKUP_MANIFEST.json`: SHA-256 of every file.

**Verification:** all 127 copies re-hashed with 0 mismatches. The backup directory was new; the script refuses to overwrite an existing one.

## Proposed local commits (not executed; one logical change each)

| # | Message | Paths |
| --- | --- | --- |
| 1 | `fix(results): quarantine illustrative demo outputs and fix loader/dashboard defects` | already-staged renames; `03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/`; `scripts/visualize.py`; `src/h2prism/visualization/dashboard.py`; `src/h2prism/data/loader.py`; `tests/test_data_loader.py`; `tests/test_visualization.py` |
| 2 | `feat(prep): leakage-safe preparation modules for F3-F9 and A12-A16` | `src/h2prism/{io,windows,features,splits,baseline,calibration,distinguishability,policy,metrics,comparators,secondary_baseline}.py`; `src/h2prism/experiments/`; `tools/research_audit/`; `tools/reporting/`; `configs/{secondary_baseline,feature_sensitivity,reporting_figures,artifact_validation}.yaml`; `02_methodology/`; `tests/` (except the files in 1 and 3); `tests/conftest.py` |
| 3 | `feat(dataset): deterministic candidate manifest, families and folds` | `src/h2prism/dataset_manifest.py`; `tools/dataset/`; `configs/candidate_artifact_validation.yaml`; `tests/test_{dataset_manifest,candidate_package,real_data_interfaces}.py` |
| 4 | `docs(audit): audit, raw-data verification, pre-experiment review and phase-4 approval packages` | `06_audit_preparation/` |

Alternatively, as a single commit: `chore(research): validate dataset and prepare reproducible methodology interfaces`.

Every commit would end with the attribution line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

**Before committing:** confirm that `06_audit_preparation/pre_experiment_review/` and `candidate_corrections/` (CANDIDATE artifacts) should be versioned. Recommended: yes, so their hashes are traceable. No push, merge or force operation is proposed.

## Final backup (end of Phase 4)

`<home>\Documents\H2-PRISM_backups\phase4_20261110_214102\`: 152 files, SHA-256 re-verified with 0 mismatches. It includes every Phase 4 deliverable written up to this section (this closing note was appended afterwards). The earlier backup `phase4_20261110_213044` is kept unchanged.
