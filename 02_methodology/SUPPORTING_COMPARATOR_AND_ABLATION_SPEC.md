# Supporting Comparator and Ablation Specification (A16)

- **Status:** IMPLEMENTED and TESTED (`tests/test_comparators.py`, `tests/test_supporting_ablations.py`). Split out of `SUPPORTING_MODEL_SPECS_A14_A16.md` §A16.

| Item | Where it runs | Status |
| --- | --- | --- |
| Comparator library (C, M, H, −H, logit, simplex and D validation) | shared by the primary runner (`comparators.compute_comparators`) | integrated |
| B confidence-only, B2 margin-only, B3 −H-only, D-only | primary runner RQ1 secondary comparisons (rank-matched and threshold transfer) | integrated |
| No-D ablation | primary runner `s_C_minus_D` (primary comparator) | integrated |
| `confidence_and_margin` arm | `supporting_ablations.run_arm` only | module tested; not registered in the primary protocol, so exploratory |
| Thresholds | development-only `PolicyConfig`; labels removed before decisions (tested) | — |

Effect estimates, uncertainty and incremental-value claims stay with F10/F11.
