# Acceptance Scores and Comparators (F8; implementation by A16)

- **Status:** SPECIFIED from `src/h2prism/comparators.py` and `combined_score.py`; IMPLEMENTED and TESTED (`tests/test_comparators.py`, `test_phase6_components.py`).
- **Direction:** higher always means more willing to issue SPECIFIC.

| Score (runner name) | Formula | Input | Missing behaviour | Role in RQ1 |
| --- | --- | --- | --- | --- |
| `confidence` C | max_k p_k | calibrated p | invalid p → UNRESOLVED (INVALID_INPUT) | B: confidence-only (secondary C vs B) |
| `margin` M | p_(1) − p_(2) | calibrated p | same | B2 (secondary) |
| `neg_entropy` −H | Σ_k p_k log p_k (0 log 0 := 0) | calibrated p | same | B3 (secondary) |
| `D_only` | D(x) | D(x) | NaN → never selected; UNRESOLVED (INVALID_SCORE) | D-only (secondary) |
| `s_C` | logistic P(correct \| logit C, M, −H, D); logit clipped at 1e-6 | calibrated p, D | rows with non-finite inputs → NaN score | **primary method** |
| `s_C_minus_D` | same model without D | calibrated p | same | **primary comparator (no-D ablation)** |

## Combined-score fitting (`fit_combined_score`)

- **Target:** correct = 1[argmax p_cal = y] on development windows.
- **Model:** `LogisticRegression(C=1.0)`.
- **Development scores:** cross-fitted over topologies (2 splits); used for development thresholds.
- **Final model:** fitted on all usable development rows and applied unchanged to the outer test (no refit).
- **Ablation:** s_C and s_C−D share the folds, probabilities, eligibility and decision rules; they differ only in the D input.
- **Interpretation:** C > B alone does not show that D adds value. C vs C−D is the direct test.
