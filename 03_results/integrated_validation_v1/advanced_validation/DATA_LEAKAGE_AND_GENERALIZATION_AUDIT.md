# Data leakage and generalization audit

The machine-readable register is `tables/A03.csv` (16 entries). This document summarises it.

## Confirmed defects and risks

| ID | Finding | Impact |
|---|---|---|
| L01 | **Label/topology attribution defect.** 36 of 57 R2 runs carry the other topology's source model. 7,347 of 8,012 classifier errors fall in those runs. | Uncorrected; D1 pending. |
| L04 | **Shared generating templates across held-out topologies.** In every fold, 17 of 17 test templates also appear in the training topologies, while the families are disjoint. | The "held-out topology" design never tests out-of-template generalization. |
| L03 | **Near-duplicate captures.** On Center, the alternate profile reproduces SID 213 up to a +0.005 MPa overlay. PS3 and PS10 are bitwise identical channels. | Disclosed. |
| L09 | **Self-template matching.** The frozen Center library recognises 7/7 queries by self or near-duplicate matches; only 3/5 supported queries are recognised once self-templates are excluded. | Corrected in analysis (leave-own-template-out). |
| L10 | **Source-model signatures in features.** The extended sensor set exists only in the down model. Center LEAK windows draw 85 % of their neighbours from the same source model. | Confirmed risk, tied to D2. |
| L08 | **Protocol 2.0 ablations reused inspected windows.** | Exploratory only. |

## Checked and not found

- **L02:** exact duplicate captures. Hashes are unique: 13/13 Center, 57/57 R2.
- **L06:** row-level splits. MHC is split by run; HY2RES chronologically, with an embargo and zero shared segments.
- **L07:** preprocessing or calibration fitted on evaluation data.
- **L12:** post hoc choice of evaluation points (the grid was fixed beforehand).

## Unverified

- **L15:** the HY2RES model-training code is not tracked, and the historical test-access seal is unverified.

## Overfitting

The data do not support a capacity-overfitting reading:

- The R2 train/test gap is **inverted** in two folds:

  | Fold | Inner-CV macro-F1 | Outer accuracy |
  |---|---|---|
  | 1 | 0.739 | 0.213 |
  | 2 | 0.304 | 0.929 |
  | 3 | 0.099 | 1.000 |

- These gaps are explained by **label corruption and distribution shift** (L01, L10), not by model capacity.
- In the runs with consistent attribution, Center and Upstream are 100 % correct and Downstream is 0 %. Downstream's undisputed run is a single NORMAL run of 665 windows that carries the training-composition defect.

## Out-of-template generalization

**Untested: zero evidence.** No evaluation template is absent from development.
