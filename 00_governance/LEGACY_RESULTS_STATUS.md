# Status of Legacy Stage 1 Results & Claims (Task F1 / Stage 2)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30  
**Status**: RETIRED / HISTORICAL ONLY

---

## 1. Explicit Status of Prior Historical Claims

In accordance with Section 1.2 of Ahmed's and Faisal's New Plans:
> *"No historical performance number may be presented as a current result unless reproduced and traceable."*  
> *"No claims of physical identifiability, metric localization, field validation, or pure-hydrogen data without corresponding verified evidence."*

| Historical Stage 1 Claim | Historical Metric | Stage 2 Audited Status | Scientific Resolution & Correction |
| :--- | :--- | :---: | :--- |
| **Pure Hydrogen Pipeline** | 100% pure $\text{H}_2$ | **REFUTED** | Raw dataset simulates a **10% $\text{H}_2$ / 90% $\text{CH}_4$ hydrogen-blend**. All research writing must reflect hydrogen-blend networks. |
| **Metric Acoustic Localization** | $\pm 650\text{ m}$ continuous | **REFUTED** | Sampling interval is strictly 1 Hz and labels are categorical valve restrictions (`leak_G3`–`G6`), not continuous millimeter coordinates. |
| **False Positive Rate (FPAR)** | 0.0% / 29.0% | **HISTORICAL** | Evaluated on preliminary 6-scenario subset with heuristic thresholding; retired. Stage 2 evaluates matched-coverage selective risk across all 123 scenarios. |
| **Balanced Accuracy** | 95.2% | **HISTORICAL** | Evaluated without full scenario family holdouts; retired. Stage 2 enforces 3-fold topology-stratified grouped cross-validation. |
| **Temperature Compensation** | Dynamic Line-Pack $T$ | **REFUTED** | The H2-SimNet dataset has **zero localized temperature sensors**. Prior temperature assumptions are retired. |

All Stage 1 scripts and results remain accessible in the **`old-main`** branch for historical auditability.
