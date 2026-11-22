# 04 — Figure critical review

All 204 logical figures (408 files) are listed in `01_COMPLETE_FIGURE_INVENTORY.csv`. Contact sheets are in `gallery/CONTACT_*.png`, and `gallery/GALLERY.html` links every thumbnail to its original file. I reviewed the contact sheets visually for the curated sets (Q1 Center, Q1 HY2RES, Q1 Integrated, H1, AV, v2) and for the approved R2 finals and the Center atlas poster exports. The MHC sets were assessed from their manifests, captions and the v1 inventory, not visually at full size.

## Suitability scale

The scale is evidence-based, not aesthetic.

| Level | Meaning |
|---|---|
| **S1 — primary candidate** | Valid evidence, central to H₂-PRISM's contribution, self-explanatory, faithful to its source |
| **S2 — supporting candidate** | Valid, but secondary or needs its neighbour figure to be understood |
| **S3 — context only** | Valid, but peripheral (reference prediction, schematics) or dense |
| **X — do not feature** | Superseded, invented, engineering QC, misleading without heavy qualification, or illegible at poster scale |

## Group-level verdicts (all 204 logical figures)

| Group (`gallery_group`) | n | Lifecycle | Verdict | Reason |
|---|---|---|---|---|
| V2_validation | 6 | FINAL, QA APPROVED | S1/S2 | Newest analyses; isolability onset, D(x) negative result, HY2RES port |
| AV_advanced | 16 | FINAL, QA APPROVED | S1/S2 | Formal integrity, robustness, isolability, computation |
| H1_validation | 9 | FINAL, QA APPROVED | S1/S2 | Registered H1 status and exploratory selective risk |
| Q1_Center | 19 | FINAL, QA APPROVED | S1–S3 | D(Y) decision behaviour and observability; C12a–d and C13a/b are dense |
| Q1_Integrated | 9 | FINAL, QA APPROVED | S2/S3 | Cross-study synthesis; I01 is a schematic |
| Q1_HY2RES | 14 | FINAL, QA APPROVED | S3 (H10/H11/H12 S2) | Forecasting study; abstention-cause figures relevant |
| Q1_MHC | 13 | FINAL, QA APPROVED | S3 | Forecasting reference, no diagnosis |
| R2_figsys_final | 3 | FINAL (PUBLICATION_MANIFEST) | X for poster (S3 archival) | Approved, but multi-panel, small type, < 3200 px; Q1/H1 replacements exist |
| Center_enhancement, HY2RES_enhancement, MHC_enhancement | 35 | SUPERSEDED_BY_REDESIGN | S3 alternative | Same data as Q1 versions; **#F4F4E9 background matches the poster**; sans-serif, footnotes inside canvas |
| Center_atlas (+ poster exports) | 14 | SUPERSEDED_BY_REDESIGN / SUPERSEDED | X | Older multi-panel layouts, text as paths; frozen formal state only |
| HY2RES_publication, HY2RES_distinguishability | 10 | SUPERSEDED_BY_REDESIGN | X | DejaVu Sans multi-panel; replaced by Q1_H |
| MHC_original | 3 | SUPERSEDED_BY_REDESIGN | X | Replaced by Q1_B |
| R2_figsys_other | 17 | SUPERSEDED / PRELIMINARY | X | Superseded run keys; preliminary renders |
| R2_dataset_design | 2 | SUPERSEDED_BY_REDESIGN | X | Replaced by Q1_I06; superseded manifest has broken paths |
| Stage2_pipeline | 6 | SUPERSEDED | X | Pre-registration Stage-2 outputs, superseded by R2 |
| HY2RES_early, Center_working | 8 | SUPERSEDED | X | Working figures |
| Engineering_verification | 8 | RETAINED | X for Results | Solver and convergence QC, not results |
| Illustrative_demo | 4 | OBSOLETE | **X — never** | Invented values |
| Planning_documents | 8 | NOT_RESULTS | X | Project-plan PDFs |

## Detailed review of candidate figures

Shared format for every figure below:
- PNG 3840 px wide at 400 dpi, with an SVG carrying live Times New Roman text.
- Background #FFFFFF. On the #F4F4E9 poster this shows as a white panel, so the frame decision is the team's.
- Aspect 16:9 unless stated. In the 840 × 600 area a 16:9 figure is 472 px tall at full width and 231 px at half width.
- Tick-label height: about 12 px at full width, 5.9 px at half width, 3.9 px at one-third width (see `08_FIGUREGUILD_ASSET_INDEX.csv`).
- "Caption accurate" refers to the repository caption file named in `01_…csv` (`caption_source`).

### Formal evidence integrity

