# Reproduce the Study C publication package

From the root of the enhancement branch, run the following command with Python 3.12.1, NumPy 2.3.1, pandas 2.3.3, Matplotlib 3.10.7 and Pillow 12.0.0.

```powershell
python 03_results/hy2res_external_validation/publication/build_publication.py --output study-c-rebuilt
```

The command reads the immutable source CSV and archived products at their original repository paths. It regenerates the numerical analysis CSVs, all PNG/SVG figures, and the contact sheet. This is an archive verification and publication build. Model fitting is outside this command. The narrative reports and the evidence matrix are curated files alongside the script.

The command checks the publisher MD5, row order and timestamps, split boundaries, segment IDs, lag availability, operating-state construction, target values and persistence predictions against source rows. It reconciles every archived held-out MAE, RMSE and denominator, including undefined metrics. The prior independent review replayed the original notebook code in a separate copy and verified the ridge predictions within numerical tolerance.

To inspect vector output, open the SVG in an editor with DejaVu Sans installed. The PNG and SVG share a Matplotlib figure specification. Bitmap figures export at 400 dpi and 5120 × 2880 pixels. The contact sheet uses downsampled thumbnails of individual PNGs.
