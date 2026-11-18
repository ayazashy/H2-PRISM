# Q1_H01 — Measurement architecture

**Scientific question.** Which measured quantities does the HY2RES record contain, and which are predicted?

**Caption.** Columns of the official HY2RES_202404.csv (Zenodo 15166733 v1; 300,768 rows at a 5 s PLC clock), grouped by published definition. Bold entries are the Study C prediction targets: buffer pressure pres_buf (bar), tank pressure pres_comp (bar; not identified as compressor-discharge pressure) and electrolyzer flow h2_flow (NL/h, over the preceding interval); the two fuel-cell targets are constant in the test period. Three columns have no published definition and are excluded. Missing counts from CHANNEL_SCHEMA.csv.

**Interpretation limit.** Grouping by published definitions; no plant topology is implied.

**Source data.**
- `03_results/hy2res_external_validation/publication/CHANNEL_SCHEMA.csv`

**Code.** `scripts/fig_hy2res.py::plot_hy2res_channel_architecture` · Files: `figures/Q1_H01_hy2res_channel_architecture.png`, `figures/Q1_H01_hy2res_channel_architecture.svg`
