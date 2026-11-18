# H1-F01 — Attainable coverage versus registered targets

**Scientific question.** Could the registered matched-coverage comparison be estimated at all?

**Caption.** Maximum attainable SPECIFIC coverage per outer fold of the registered run R2 (9,331 windows per fold). Center reaches 0.258, Downstream 0.722 and Upstream 0.736, so the primary target 0.80 is unattainable in every fold and 0.60 in Center; because a pooled result needs every fold, RQ1 is NOT_ESTIMABLE. Development maxima (threshold-transfer mode) are 0.569, 5.4e-05 and 0.035. The binding constraint is the specific-blocking support flags (fewer than two independent families or scenarios among a window's 25 nearest development neighbours).

**Interpretation limit.** Registered result; no threshold or flag is relaxed.

**Source data.**
- `h1_validation/analysis/h1_02_fold_feasibility.csv`
- `03_results/primary_protocol/PRIMARY/estimability.csv`

**Code.** `scripts/fig_h1.py::plot_h1_attainable_coverage` · Files: `figures/H1-F01_attainable_coverage.png`, `figures/H1-F01_attainable_coverage.svg`
