# Study C evidence enhancement — Reproduction

## Source
Official file: Zenodo 15166733 v1, `HY2RES_202404.csv` — 38,621,947 bytes, MD5 `9a3c3e3b1668596854b43bfd790d3e0e`, SHA-256 `c9adf30dc1ac53e28c929505a23f84abc6e91185a4c07088adb49dd994601cdf`. Either download it with `publication/STUDY_C_REPRODUCE.md`, or recover it from Git history and restore CRLF line endings:

```powershell
git show abed1c1:data/external_validation_data/HY2RES_202404.csv > HY2RES_202404.lf.csv   # LF-normalised blob, MD5 0352346b…
python -c "import pathlib,hashlib; b=pathlib.Path('HY2RES_202404.lf.csv').read_bytes().replace(b'\n',b'\r\n'); pathlib.Path('HY2RES_202404.csv').write_bytes(b); print(hashlib.md5(b).hexdigest())"
```

Keep the CSV outside version control. `data/external_validation_data/` is gitignored, and the frozen distinguishability script reads it from there.

## Commands (repository root, PowerShell; Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7)

```powershell
$env:HY2RES_SOURCE_CSV = '<verified HY2RES_202404.csv>'
$E = '03_results/hy2res_external_validation/evidence_enhancement'
python "$E/analysis.py" --output "<fresh>/analysis"                                  # Gates A–D; exits if any fails
python "$E/report.py" --analysis "<fresh>/analysis" --output "<fresh>"
python -m pytest -q "$E/test_enhancement.py"
python 03_results/hy2res_external_validation/publication/distinguishability/build_distinguishability.py --output "<fresh>/frozen_rule"   # original script, unchanged
```

## Determinism
Two independent runs produced identical CSVs and identical decompressed `test_decision_attribution.csv.gz` content. Gzip is written with `mtime = 0`. `results/SHA256SUMS.csv` lists every published file. Text outputs use LF endings, matching the repository's `03_results/** eol=lf` rule.
