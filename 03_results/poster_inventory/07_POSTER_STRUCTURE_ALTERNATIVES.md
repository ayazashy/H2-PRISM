# 07 — Poster Results structure alternatives

## Constraints that bound every alternative

- **Area.** Results area 840 × 600 px (7:5).
- **Figure format.** Every candidate figure is 3840 px wide with 10 pt labels at 400 dpi.

  | Width in the area | Label height | Share of area height | 16:9 figure height |
  |---|---|---|---|
  | Full (840 px) | about 12 px | 2.0% | 472 px |
  | Half (410 px) | about 5.9 px | 1.0% | 231 px |
  | Third (270 px) | about 3.9 px | 0.65% | 152 px |

- **Practical capacity.** One dominant figure plus 2–3 compact items, or four half-width figures at the legibility floor. Whether 1% of area height is legible depends on the printed poster size, which the team controls.
- **Aspect ratio.** Most figures are 16:9 (1.78), wider than the 7:5 area (1.40). Two half-width 16:9 figures stacked twice use 462 px of the 600 px height, leaving about 138 px for stage titles and captions.
- **Background.** Candidate figures are #FFFFFF; the poster is #F4F4E9. The originals of the Center, HY2RES and MHC figures exist in #F4F4E9 but are superseded redesigns, in a different typeface.

Space shares below are fractions of the Results area, provisional only.

---

## Alternative A — Capability-first: from verified exclusions to engineering limits (4 stages)

**Contribution argued:** H₂-PRISM's defensible contribution is a certified three-outcome decision engine whose behaviour, limits and sensor dependence are measured.

| # | Stage title | Core question | Primary | Supporting | Share |
|---|---|---|---|---|---|
| 1 | Certified exclusions are never created by information loss | Are D(Y) exclusions sound? | `AV-F05_dy_status_transitions.png` | table `A04a.csv` | ~15% (compact) |
| 2 | What the sensors can separate | Which hypothesis pairs are formally separable, and why not Normal vs SID 215? | `V2-F03_isolability_onset.png` | `V2-F04_structural_incidence.png` *or* table `A16b.csv` | ~30% |
| 3 | How the engine decides, and when it is wrong | What do SPECIFIC / AMBIGUOUS / UNRESOLVED look like on real captures? | `Q1_C15_center_dy_evidence_breakdown.png` | `AV-F04_library_completeness.png` | ~35% |
| 4 | Robustness and limits | How do sensor loss, faults and timing change decisions; what remains unestablished? | `AV-F08_missing_sensor_robustness.png` | subset of `HYPOTHESIS_REGISTRY.csv` (id, name, status) | ~20–25% |

- **Reading order:** 1 → 2 → 3 → 4, left-to-right then top-to-bottom. Stage 3 is the visual anchor.
- **Advantages:** follows the dependency chain F1→F5 (`06_…`), each stage answering the question raised by the previous one. Leads with the only SUPPORTED_WITHIN_SCOPE hypothesis (H3). Shows the key limitation (AV-F04) next to the result it qualifies.
- **Overcrowding risk:** high if both stage-2 items and both stage-3 items are kept at full detail (6 figures). Minimum version: AV-F05, V2-F03, Q1_C15, AV-F08 plus a 10-row status list.
- **Possible misinterpretation:**
  - isolability read as accuracy (stage 2);
  - Center counts read as rates (stage 3);
  - hypothetical bounds read as sensor specifications.
  - Every figure carries its stamp; captions need the denominators (42 cells, 24 decisions, 6 captures).
- **Omitted:** the R2 learned-score branch (H1 NOT_ESTIMABLE, label defect, D(x) negative result), HY2RES portability, gas qualification. Only the registry subset carries them, so a reader could miss that the registered hypothesis failed to be testable.

## Alternative B — Question-first: from the registered hypothesis to the defensible contribution (3 stages)

**Contribution argued:** the registered selective-risk hypothesis could not be tested; the data defect and D(x)'s lack of value are demonstrated; the certified engine is what survives.

