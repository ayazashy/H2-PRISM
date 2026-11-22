# H1 comparative analysis

Numbers: `tables/H1-T03.csv`, `H1-T04.csv`, `H1-T05a/b.csv`. Status: EXPLORATORY_POST_HOC unless stated.

## 1. What each comparison isolates

| Comparison | Isolates | Information difference | Fair? |
|---|---|---|---|
| s_C vs s_C−D (registered) | D(x) inside the meta-model | D(x) only | yes: identical predictions, eligibility, counts and tie key |
| s_C vs guarded confidence / margin / −entropy | meta-model + D(x) vs one conventional score | meta-model inputs | yes (same eligibility) |
| s_C vs D_only | combined score vs neighbourhood statistic alone | classifier probabilities | yes |
| s_C vs conventional confidence (no guard) | whole evidence layer (support flags + meta-model + D) vs H1's conventional baseline | flags, which use development neighbourhood family counts | same windows and counts. The tested component legitimately uses development-reference information that the baseline lacks |

## 2. Registered contrast: D(x)

- **Risk differences:** Δ(s_C − s_C−D) is 0, −0.100, −0.134, −0.088, −0.006 at 0.05–0.25.
- **Intervals:** every family- and ancestor-level interval includes 0.
- **Windows exchanged:** adding D(x) exchanges 1,272–2,066 windows per grid point.
  - The windows only s_C−D accepts contain 0–563 errors.
  - The windows only s_C accepts contain 0–29.
  - Those errors come from 1–3 scenario ancestors, all in Center runs with disputed attribution.
- **Undisputed runs:** neither policy makes an error at any grid point.

**Reading.** The registered contrast has no information about diagnostic errors that are independent of the attribution defect. A negative point estimate here is not evidence for H1.

## 3. The evidence layer against conventional abstention

- **Risk differences:** Δ is −0.467 to −0.277.
  - Family intervals exclude 0 at 4/5 grid points.
  - Ancestor intervals exclude 0 at 3/5.
- **Errors blocked by the guard:** 6,271 of 8,012 classifier errors (78.3 %).
  - Error rate is 0.523 among blocked windows and 0.109 among eligible windows.
- **Errors issued as SPECIFIC across the grid:**
  - Conventional confidence: 467–2,300 Center errors and 187–655 Downstream errors.
  - Evidence policy s_C: 0–1,019 Center errors and 0 Downstream errors.

**Reading.** This is the strongest positive *descriptive* signal. The evidence-support flags identify windows whose neighbourhood rests on a single independent family. Here those coincide with windows from misattributed runs.

**Why it is not H1 evidence:**

- This is consistent with the guard detecting unsupported or out-of-distribution evidence.
- It is not shown on independently labelled diagnostic difficulty, and it was not pre-registered as the primary contrast.
- The R2 windows were inspected.

## 4. Score ranking (correctness AUROC, eligible windows)

| Score | Center | Downstream |
|---|---|---|
| s_C | 0.981 | 1.000 |
| s_C−D | 0.522 | 1.000 |
| confidence | 0.983 | 0.000 |
| −entropy | 1.000 | 0.000 |
| D only | 0.565 | 0.316 |

- In Downstream, every conventional score is perfectly anti-informative.
- In Center, D(x) brings the meta-model up to, but not above, the conventional scores.
- No score is uniformly best, and the extreme values are artefacts of a few confidently wrong runs.

## 5. Development ablation (exploratory, development windows)

- **Where estimable:** s_C = s_C−D = confidence.
  - G1: 0.091.
  - C: 0.045.
  - A, D, E: 0 vs 0 floor.
- **Not estimable:** B and F.
- **G2:** the AUROC gain of s_C over s_C−D (+0.121) rests on one fold, because the meta-model is undefined in 2 of 3 folds.

## 6. Formal D(Y) vs conventional scores

No shared-scenario comparison exists, so D(Y) and the classifier policies cannot be ranked against each other.

**What D(Y) adds that a confidence score cannot:**

- the ability to return UNRESOLVED because the declared hypothesis library is incomplete (full universe: 336/336);
- exclusion statements in physical units under declared bounds.

**Its weakness:** when the library is incomplete and the universe is restricted, it decides wrongly (11/11 wrong SPECIFIC with unsupported truth).
