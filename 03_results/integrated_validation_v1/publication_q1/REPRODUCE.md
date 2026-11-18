# Reproducing the integrated Q1 package

**Environment:**

- Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7, SciPy 1.16.0, PyYAML, Pillow, pyarrow.
- Times New Roman must be installed on the system. On Windows this is `C:\Windows\Fonts\times.ttf`. The scripts refuse to run if Matplotlib resolves any other font, and no font file is distributed.

**Inputs:**

- All inputs are tracked in this repository, except:
  - the Center capture workspace (only needed to re-extract `data/center_trace_windows.csv`);
  - the frozen R2 parquet files (only needed for the H1 analysis; see `../h1_validation/H1_REPRODUCE.md`).
- The tracked trace CSV carries the source SHA-256 of each capture (`data/center_trace_windows.provenance.json`).

Run from the repository root (PowerShell):

```powershell
$S = '03_results/integrated_validation_v1/publication_q1/scripts'
# optional: re-extract the Center trace windows through the hash-verifying frozen loader
python "$S/extract_center_traces.py" --workspace $env:H2PRISM_CENTER_WORKSPACE --output 03_results/integrated_validation_v1/publication_q1/data/center_trace_windows.csv
python "$S/build_inventory.py"      # quality_control/FIGURE_INVENTORY.{csv,md}
python "$S/build_figures.py"        # figures/ (PNG + SVG), captions/, tables/TS01–TS02, quality_control/FIGURE_MANIFEST.csv
python "$S/build_tables.py"         # tables/T01–T10 (CSV + Markdown), TABLES_BUNDLE.md
python "$S/results_report.py"       # INTEGRATED_RESULTS.md, FIGURE_INDEX.md, TABLE_INDEX.md
python "$S/verify_package.py"       # quality_control/NUMERICAL_VERIFICATION.csv, ../SHA256SUMS.csv
```

**Build order:** run the H1 pipeline first, because the integrated tables T08–T10 and the Results chapter read its outputs.

**Determinism:** two consecutive full builds produced byte-identical PNG and SVG files for all 55 figures.

**Data-consistency checks:**

- `build_figures.py` asserts the D(Y) consistency rules: universes agree on supported hypotheses, and unsupported hypotheses are indeterminate everywhere.
- `verify_package.py` fails if any figure hash, QA status, table reconciliation or tracked file check fails.
