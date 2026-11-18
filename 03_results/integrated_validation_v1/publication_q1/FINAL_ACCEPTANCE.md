# Integrated validation and Q1 package — acceptance

**Decision: ACCEPTED WITH LIMITATIONS (package level).**

This decision covers the integrity, reproducibility and presentation of the package. It does **not** assert that H1 is supported: H1 remains NOT_ESTIMABLE (`../h1_validation/H1_ACCEPTANCE.md`). Acceptance by a journal is not guaranteed.

| Gate | Result | Evidence |
|---|---|---|
| A — Repository integrity | PASS | Studies integrated on `research/integrated-validation`. The conflict repair is a separate commit (`6eddd4a`). `git diff --diff-filter=MD 6fee8a0 HEAD` is empty. The package is additive: `git status` shows no tracked modification. |
| B — Original H1 result integrity | PASS | `rq1.csv`: 12/12 primary-contrast rows NOT_ESTIMABLE (asserted in `h1_analysis.py`). Nothing in the package replaces this verdict. |
| C — Evaluation eligibility | PASS (exploratory) | The shared-coverage grid was fixed earlier by the R2 diagnostics. The tie key is the registered one. 161/161 reproduction checks match. All new comparisons are labelled EXPLORATORY_POST_HOC with explicit denominators and independence units. |
| D — Baseline fairness | PASS | Identical eligible windows, exact counts and tie key for all registered scores. The conventional baseline differs only by the evidence guard, and this is disclosed. |
| E — Formal D(Y) integrity | PASS | Every D(Y) figure and table carries CONDITIONAL_HYPOTHETICAL_BOUNDS and "not calibrated uncertainty". Semantics are unchanged. Universe consistency is asserted. |
| F — Numerical verification | PASS | `quality_control/NUMERICAL_VERIFICATION.csv`: 273/273 checks, covering figure hashes, QA status, size and dpi, the font, table reconciliations against source tables, H1 checks and tracked-file status. |
| G — Figure quality | PASS (automated + visual) | 55 Q1 and 9 H1 figures APPROVED. Automated checks found no clipping, no text overlap and no font below 8 pt. Every figure was inspected visually at reduced size, and defects were fixed before approval. |
| H — Typography and export | PASS | Times New Roman resolves to `C:\Windows\Fonts\times.ttf`. White PNG borders; no #F4F4E9. PNG 3840 × 2160–2880 px at 400 dpi. SVGs parse with live Times New Roman text and contain no raster. No PDF exports. |
| I — Frozen-file preservation | PASS | No tracked file modified. Center (44), MHC (10) and HY2RES (6) tests pass. R2 parquet hashes equal the pinned manifest. *The Center `baseline_freeze --verify` needs `data/raw`, which is absent from this worktree; preservation of the 410 frozen files is shown through Git instead.* |
| J — Reproducibility | PASS | Two consecutive full builds were byte-identical for all 55 figures (PNG and SVG). The H1 pipeline was re-run (see the H1 acceptance record). Commands are in `REPRODUCE.md`. Checksums are in `../SHA256SUMS.csv`. |
| K — Claim qualification | PASS | T10 and Q1_I09: no fault classification, localization accuracy, certified D(Y), industrial transfer or novelty claim. |
| L — Governance | PASS | D1 is NOT_RECORDED, so the corrected-attribution replication was not run. Protocol 2.0 is not approved and was not run. |

**Limitations:** `INTEGRATED_LIMITATIONS.md`.

**Historical figures:** all 191 tracked historical PNG/SVG files are unchanged. Their eligibility and Q1 replacements are listed in `quality_control/FIGURE_INVENTORY.csv`.