**AV-F05 — Formal D(Y) decision-state transitions** · S1 supporting
- Question: does removing information or widening bounds ever create an unjustified exclusion?
- Notice first: every forbidden cell is 0.
- Caption accurate; a 3 × 3 matrix with large numerals that stays legible even at half width.
- Pair with table A04a and the proof document. Its key information is not shown elsewhere.

### D(Y) decision semantics and behaviour

**Q1_C15 — Why formal D(Y) abstains: three evidence situations** · S1, the strongest single D(Y) figure
- Question: what makes the engine abstain or decide?
- Notice first:
  - frozen 12/12 abstain (no qualified bounds);
  - full universe 42/42 indeterminate;
  - restricted universe 8 correct, 2 wrong, 4 ambiguous, 28 model mismatch.
- Caption accurate; three bars, readable at half width.
- Without a cell-count note it risks being read as rates.

**Q1_C14 — Restricted-universe decisions** · S1/S2
- Question: which query × bound cells become SPECIFIC?
- Notice first: correct SPECIFIC only for SID 213 (S3–S5, REF); SID 215 → Normal wrong at S5/REF.
- Grid labels are small (S1–S6, REF, H213 in cells); best at ≥ 60% width.
- Complements Q1_C15, which gives the counts while C14 gives where they fall. Do not show both at small size.

**AV-F04 / H1-F06 — Library completeness** · S1 (pick one)
- AV-F04 shows four library variants; H1-F06 adds sensor-group rows (8 rows, denser).
- Notice first: removing the true hypothesis produces wrong SPECIFIC decisions.
- This is the key limitation of D(Y). AV-F04 is cleaner; H1-F06 duplicates it with more detail.

**Q1_C12a–d, Q1_C13a/b — Status matrices and exclusion onsets** · S3
- Valid but dense: 10–24 rows, small cell labels, aspect up to 4:3 (C13a/b 3840 × 2880).
- Use only for a dedicated D(Y) panel at full width. Their information is summarised by Q1_C15 and V2-F03.

### Isolability and sensor observability

**V2-F03 — Pairwise isolability onset** · S1
- Question: how much tighter than REF must the bounds be to separate each pair, and is any pair intrinsically inseparable?
- Notice first: Normal vs SID 215 needs about 0.08 × REF even with all channels; pressure-only fails for every withdrawal pair.
- 15 labelled rows on a log axis; readable at ≥ 50% width, row labels about 6 px at half width.
- Must carry "template-level; hypothetical bounds", and must not be read as classification accuracy.
- Complements AV-F07, the binary view at REF. Do not show both.

**AV-F07 — Sensor-dependent pairwise isolability** · S2 (alternative to V2-F03)
- Three 6 × 6 binary matrices (all / pressure / flow); intuitive but binary.
- The labels "14/15 pairs separable" invite an accuracy reading; qualify as "formally separable at REF".

**V2-F04 — Structural incidence** · S2
- Explains why SID 215 is inseparable: no channel exceeds 2 ε_REF.
- 13 × 7 grid with clear category legend.
- Redundant with Q1_C01 in content but more formal. Choose one.

**Q1_C01 — Each outlet excites a different sensor group** · S2
- Physical intuition: flow meters vs pressure sensors, log scale.
- Most accessible observability figure; dense marker labels.

### Robustness: sensors and timing

**AV-F08 — Missing-sensor robustness** · S1 (3840 × 2480, aspect 1.55, a better fit to 7:5)
- Notice first: flow-only gives 4 wrong vs 2 baseline; without MFS3, mostly ambiguous.
- 10 rows of stacked bars with in-bar counts; readable at about 60% width.
- Conditional on hypothetical bounds; 24 decisions per configuration over 6 captures.

**V2-F02 — Synthetic sensor faults and jitter** · S2
- Must carry the SYNTHETIC label (it does).
- Notice first: no added wrong decisions; moderate faults raise the wrong share among SPECIFIC; large faults → all UNRESOLVED.
- Caption corrected in v2 to state the risk increase. Same visual grammar as AV-F08, so they work side by side.

**AV-F09 — Timing robustness** · S2
- Two panels: widening the clock bound changes nothing; delay beyond the bound → abstention (wrong decisions persist).
- Dense row labels; 16:9.

### Registered hypothesis and exploratory selective risk

**H1-F01 — Attainable coverage vs registered targets** · S1 for honesty about H1
- Notice first: the Center maximum of 0.258 is below the 0.60/0.80/0.90 targets → NOT_ESTIMABLE.
- Simple bars, readable at half width.

**H1-F02a / AV-F01 — Selective risk vs coverage** · S2 (pick one)
- Both show the same exploratory curves. AV-F01 adds the no-abstention reference and a wide grey "not attainable" region; H1-F02a is zoomed to the shared region and more readable.
- Must carry "EXPLORATORY, post hoc, inspected windows".

