# Advanced validation — reproduction

**Environment:** as for the H1 package (Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7, PyYAML, pyarrow, psutil, Pillow), with Times New Roman installed.

**External inputs:**

| Input | Variable | Notes |
|---|---|---|
| Frozen R2 run directory (parquet files, hash-pinned) | `H2PRISM_R2_RUN` | Not tracked by data policy |
| Center capture workspace | `H2PRISM_CENTER_WORKSPACE` | Each capture is hash-verified by the loader |

From the repository root (PowerShell):

```powershell
$env:H2PRISM_R2_RUN = '<frozen R2 run directory>'
$env:H2PRISM_CENTER_WORKSPACE = '<Center workspace>'
$S = '03_results/integrated_validation_v1/advanced_validation/scripts'
python "$S/av_r2.py"                      # R2 accounting, negative control, eligibility, template sharing, gap
python "$S/av_dy_experiments.py" --workers 7   # 2,376 formal decisions (about 3 min on 8 logical CPUs)
python "$S/av_dy_analysis.py"             # invariants, summaries, localization, isolability, minimum sets
python "$S/av_benchmarks.py"              # timing (hardware-dependent; values differ by machine)
python "$S/av_tables.py"                  # tables A01–A20
python "$S/fig_av.py"                     # figures AV-F01..F16 + captions + quality_control/AV_FIGURE_MANIFEST.csv
python "$S/av_report.py"                  # ADVANCED_VALIDATION_RESULTS.md
python "$S/verify_av.py"                  # checks and ../SHA256SUMS update
```

**Expected reproducibility:**

- Every step except `av_benchmarks.py` is deterministic.
- The random sensor masks use seed 20261118.
- Timing values vary with hardware and load.
