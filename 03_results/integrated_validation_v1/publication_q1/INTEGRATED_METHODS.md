# H₂-PRISM integrated validation — Methods

## 1. Evidence sources

| Source | System | Data | Role |
|---|---|---|---|
| Center | Controlled Simscape network simulation. The gas model is air-like (R = 0.287 kJ/(kg·K)). | 12 accepted captures, 13 sensors, 0.2 s step | Mechanism, location and formal D(Y) evidence under declared conditions |
| R2 / H₂-SimNet | Three simulated pipeline topologies | 27,993 windows of 60 s, 128 features, 4 classes | Registered H1/RQ1 experiment |
| MHC (Study B) | Experimental dual-stage metal-hydride compressor | 29 workbooks; 3 held-out runs | Reference prediction on real hydrogen measurements |
| HY2RES (Study C) | Operational residential hydrogen system | 300,768 rows at 5 s | Reference prediction, drift and evidence validity |

**Integrity of the inputs:**

- Every input is a frozen or accepted artifact, identified by hash (T01).
- The integration branch `research/integrated-validation` merges the three accepted study branches. Commit `6eddd4a` separately repairs the 11 files that carried conflict markers.
- No frozen result, partition, mask, model or metric was modified, retrained or re-tuned.

## 2. Definitions

| Quantity | Definition |
|---|---|
| Coverage | C = Σ aᵢ / N, where aᵢ = 1 if a SPECIFIC decision is issued and N is all eligible windows of the evaluated set |
| Selective risk | R_sel = Σ aᵢ 1[ŷᵢ ≠ yᵢ] / Σ aᵢ. Undefined when Σ aᵢ = 0. AMBIGUOUS and UNRESOLVED decisions never count as correct SPECIFIC decisions |
| Paired difference | Δ_R(c) = R_sel(evidence policy) − R_sel(comparator) at a common rank-matched coverage c |
| D(x) | Top-1 minus top-2 class proportion among the k = 25 nearest development windows (z-scored features), excluding the query's own family |
| s_C, s_C−D | Logistic meta-scores P(correct \| logit confidence, margin, −entropy[, D]) |
| Formal D(Y) | (H_consistent, H_excluded, H_indeterminate) for declared hypotheses under declared bounds ε_total = ε_obs + ε_model per measurement kind, with a ±τ clock alternative. See the decision rule below |
| B3 RMS | Root-mean-square of channel-normalised template differences. Scale: pre-1000 s RMS of the SID 213 control per channel. Dimensionless |
| Recording increment | Smallest positive step between distinct recorded values of a channel. This is recorded quantization, not instrument resolution or accuracy |
| Rank probability | P(X_a > X_b) + ½ P(X_a = X_b) between two operating states (HY2RES) |

**D(Y) decision rule:**

| Condition | Decision |
|---|---|
| Exactly one supported hypothesis is consistent and no hypothesis is indeterminate | SPECIFIC |
| More than one hypothesis is consistent and none is indeterminate | AMBIGUOUS |
| Any hypothesis is indeterminate (INDETERMINATE_HYPOTHESES), or every hypothesis is excluded (MODEL_MISMATCH) | UNRESOLVED |

Unsupported hypotheses (no adapter) are always indeterminate.

## 3. Analyses

Study-level analyses are those accepted in each study package (Center enhancement, Study B and Study C enhancements). This package re-plots their verified tables. It adds:

- **(a)** The H1 analysis (`../h1_validation`, `H1_METHODS.md`).
- **(b)** Cross-study normalisation of errors by recording increment (T03, Q1_I02, Q1_I03). Values are shown side by side and never pooled.
- **(c)** Recomputed R2 independence units (Q1_I06).
- **(d)** Hash-verified extraction of two small Center trace windows through the frozen loader (`data/center_trace_windows.csv` with provenance).

## 4. Figure production

**Typography and style:**

- Times New Roman is resolved through `matplotlib.font_manager.findfont(..., fallback_to_default=False)` to `C:\Windows\Fonts\times.ttf`. It is used for rendering only and is never copied or embedded. SVG text stays live (`svg.fonttype = none`).
- Canvas, axes, legend and saved backgrounds are #FFFFFF.
- Palette: navy #17324D, teal #087E8B, blue #3B6F9C, burgundy #A44A4A, ochre #BA8A28, slate #64748B, grid #E5E7EB, text #20252B.
- Categories are also encoded by marker, line style or hatching, so they remain distinguishable in grayscale.

**Export:**

- PNG at 400 dpi: 3840 × 2160 px, or 3840 × 2400–2880 px where rows require it.
- SVG with a fixed hash salt and no date metadata.
- One caption file per figure.
- One plotting function per figure in `scripts/fig_*.py` (`h1_validation/scripts/fig_h1.py` for H1).

**Automated QA** (`scripts/q1qa.py`), run on every figure:

- Text clipping and pairwise overlap of drawn text. Hidden ticks are excluded.
- Minimum font size of 8 pt.
- Font family of every text artist.
- PNG long side ≥ 3200 px and dpi ≥ 400.
- Pure-white PNG border; no #F4F4E9 pixel.
- SVG parse: font families limited to Times New Roman, no embedded raster, no legacy background.

A figure is APPROVED only when every check passes. Every figure was also inspected visually at reduced size. Internal inspection sheets were kept outside the repository.

## 5. Statistical policy

- No p-values and no significance claims.
- **Intervals:**
  - The registered paired topology-stratified family bootstrap (2,000 replicates, seed 20261104).
  - A scenario-ancestor bootstrap added to expose the dependence of families across topologies.
- All intervals on R2 data are post hoc, because every outer-test window was inspected.
- Counts from repeated views of one capture family (Center) are reported as counts, never as rates of independent trials.

## 6. Research-question mapping

| Question | Statement | Registered operationalisation |
|---|---|---|
| RQ1 / H1 | Does the distinguishability assessment reduce selective risk at matched coverage? | Δ = R_sel(s_C) − R_sel(s_C−D) at rank-matched 0.80 (`02_methodology/STATISTICAL_ANALYSIS_PLAN.md`) |
| RQ2 | Does D(x) carry decision information beyond confidence, margin and entropy? | Protocol 2.0 development ablation |
| RQ3 | Does the policy produce valid SPECIFIC, AMBIGUOUS and UNRESOLVED outcomes? | Registered per-class outcome shares (`rq2.csv`, named "RQ2" in the 2026-11-04 methodology) |

This package uses the numbering of the Center enhancement and the audit (RQ1, RQ2, RQ3) and states the mapping here so the methodology documents can be traced.
