# Q1_I07 — Formal D(Y) qualification across studies

**Scientific question.** Where can formal D(Y) be evaluated at all?

**Caption.** Inputs required by the formal set-membership decision D(Y) = (H_consistent, H_excluded, H_indeterminate), per evidence source. Only Center provides configured events and locations, and its bounds are declared hypothetically (conditional hypothetical bounds — not calibrated uncertainty); three of nine declared Center hypotheses have no adapter. R2 used the empirical D(x), not D(Y). MHC and HY2RES have no event labels or locations, so D(Y) is blocked by evidence (TAB_B08, TAB_H09).

**Interpretation limit.** Studies differ in system, data type and evidence level and are not pooled; simulated (Center, H2-SimNet), experimental (MHC) and operational (HY2RES) evidence is reported side by side only.

**Source data.**
- `center TAB_C08`
- `study_b TAB_B08`
- `hy2res TAB_H09`

**Code.** `scripts/fig_integrated.py::plot_integrated_dy_qualification` · Files: `figures/Q1_I07_integrated_dy_qualification.png`, `figures/Q1_I07_integrated_dy_qualification.svg`
