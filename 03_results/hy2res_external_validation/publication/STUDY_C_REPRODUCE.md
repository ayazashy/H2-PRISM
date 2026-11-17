# HY2RES data and publication reproduction

The frozen source is the CC BY 4.0 release by Rodríguez de Lope and colleagues, Zenodo record 15166733, version v1. The source stays local for reproduction. Its expected MD5 is `9a3c3e3b1668596854b43bfd790d3e0e`. From the repository root in PowerShell:

```powershell
$source = 'data/external_validation_data/HY2RES_202404.csv'
New-Item -ItemType Directory -Force (Split-Path $source) | Out-Null
if (-not (Test-Path $source)) {
    curl.exe --fail --location 'https://zenodo.org/records/15166733/files/HY2RES_202404.csv?download=1' --output $source
    if ($LASTEXITCODE -ne 0) { throw 'HY2RES download failed' }
}
if ((Get-FileHash $source -Algorithm MD5).Hash -ne '9a3c3e3b1668596854b43bfd790d3e0e') {
    throw 'HY2RES checksum mismatch'
}
```

Use Python 3.12.1 with NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7 and Pillow 12.0.0. Build into separate directories to preserve the frozen and published artifacts:

```powershell
python 03_results/hy2res_external_validation/publication/build_publication.py --output study-c-rebuilt
python 03_results/hy2res_external_validation/publication/distinguishability/build_distinguishability.py --output distinguishability-rebuilt
```

Both builds read the source and frozen evidence. They perform no model training. The first rebuild reconciles 40 archived metric rows and exports the seven publication figure pairs. The second rebuild reproduces the descriptive pressure–flow and candidate-set figures. The historical test-access seal remains unverified.

[Official source and license](https://zenodo.org/records/15166733) · [Frozen source manifest](../source_manifest.json)
