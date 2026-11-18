# H1 analysis — reproduction

**Environment:** Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7, PyYAML, pyarrow (parquet). Times New Roman must be installed. It is used for rendering only and never copied.

**External input.** The frozen R2 run directory holds `predictions.parquet` (SHA-256 `4338c8c9…`) and `decisions.parquet` (`1f457927…`). These are untracked by data policy. In the original workspace they sit at `../H2-PRISM/03_results/primary_protocol/PRIMARY`. Running the R2 runner again is not required and is not allowed.

Run from the repository root (PowerShell):

```powershell
$env:H2PRISM_R2_RUN = '<frozen R2 run directory>'
$H = '03_results/integrated_validation_v1/h1_validation/scripts'
python "$H/h1_analysis.py"     # verifies hashes; writes analysis/*.csv; 161 verification checks must all match
python "$H/h1_tables.py"       # tables/H1-T01..T08 (CSV + Markdown)
python "$H/fig_h1.py"          # figures/H1-F01..F07 (PNG 3840 px + SVG), captions/, quality_control/H1_FIGURE_MANIFEST.csv
python "$H/h1_report.py"       # H1_RESULTS.md assembled from the CSVs
```

**Behaviour:**

- **Determinism:** fixed bootstrap seed 20261104, fixed SVG hash salt, no timestamps in images. Re-running produces identical CSVs and images.
- **Refusal:** `h1_analysis.py` exits with `REFUSED` if the parquet hashes or the configuration hash differ. An `AssertionError` is raised if any reproduced count differs from the frozen R2 outputs.
