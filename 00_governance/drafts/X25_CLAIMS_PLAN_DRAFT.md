# DRAFT — Publication claims plan. Action X25 (issues E-06, E-07, G-08)

Status: **DRAFT, owner decision required (project lead).** Nothing here is published.

## 1. Required disclosure (C16) on every artifact derived from the released data

> The released simulation models use an air-like gas specification (specific gas constant 0.287 kJ/(kg·K); perfect-gas γ = 5.75 and Pr = 0.079, both physically inconsistent). Results derived from these data characterise the released simulator, not hydrogen. See `05_documentation/GAS_MODEL_LIMITATION.md`.

## 2. Negative and inconclusive results that must be reported (E-06)

| Result | Source |
|---|---|
| Group-balanced risk saturates at 1/11, so arm comparisons are not resolvable at that endpoint. | Arm H diagnostic |
| D(x) saturates; E_h is undefined for 79.6 % of windows; v2 is undefined for 100 % of the current data. | — |
| Sampled v2 calibration misses the 1 % criterion for θ_det (1.2–1.5 %). | X26 |
| The H2–CH4 default flash fails in CoolProp for H2-rich blends. | X20 probe |
| The blend claim is refuted. | Earlier correction |

## 3. Claims not permitted until the stated evidence exists

| Claim | Requires |
|---|---|
| Any superiority of distinguishability over confidence-only | X17 confirmatory contrast on the sealed partition |
| Hydrogen-network validity | X07 V2–V8 PASS |
| Industrial applicability | X23 field data |
| Cross-gas validity | X20 under a new authorization |

## 4. Sources of truth (G-08)

- `00_governance/MASTER_ISSUE_REGISTER.csv` (baseline)
- `00_governance/ISSUE_CLOSURE_MATRIX.csv` (current status)
- `00_governance/EXECUTION_COMPLETION_REPORT.md`

Older gap documents are superseded where they conflict with these.
