# Reproduce the publication package

From the repository root, in PowerShell with the existing Python scientific environment active, select a destination that does not yet exist.

```powershell
$env:PYTHONPATH = 'src'
python -m h2prism.publication_atlas --repository . --workspace C:/Users/ahmd1/Documents/Codex/2026-11-16/before-starting-the-new-h-prism --output C:/Users/ahmd1/Documents/Codex/publication-reproduction
```

The renderer verifies the frozen SHA-256 manifest before opening a new destination. It uses NumPy, pandas, SciPy and Matplotlib. It reads the numeric capture files and frozen tables, and writes PNG, SVG, PDF, Markdown, CSV and JSON. It does not import serialized model objects. The historical inventory reflects files available on the host. Reproduce using the same library versions for byte-level comparisons.