**H1-F02b — Paired differences with intervals** · S2
- Notice first: s_C − s_C−D intervals include 0. The honest D(x) statement.

**AV-F02 — Wrong SPECIFIC at equal coverage, split by attribution** · S1 for the label-defect story
- Notice first: the hatched (disputed-run) portion dominates every bar.
- Two panels, readable at about 60% width.

**V2-F01 — D(x) incremental value** · S1 for the D(x) negative result
- Panel (a) uses a symlog axis. The axis transition can confuse a quick reader; the caption explains it.

**Q1_I05 — R2 confusion by held-out topology** · S2
- Notice first: Center LEAK → Normal (7,307); Downstream Normal → LEAK (662). These are exactly the disputed-attribution runs.
- Small matrix numerals.

**Q1_I08 — Registered three-outcome shares (RQ3)** · S3, high misinterpretation risk
- "0 of 11,198 wrong" excludes the Center fold and includes Downstream runs with disputed labels. If shown, carry the denominator and the fold exclusion.

**AV-F11 — Negative control** · S3
- A single NORMAL template means 1 independent unit, so it is not a false-alarm rate.

### Cross-domain, gas and synthesis

**V2-F05 — HY2RES certified port** · S2
- Shows Level-A portability and the gap between candidate filtering and certified exclusion.
- Six labelled bars, readable. Must not be read as diagnostic validation (labels are electrical power states).

**AV-F14 — Gas qualification matrix** · S2 compact
- Symbol matrix, legible. The central negative statement for hydrogen.

**AV-F15 — Software portability** · X/S3
- Partly superseded by V2-F05: HY2RES now runs through the engine at Level A.

**V2-F06 / Q1_I09 / AV-F16 — Evidence summaries** · S2 (pick one)
- V2-F06 is the most current (H1–H10 × C1–C10). The others are v1 versions with partly superseded rows (AV-F16 "D(Y) refuses with incomplete library").

**Q1_I01 — Evidence architecture** · S3 schematic
- Methods or context, not a result. Contains "48 correct, 11 wrong" pooled counts; see the misinterpretation register.

**AV-F12 — Measured computational scaling** · S2 compact
- Six small panels; tick labels become tiny below about 60% width. A table (A14b) carries the same message more compactly.

**AV-F13 — Sensor count trade-off** · S3
- No prices; the y-axis counts out of 24. Overlaps AV-F08.

### Reference prediction (HY2RES, MHC)

**Q1_H10, Q1_H11 — HY2RES abstention follows out-of-support drift** · S2 if HY2RES is shown
- A good "abstains for a stated reason" example.

**Q1_I02 — Cross-study reference comparison** · S3
- Prediction context only.

**Q1_B\*, Q1_H01–H09** · S3
- Forecasting baselines; not H₂-PRISM diagnostic evidence.

## Figures that should NOT appear prominently

1. **Illustrative_demo, all 4** — invented values (`03_results/ILLUSTRATIVE_DEMO_NOT_RESULTS/`).
2. **Stage2_pipeline `03_results/figures/fig1–fig6`** — superseded pre-registration outputs, < 3200 px.
3. **R2_figsys_other**, all `preliminary/` and non-`b200fcdac` run keys — superseded run variants.
4. **R2_figsys_final fig2/fig4/fig5** — approved but dense multi-panel and small; replaced by H1-F01/F02a, Q1_I08 and Q1_I05.
5. **Center_atlas and its poster exports** — frozen formal state only (12/12 UNRESOLVED), older style; replaced by Q1_C*.
6. **Engineering_verification** (phase10–12 convergence and mass plots) — QC, not results.
7. **Q1_I08 without qualification** — Center excluded; disputed labels.
8. **AV-F07 captions read as accuracy** ("14/15").
9. **AV-F15** — superseded statement about portability.
10. **Any MHC/HY2RES prediction figure presented as diagnostic validation.**

## Modifications that could change scientific meaning

- Cropping V2-F02 or AV-F08 legends removes the hatched/solid distinction between wrong and correct, or ambiguous and unresolved.
- Removing the red stamp lines (EXPLORATORY, SYNTHETIC, CONDITIONAL HYPOTHETICAL BOUNDS) changes the evidence class.
- Re-colouring Q1_C14 or C15 so that SPECIFIC-wrong is no longer hatched loses the grayscale distinction.
- Recomposing panels of AV-F09 or V2-F01 separately is safe only if each panel keeps its own axis label and stamp.
- Changing the V2-F03 log axis to linear hides the λ* < 1 region.
