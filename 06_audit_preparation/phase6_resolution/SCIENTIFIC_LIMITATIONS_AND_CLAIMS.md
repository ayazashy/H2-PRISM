# Scientific Limitations and Claims (Phase 6 candidate; PENDING Ahmed signoff)

This updates `phase4_approvals/SCIENTIFIC_CLAIM_AND_LIMITATION_REGISTER.md`; nothing listed there is weakened.

## Permitted (verified)

- The official H₂-SimNet V2 data were used unaltered: 57 simulated runs in 3 withdrawal topologies; 1 s sampling; 16 sensor channels.
- The candidate folds are family- and duplicate-disjoint; the pipeline is deterministic and cross-platform reproducible (software properties).
- The D(x), comparators, policy, combined-score and bootstrap code implement their stated definitions (tested).

## Conditional (permitted only after the experiment, with these qualifiers)

- "Within held-out withdrawal topologies of the simulated network, D(x) changed or did not change selective risk at matched coverage by X [interval conditional on 3 topologies]."
- Rates of the three outcomes and their reproducibility (RQ2), using the operational criteria in `AHMED_RESOLUTION.md` C2.
- Per-class results for NORMAL, FAULT and DELAY: **descriptive only**.

## Unsupported (prohibited)

Real-world deployment readiness · field validation · generalisation to industrial or unseen networks · physical identifiability · metric leak localisation · pure-hydrogen behaviour · a verified 10% H₂ / 90% CH₄ composition · superiority or novelty of D(x) · any Stage 1 historical metric · any value from the quarantined illustrative figures.

## Mandatory limitations

1. Simulation only.
2. 3 topologies.
3. 3 independent runs each for NORMAL and DELAY; 3 weak/strong families for FAULT.
4. Phase–event confounding by design (fault onsets at 25 s).
5. Annotation conflicts: G5G6 location; `brokenC1G5_weak`; delay offset.
6. Ancestry of 19 run pairs unresolved (sensitivity map registered).
7. Development folds hold one family per thin class, so thresholds and SPECIFIC availability are LEAK-driven.
8. Windows are dependent.
9. Bootstrap intervals are conditional, not generalisation intervals.
