# Center evidence enhancement — Reproduction

## External data dependency

The 12 accepted captures stay outside Git. Point the code at the Center workspace, which contains `work/` and `outputs/` laid out as listed in `03_results/validation/baseline_freeze_v1/baseline_manifest.json`. Either pass `--workspace <path>` or set `H2PRISM_CENTER_WORKSPACE`. The loader refuses any capture whose raw SHA-256 differs from its receipt.

Raw capture hashes (`center_raw.mat`):

| Capture | SHA-256 |
|---|---|
| A:normal | 82487367abc40f5ac4a22324eca3178c39ed95e3fad35a650a8a08d92823a5a7 |
| A:outlet_opening | a8cb6432e8b1860805a3a2b3c90f1af1644f6757a17e403c44be831131fe5513 |
| sid312:normal | 1abb27b0cadff569872fa47b5274dd67ffe542146b11671d533af8fbaa8f8400 |
| sid312:outlet_opening | f7672fe69f79779b76a4a5ae520180ed70ef747b6989689c971eec08af4ea017 |
| sid215:normal | 8e8609d0e469fb03022f6763c0f44fbf73b647b398859e070fbbe6cfdd75b4e0 |
| sid215:outlet_opening | 9dbcd50e5fdcb8f9b7e480a5d1a663fac95f16a6c03e13777eddadb7a51cd847 |
| pressure_rival:normal | 9294d23b7e0a8a1e8a2cbd48ef50a5e7d2d2b2994cda329f9c4af26ed730e534 |
| pressure_rival:outlet_opening | 6fb49fec31dbd399254d63668e6079753d45012b4d3b5c461f71de1676e209a1 |
| alternate_profile:normal | 51170d2b5cfaed1b1e74b7a2c910f287e98cb5c74547c920e0f2177c095efafd |
| alternate_profile:outlet_opening | 664d4c1b39295d6efd93ba941a0ec9bd94dec9179082c4a884c382fa25d13113 |
| timing:normal | 15d4851f8c034ffdcfd29e81bccf062d1b820515ba6c8515051b76427f4cdef3 |
| timing:outlet_opening | 370b0f92876de7e985d2e2f178a9b613acd9409aa04adb8613898fc23adf870a |

## Environment

Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, SciPy 1.16.0, Matplotlib 3.10.7, on Windows 11. Figures use Segoe UI as the fallback for IBM Plex Sans. Kernel file hashes are in `analysis/execution_manifest.json`.

## Commands (from the repository root, PowerShell)

```powershell
$env:PYTHONPATH = 'src'
$env:H2PRISM_CENTER_WORKSPACE = '<center workspace>'
# 1. frozen baseline check (12 captures, 410 files)
python -m h2prism.baseline_freeze . $env:H2PRISM_CENTER_WORKSPACE 03_results/validation/baseline_freeze_v1/baseline_manifest.json --verify
# 2. analysis into a fresh directory (~4 min; refuses an existing directory)
python -m h2prism.center_enhancement --output <fresh>/analysis --repository .
# 3. tables and figures
python -m h2prism.center_enhancement_report --analysis <fresh>/analysis --output <fresh> --repository .
# 4. focused tests
python -m pytest -q tests/test_center_enhancement.py
```

`repository` must be a checkout that also contains `data/raw` (gitignored) only for step 1. Steps 2–4 need the workspace and the tracked repository files.

## Determinism

Two independent runs of step 2 produced byte-identical `recognition.json`, `location.json`, `dy_decisions.json`, `dy_thresholds.csv`, `pair_contrasts.csv`, `channel_signal.csv` and both gate files. Checksums of every published file are in `SHA256SUMS.csv` (text outputs are written with LF endings to match the repository eol=lf rule).
