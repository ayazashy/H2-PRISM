# ILLUSTRATIVE DEMO OUTPUT — NOT EXPERIMENTAL RESULTS

**Status:** QUARANTINED (moved here on branch `audit/preparation-integration`, pending Ahmed/Faisal decision)

Every file in this folder was produced by `scripts/visualize.py --demo` from **hard-coded or randomly generated numbers**.
No model was trained, no prediction was made and no H2-SimNet data was evaluated to produce them.

| File | How the plotted values were produced (`scripts/visualize.py`, commit 13c5512) |
| --- | --- |
| `fig3_confusion_matrix.png` | hard-coded 4×4 matrix `cm_demo` |
| `fig4_risk_coverage_curve.png` | analytic curves `0.02+0.12·cov³` (C), `0.03+0.16·cov^2.8` (C−D), `0.04+0.22·cov^2.5` (B) |
| `fig5_calibration_reliability.png` | `conf + N(0, 0.03)` random noise; ECE 0.024 and Brier 0.082 typed in by hand |
| `fig6_distinguishability_separation.png` | random draws from Beta(5,2) and Beta(2,5) |
| `dashboard_ILLUSTRATIVE.html` | embeds the figures above; the previous version showed invented KPI cards (accuracy 96.0 %, selective risk 8.1 % at 80 % coverage, ECE 2.4 %) |

These files previously lived in `03_results/figures/` and `03_results/dashboard.html`, the location of real
results, with no label. In particular `fig4` displayed the ordering C < C−D < B, which is the hypothesised
**positive answer to RQ1**, but no experiment supports it.

Rules (Ahmed plan §1.2; Faisal plan §1.1): *no fabricated metrics, plots, sample counts or experimental outcomes*.
These files may be used only as layout mock-ups, must keep the ILLUSTRATIVE label, and must never be cited in
the proposal, manuscript, poster, or presentations as evidence. Delete them or keep them here; that is a team decision.
