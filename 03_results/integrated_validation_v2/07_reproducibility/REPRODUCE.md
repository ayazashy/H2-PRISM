# Reproducibility

## Environment
`03_execution/ENVIRONMENT.txt`:
- python 3.12.1
- platform Windows-11-10.0.26300-SP0
- cpu AMD Ryzen 5 7520U with Radeon Graphics (8 logical)
- ram_GB 7.2
- numpy 2.3.1
- pandas 2.3.3
- matplotlib 3.10.7
- scipy 1.16.0
- pyyaml 6.0.3
- pytest 9.2.0
- pyarrow 25.0.1
- coolprop not installed

## Data acquisition (outside Git)
- **R2 frozen run:** set `H2PRISM_R2_RUN` to the PRIMARY run directory (predictions.parquet SHA-256 4338c8c9…).
- **Center workspace:** set `H2PRISM_CENTER_WORKSPACE`. MAT captures are re-hashed on load.
- **HY2RES:** the Zenodo record 15166733 CSV (MD5 9a3c3e3b…), passed with `--data` / `--hy2res`.

## Exact commands (repository root)
```bash
python 03_results/integrated_validation_v2/03_execution/scripts/run_all.py --hy2res <HY2RES_202404.csv>
python 03_results/integrated_validation_v2/03_execution/scripts/audit_baseline.py --hy2res <csv>
python 03_results/integrated_validation_v2/03_execution/scripts/verify_v2.py
python -m pytest -q tests/test_dy_adversarial.py
```

- `run_all.py` runs every analysis, table, figure and report script in dependency order. It writes runtimes to `03_execution/logs/RUN_ALL.csv` and the per-file hash comparison with the committed outputs to `logs/DETERMINISM.csv`.
- `audit_baseline.py` re-runs the full suite (about 19 minutes measured); `--reuse-pytest-log` parses the existing log instead.

## Determinism
- Analyses are deterministic: fixed seeds, exact-rational decisions, sorted outputs.
- Figures use a fixed SVG hash salt and no dates.
- Known nondeterminism: runtimes and log timings vary between runs. SVG/PNG bytes depend on the Matplotlib and FreeType versions.

## Independent re-verification
- `verify_v2.py` re-checks figure hashes and QA, the checksums of every package file, the reconciliations of key numbers against their source files, and that no file outside the package changed.
