# H1 and localization assessment

## A. H1 verdict

| Test | Verdict |
|---|---|
| Registered R2 test | **NOT_ESTIMABLE** (unchanged; 12/12 rows) |
| Exploratory reanalysis | **INCONCLUSIVE** |

**What the exploratory reanalysis shows (Results R1–R3):**

- At coverage 0.25, s_C has the lowest point risk: 0.146 (1,019 wrong of 6,999 SPECIFIC). The other policies:

  | Policy | Risk at 0.25 |
  |---|---|
  | s_C−D | 0.152 |
  | Guarded confidence | 0.238 |
  | Conventional confidence abstention | 0.422 |
  | No abstention, at coverage 1 | 0.286 |

- Every interval for the registered contrast includes 0.
- All of s_C's wrong decisions lie in runs whose topology attribution is disputed.
- Outside those runs, neither s_C nor s_C−D makes a single error at any grid point.

**Part of the apparent benefit explained by the corrupted labels.**

- 7,347 of the 8,012 classifier errors lie in disputed runs.
- The remaining 665 errors sit in one undisputed Downstream NORMAL run, and Experiment F attributes them to the swapped training composition.
- The evidence guard's advantage over conventional abstention therefore comes entirely from withholding errors that the defect creates:
  - 2,300 of conventional abstention's 2,955 errors at 0.25 are in disputed runs;
  - the remaining 655 are the NORMAL → LEAK errors of that single template.

**Why the registered test is still not estimable.** The Center fold can reach at most 0.258 coverage under the registered support flags, below the registered targets. The 0.80 target is also unreachable in the other two folds (0.722, 0.736).

**Obstacle to a stronger conclusion.** The R2 data contain no error that is independent of the attribution defect. Every test template also appears in the training topologies (17/17), so out-of-template generalization was never tested.

**Smallest experiments that would materially strengthen H1:**

1. Yazan records D1. Then run the corrected exploratory replication with `h1_analysis.py` on its outputs. It shows whether nonzero, independent errors and a shared coverage region exist.
2. Run new scenario templates that are disjoint from the development templates, with ≥ 2 independent templates per class. Confirm before unblinding that 0.80 coverage is attainable on development data.
3. Run the confirmatory test under `../h1_validation/H1_CONFIRMATION_REQUIREMENTS.md`.

## B. Classification and localization

**Classification on eligible cases (R2, inspected, exploratory):**

| Policy | Accuracy |
|---|---|
| No abstention | 0.714 (19,981 / 27,993) |
| s_C at coverage 0.25 | 0.854 (5,980 / 6,999) |
| Undisputed runs (each topology's NORMAL run plus all Upstream runs) | 1.000 in Center and Upstream; 0 in Downstream (its one NORMAL run, 665 windows, wrong) |

These are window-level figures on inspected data from 17 templates, not a population accuracy.

**Localization (Results R9).**

- **Highest level demonstrated:** Level 2, correct categorical outlet identification, for **one outlet (SID 213)**.
  - It rests on **two near-duplicate captures**: the alternate profile differs only by a +0.005 MPa overlay. That is **one independent location**.
  - SID 312 and SID 215 cannot be estimated, because neither has an independent template.
- **Ranking metrics:** MRR = 1.0 over the 3 supported query×condition rows. Forced ranking is wrong for both unsupported outlets.
- **H-Loc (exploratory):** at matched coverage 0.5, neither the margin-ranked nearest template nor formal D(Y) names a wrong outlet (0/2 and 0/8). Without abstention the nearest template is wrong in 2/4 cases. With one supported location no rate generalizes.
- **Not demonstrated:** Levels 3–5.
