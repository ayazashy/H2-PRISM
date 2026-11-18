# Study B evidence enhancement — Reproduction

**Source:** the official MHC v1.2 ZIP (Zenodo 19036733). Expected values: 377,874,239 bytes, MD5 `64cbe2a68c0af5dc2e4a0a9690003eac`, SHA-256 `91755fb1e555e0eb32d160ac140a4261b6bb47d24944c7e717b723fe2a641e32`. Keep the ZIP outside Git.

**Environment:** Python 3.12 with `study_b/requirements.txt` (NumPy 2.3.1, openpyxl 3.1.5, scikit-learn 1.7.0, Matplotlib 3.10.7) plus pandas. This package was produced with openpyxl 3.0.10, and the replay was bit-identical.

From the repository root (PowerShell):

```powershell
$zip = '<path to MHC-Dataset-v1.2.zip>'
$out = 'study_b/evidence_enhancement/results'   # must not exist; use a fresh path to rebuild elsewhere
python study_b/evidence_enhancement/replay.py $zip --output "$out/replay"            # refuses to write predictions if the frozen gate fails
python study_b/evidence_enhancement/analysis.py --replay "$out/replay" --output "$out/analysis"
python study_b/evidence_enhancement/report.py --replay "$out/replay" --analysis "$out/analysis" --output $out
python -m pytest -q study_b/evidence_enhancement/test_enhancement.py study_b/test_benchmark.py
python study_b/verify_publication.py $zip                                             # frozen verifier, read-only
```

Two independent runs produced identical decompressed predictions (2,146,674 bytes) and identical gate and analysis CSVs. `results/SHA256SUMS.csv` lists every published file. Text outputs use LF endings, matching the repository's `eol=lf` rule.
