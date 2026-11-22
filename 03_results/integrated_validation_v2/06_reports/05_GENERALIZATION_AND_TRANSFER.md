# Generalization and transfer

| Level | Status | Evidence |
|---|---|---|
| A — software portability | Demonstrated for HY2RES (one rule, one study) | Out-of-template: untested (no held-out template). HY2RES Level-A port of the frozen rule reproduced it exactly (True); certified SPECIFIC 0 vs frozen singleton 10,762; ambiguous 1,327 = 1,327; wrong certified SPECIFIC 0. |
| B — physics-based transfer | Not available | no qualified H2/blend model (A13) |
| C — empirical diagnostic generalization | BLOCKED_BY_DATA | 17/17 R2 test templates occur in training (L04); HY2RES and MHC have no labelled faults or locations |

- The Level-A port gives no evidence of Level-C generalization.
- MHC is a forecasting study with no diagnostic hypotheses, so no adapter was built.
- What would unblock Level C: R2 templates held out of development, or an external study with independently labelled events.
