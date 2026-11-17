# Repository Baseline (recorded before any modification)

| Item | Value |
| --- | --- |
| Local path | `<local clone>/H2-PRISM` (machine-specific path redacted before version control) |
| Remote | `origin https://github.com/ayazashy/H2-PRISM.git` (the user is a collaborator, not the owner) |
| Default branch | `main` (`refs/remotes/origin/HEAD -> origin/main`) |
| Branch at start | `main`, clean working tree (no staged, unstaged or untracked changes) |
| HEAD at start | `13c55125a2588cfb2708d7c0e58bc9454996b933`, "feat(data): add 1-click setup_data.py runner …" |
| Other remote branches | `origin/dataset`, `origin/old-main` (Stage 1 archive) |
| Submodules / LFS | none (no `.gitmodules`, no `.gitattributes`, `git lfs` not configured) |
| Tracked files | 87 |
| Working branch created | `audit/preparation-integration` (new local branch from `13c5512`; nothing pushed) |
| Python | 3.12.1 (Windows). The authors' logs record 3.14.2 on macOS |
| Base environment | numpy 2.3.1, pandas 2.3.3, scikit-learn 1.7.0, scipy 1.16.0, pyarrow 25.0.1, matplotlib 3.10.7. **pytest and PyYAML were missing.** |
| Test environment used | `.venv/` (gitignored, `--system-site-packages`) with `pytest 9.2.0` and `PyYAML 6.0.3` added. Nothing was installed globally |
| Raw dataset | **absent** (`data/raw/` does not exist). Only `data/sample/` (4 Parquet files, checksum-verified) |

## Source documents

| Plan | Location used | SHA-256 (prefix) | Note |
| --- | --- | --- | --- |
| Ahmed New Plan 2 | `~/Downloads/Ahmed New Plan 2.pdf` | `0d838036…` | Contains A1–A16. The repo copy `assets/Ahmed new plan.pdf` is an older version (A1–A11 only) |
| Faisal New Plan 2 | `~/Downloads/Faisal New Plan 2.pdf` | `ce419091…` | Adds the A12–A16 delegation clauses. The repo copy is older |
| Yazan new plan | `assets/Yazan new plan.pdf` | `6f0a7868…` | Identical to the copy in Downloads. No "Plan 2" exists |

## Baseline structure (tracked)

`00_governance/` (5) · `01_dataset_audit/` (34, including `provisional/`) · `03_results/` (dashboard and 6 figures) · `05_documentation/FIGURE_SPECIFICATION.md` · `assets/` (5 PDFs) · `audit/` (7 scripts) · `configs/interface_contracts.yaml` · `data/sample/` (5) · `scripts/` (2) · `src/h2prism/{data,visualization}` · `tests/` (3 test modules). **`02_methodology/` and `04_validation/` are referenced by README but do not exist.**

## Baseline test result (unchanged code, Python 3.12)

`pytest` (the whole suite) stopped at collection: `tests/test_visualization.py` raised `NameError: name 'Any' is not defined` (`src/h2prism/visualization/dashboard.py:27`).
Excluding that module: **10 passed, 2 failed**.
- `test_load_scenario_by_id` failed with FileNotFoundError (raw data absent).
- `test_load_fold` failed because the fold came back empty; `load_fold` silently skipped every missing file.

README claims "23 passing tests".

## Component classification (F1 support; Faisal must verify)

| Component | Classification | Status | Reason |
| --- | --- | --- | --- |
| `audit/01…08`, `run_all_audits.py` | MODIFY (owner: Yazan) | IMPLEMENTED, not re-executable here | Real, deterministic code; Scenario_ID, family and fold logic defective (ISS-01, 02, 07) |
| `01_dataset_audit/*` | MODIFY | PARTIALLY_IMPLEMENTED | See `YAZAN_DATASET_VERIFICATION.md` |
| `src/h2prism/data/loader.py` | KEEP + MODIFY | TESTED | Silent skip fixed; ambiguity documented |
| `src/h2prism/visualization/*` | KEEP (styling) | TESTED | Plotting functions are fine. Their demo inputs were the problem |
| `scripts/visualize.py --demo` | MODIFY | TESTED | Fabricated outputs quarantined and labelled |
| `03_results/figures/fig3–6`, `dashboard.html` | RETIRE (quarantined) | — | Not results (ISS-03) |
| `03_results/figures/fig1–2` | UNVERIFIED | — | fig1 is derived from `FAMILY_CLASS_DISTRIBUTION.csv`, which inherits the Y5 defects; fig2 comes from raw data |
| `configs/interface_contracts.yaml` | MODIFY (owner: Faisal) | PARTIALLY_IMPLEMENTED | Differs from the F12 core contract (ISS-14) |
| `00_governance/*` | MODIFY (owners: Ahmed, Faisal) | — | Unsupported gate PASS records (ISS-11) |
| `scripts/download_data.py`, `setup_data.py` | UNVERIFIED | — | Not executed: they download about 1 GB from Zenodo, which needs user approval |
| Stage 1 code on `old-main` | RETIRE (historical) | — | Not reproduced; no historical metric may be cited |
