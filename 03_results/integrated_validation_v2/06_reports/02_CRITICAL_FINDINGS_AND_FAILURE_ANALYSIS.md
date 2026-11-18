# Critical findings and failure analysis

1. **Label/topology attribution (L01, critical).**
   - 7,347 of 8,012 classifier errors fall in disputed runs.
   - In undisputed runs, window accuracy is 0.938 against 0.714 overall.
   - D1 is unrecorded; the corrected replication is gated and BLOCKED_BY_PROVENANCE.
2. **D(x) tracks the artifact (L17).**
   - In Center, 1 − D ranks disputed windows with AUROC 0.084 (separation 0.916), but errors only with AUROC 0.393.
   - Out of template, adding D worsens the correctness model (0.906 → 0.995 log-loss).
3. **Library incompleteness (H9 CONTRADICTED).**
   - With the true mechanism removed, D(Y) issued 2 wrong SPECIFIC decisions and 4 candidate sets without the truth.
   - Its guarantees hold only for a complete library.
4. **Selective risk under synthetic faults.**
   - Moderate bias or drift (2 ε_obs) removes correct decisions first.
   - Wrong-specific risk therefore rises from 0.200 to 0.333, while the count of wrong decisions stays at the baseline.
5. **Delay beyond the clock allowance.** At delay 2 s with τ = 1 s: 0 correct and 2 wrong SPECIFIC decisions remain. The wrong ones persist while the correct ones vanish.
6. **HY2RES singleton calls are not certifiable.** 10,762 frozen calls become UNRESOLVED once a single-coordinate exclusion certificate is required.
7. **Reproducibility defects.**
   - L21: hash pins recorded on CRLF working copies fail on fresh checkouts.
   - L22: the v1 Q1 manifest name collides with the figure-system test (our own commit e944e1b).
   - L20: the Stage-2 pipeline is non-importable (owner decision).
8. **Traceability (H10).** The frozen export persists 7/16 required fields.
