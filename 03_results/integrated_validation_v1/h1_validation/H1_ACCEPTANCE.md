# H1 analysis — acceptance

**Analysis status:** ACCEPTED AS EXPLORATORY ANALYSIS. This decision covers the integrity and correctness of the analysis, not support for H1.

**H1 verdict:**

- **NOT_ESTIMABLE** under the registered protocol. The verdict is unchanged.
- The exploratory reanalysis gives **EXPLORATORY EVIDENCE ONLY** and is **INCONCLUSIVE**.

| Gate | Result | Evidence |
|---|---|---|
| A — Repository integrity | PASS | Additive files only; no tracked file modified |
| B — Original H1 result | PASS | All 12 primary-contrast rows of `rq1.csv` are NOT_ESTIMABLE (asserted). No verdict is replaced. |
| C — Evaluation eligibility | PASS, labelled exploratory | Registered tie key and exact counts. The grid was fixed before this analysis. The R2 parquet hashes equal the pinned diagnostics manifest. Denominators and independence units are stated (39 families, 17 ancestors). All windows are disclosed as inspected. |
| D — Baseline fairness | PASS | Identical eligible windows and counts for the registered scores. The conventional baseline differs only by the evidence guard, and this is disclosed. |
| E — Formal D(Y) integrity | PASS | Conditional hypothetical bounds stated. Unsupported-truth assertion: 11/11 wrong SPECIFIC have unsupported truth, and 0/48 with supported truth are wrong. |
| F — Numerical verification | PASS | 161/161 reproduction checks against the frozen R2 outputs (`analysis/h1_verification.csv`). The checks include the registered family-bootstrap intervals, reproduced exactly. |
| G/H — Figures | PASS | 9 figures APPROVED by automated QA and inspected visually. Times New Roman, white background, 3840 px PNG at 400 dpi, and SVG with live text. |
| I — Frozen preservation | PASS | Read-only access to the frozen R2 files; nothing written outside `h1_validation/` |
| J — Reproducibility | PASS | Full rerun (analysis → tables → figures) produced identical bytes for all 41 outputs. Bootstrap seed 20261104. |
| K — Claim qualification | PASS | H1 is neither supported nor refuted. No significance claim. Exploratory, conditional and blocked components are separated (H1-T07, H1-F07). |
| L — Governance | PASS | D1 is NOT_RECORDED, so Experiment F (corrected-attribution replication) was not run. The minimum approval is specified in `H1_EXECUTION_DECISION.md` §8. |

**Success criteria for the exploratory registered contrast** (fixed in the decision record §10):

| Criterion | Status | Evidence |
|---|---|---|
| (1) Δ < 0 at every grid point | Not met | Δ = 0 at 0.05 |
| (2) Intervals exclude 0 | Not met | No interval excludes 0 |
| (3) Discordant errors from ≥ 3 ancestors | Partly met | 3 ancestors at 0.20 and 0.25; 0, 1 and 2 at 0.05, 0.10 and 0.15 |
| (4) Nonzero difference outside disputed runs | Not met | Zero errors for both policies |

**Outcome:** INCONCLUSIVE, as pre-stated.
