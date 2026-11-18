# Reviewer-style critique (red team)

A skeptical review of this package. It assumes a reviewer who is looking for reasons to reject.

1. **What is actually novel?** A certificate-carrying three-outcome decision engine whose exclusions are independently re-verifiable, with a stated monotonicity proof. D(x) is not novel as a result: it shows no incremental value.
2. **What was independently demonstrated?** Nothing diagnostic. Only software and mathematical properties (H3) are established on hash-verified inputs.
3. **Does D(x) add measurable value?** No. Out-of-template log-loss worsens (0.906 → 0.995), and D tracks disputed attribution.
4. **What is the true contribution of D(Y)?** Fail-safe abstention semantics and auditable certificates, conditional on library completeness and on declared bounds.
5. **Is H1 estimable?** No: 12/12 PRIMARY rows are NOT_ESTIMABLE; the targets are unattainable.
6. **Could main results be explained by label defects?** Yes for R2: 7,347/8,012 errors lie in disputed runs.
7. **Dependence or leakage?** Templates are shared across folds (L04) and D encodes source-model signatures (L17). Intervals use ancestors.
8. **Are baselines competitive?** Confidence, margin, entropy and nearest-template baselines are included. No modern tuned classifier comparison exists (labels disputed).
9. **Are uncertainty intervals valid?** Ancestor bootstrap over 17 units is coarse; with one NORMAL ancestor, negative-control rates have no interval.
10. **Localization beyond one outlet?** No.
11. **Unjustified certainty?** Yes in two places: wrong SPECIFIC decisions under an incomplete library (2), and persistent wrong SPECIFIC decisions under delay or moderate bias, where selective risk rises.
12. **Monotonicity mathematically qualified?** Yes: proof with assumptions A1–A5. It does not cover perturbed data or library changes.
13. **Bounds physically defensible?** No. They are hypothetical; REF is a solver-refinement delta.
14. **Cross-domain generalization?** Not demonstrated (Level A only).
15. **Pure H2 / blends as tested?** No. BLOCKED_BY_PHYSICS.
16. **Costs real or hypothetical?** Compute time is measured; hardware cost scenarios are hypothetical relative units.
17. **Reproducible?** Yes for the v2 package (scripts, hashes, environment). The repository suite still has 13 pre-existing failures and 1 known blocker, all triaged.
18. **Strongest / most misleading figures?** Strongest: V2-F03 (isolability onset) and V2-F05 (certified port). Potentially misleading without its labels: V2-F02 (synthetic) and any R2 accuracy figure (disputed labels).
19. **What would invalidate central claims?** A forbidden transition or a failed certificate re-verification (H3); D(x) value appearing after D1 correction would reverse H2.
20. **Minimum work for a strong submission?** Record D1 and replicate; hold out templates; obtain independent captures to calibrate bounds; persist certificates (H10); re-record pins on LF bytes.

## Issues resolved in this round
- **Selective-risk rise under faults.** The figure caption had first reported only wrong-decision counts. It now also reports the rise in selective risk.
- **RQ1 count.** The registry first counted the H1 extract (6 rows). It now counts the registered R2 file (12 PRIMARY rows), consistent with v1.
- **Invariant total.** It is reported as hypothesis-status checks (consistent with v1), not as paired decisions.
- **Baseline audit.** It no longer leaves v1 QC records or governance files modified after running verifiers or tests.

## Unresolved
- L20, L21, L22 (owner or lead decisions).
- D1 (dataset owner).
- No held-out templates.
- No calibrated bounds.
- No price data.