| # | Stage title | Core question | Primary | Supporting | Share |
|---|---|---|---|---|---|
| 1 | The registered test is not estimable, and errors trace to disputed labels | Can H1 be evaluated, and what drives errors? | `H1-F01_attainable_coverage.png` | `AV-F02_false_specific_equal_coverage.png`; table `V2-T09_r2_run_level.csv` | ~35% |
| 2 | D(x) adds no information beyond confidence | Is the evidence score useful out of template? | `V2-F01_dx_incremental_value.png` | `H1-F02b_paired_risk_difference.png` *or* table `V2-T01_dx_incremental_utility.csv` | ~30% |
| 3 | What remains defensible: certified three-outcome decisions | What does the formal engine guarantee and decide? | `Q1_C15_center_dy_evidence_breakdown.png` | `AV-F05_dy_status_transitions.png` / table `A04a.csv` | ~35% |

- **Reading order:** 1 → 2 → 3. A negative-to-positive arc.
- **Advantages:** scientifically candid; matches the registered research question; strongest protection against reviewers who expect the H1 result.
- **Overcrowding risk:** moderate. Five figures plus two tables is too many; keep one supporting item per stage.
- **Possible misinterpretation:**
  - AV-F02's hatched bars must be read as disputed-attribution runs, not as model failure;
  - V2-F01 (b) is synthetic.
- **Omitted:** isolability, sensor robustness, timing, computation, transfer. The engineering value of the engine is under-shown.

## Alternative C — Claim ledger: verified, conditional, negative (3 stages)

**Contribution argued:** an evidence-calibrated account of what H₂-PRISM has and has not established, organised by evidence class.

| # | Stage title | Core question | Primary | Supporting | Share |
|---|---|---|---|---|---|
| 1 | Verified | What holds without assumptions about bounds or labels? | table `A04a.csv` | table `A14b.csv` (scaling exponents) | ~20% |
| 2 | Conditional on declared bounds (Center) | What the engine separates and decides under hypothetical bounds | `Q1_C15_center_dy_evidence_breakdown.png` | `V2-F03_isolability_onset.png` | ~45% |
| 3 | Negative, exploratory or blocked | What failed, and what is not yet testable | `V2-F06_hypothesis_evidence_summary.png` | `V2-F01_dx_incremental_value.png` *or* `AV-F04_library_completeness.png` | ~35% |

- **Reading order:** 1 → 2 → 3, with V2-F06 as the closing summary.
- **Advantages:** the clearest separation of evidence classes, so misreading risk is minimal. Every hypothesis status is visible (V2-F06).
- **Overcrowding risk:** low to moderate. V2-F06 is a 10 × 10 matrix; at half width its criterion labels (C1–C10) are fine, but the hypothesis names are small.
- **Possible misinterpretation:**
  - V2-F06 colour cells can be read as quality scores rather than criterion statuses;
  - stage 1 tables may look thin to a non-specialist.
- **Omitted:** sensor robustness and timing (AV-F08, AV-F09), the label-defect evidence (AV-F02), HY2RES portability. These are visible only through V2-F06's statuses.

---

## Ranking (scientific communication, not attractiveness)

1. **Alternative A.**
   - Most coherent progression: each stage answers the previous stage's question (`06_…`).
   - Centred on the contribution the evidence actually supports (H3 plus conditional engineering behaviour).
   - Keeps its main limitation (AV-F04) adjacent.
   - Weakness: it can hide the registered-hypothesis outcome. That is mitigated only if the stage-4 status list is kept and names H1 NOT_ESTIMABLE and D(x) as negative.
2. **Alternative B.**
   - Most candid about the registered hypothesis and the data defect.
   - But it gives the engine's engineering behaviour little space and opens with two negative stages, which de-emphasises the supported contribution.
   - Strongest choice if the poster's audience expects an H1 answer.
3. **Alternative C.**
   - Most rigorous classification, but least narrative: the reader learns statuses rather than following a scientific question.
   - Best as a closing panel or a companion handout.

A hybrid of A's four stages, with B's stage 1 compressed into A's stage 4, is supported by the evidence. Choosing it, or any final layout, is the team's decision.
