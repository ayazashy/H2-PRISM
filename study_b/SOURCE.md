# H₂-PRISM Study B source

Fleming, L. (2026). *Experimental Dataset for a Two-Stage Metal Hydride Hydrogen Compressor* (v1.2). Zenodo. [Archived release](https://doi.org/10.5281/zenodo.19036733).

The archived README identifies the companion manuscript as *Experimental Two-Stage Compressor with Exchangeable Metal Hydrides and Open Dataset Contribution*. The archive includes Experiment Overview, the recorded and processed worksheets, PCI data, and apparatus geometry. The source LICENSE specifies [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The tables and figures are Study B analyses adapted from the authors' data.

The official ZIP contains 377,874,239 bytes. The published MD5 is `64cbe2a68c0af5dc2e4a0a9690003eac`. The verified SHA-256 and member inventory are in [source_manifest.json](source_manifest.json). The verifier reads the archive without extracting files. Keep the original ZIP outside Git.

```powershell
python study_b/verify_source.py "<archive-path>" study_b/source_manifest.json
```
