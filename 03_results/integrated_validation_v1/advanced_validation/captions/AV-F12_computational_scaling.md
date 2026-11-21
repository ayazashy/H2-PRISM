# AV-F12 — Actual computational scaling

**Scientific question.** How does runtime scale with sensors, hypotheses, window length, shifts and reference size?

**Caption.** Wall-clock time on AMD Ryzen 5 7520U with Radeon Graphics (8 logical CPUs, 7.2 GB, Python 3.12.1, NumPy 2.3.1), single process, one dimension varied at a time (others at 13 channels, 6 hypotheses, 151 samples, ±1 s). Formal D(Y): log–log slopes 1.02 (M), 0.98 (H), 1.06 (T) and 0.00 (S, early exit). D(x) on synthetic arrays: 0.70 in N over 1k–20k. Slopes describe this implementation over the measured range only; they are not complexity proofs.

**Interpretation limit.** One laptop-class CPU; Python allocations only for memory; synthetic arrays for D(x).

**Source data.**
- `advanced_validation/benchmarks/dy_scaling.csv`
- `dx_scaling.csv`
- `scaling_fits.csv`
- `hardware.csv`

**Code.** `scripts/fig_av.py::plot_av_scaling` · Files: `figures/AV-F12_computational_scaling.png`, `figures/AV-F12_computational_scaling.svg`
