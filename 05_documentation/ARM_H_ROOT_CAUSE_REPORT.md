# Arm H: root causes of the NORMAL↔LEAK errors and of D(x)'s missing increment

- **Date:** 2026-11-13.
- **Scope:** read-only diagnostic of development arm H_POSITION_MATCHED (run key `65f05249dd12`).
- **Evidence status:** EXPLORATORY_DIAGNOSTIC. These are development data that were all inspected earlier, so nothing here confirms a claim.

**What was done:**

- The H outputs, authorization record and RC1 are unchanged. The H outputs are verified against their hash list at the start of every script run.
- No classifier, calibrator or meta-model was fitted, and nothing was tuned.
- The only computed geometry is standardisation and k = 25 nearest neighbours, exactly as D(x) uses them. Each window's reference is the other development topology of its fold, which is the training data of the classifier that predicted it.

**Sources:**

- Scripts: `tools/experiments/diagnose_h_failures.py` and `tools/experiments/diagnose_h_signals.py`.
- Outputs: `03_results/diagnostics/arm_h_failures/`.
- Inputs: H's stored development predictions, manifest v0.3, position map v0.1, and the clean and noisy raw series of all 51 eligible runs.

**Units:**

- σ = per-sample added-noise standard deviation (noisy − clean of the same model's NORMAL run).
- Window-σ = σ/√60, the noise of a 60 s window mean.

## 1. Verification of the four carried-forward statements (`STATEMENT_VERIFICATION.csv`)

| Statement | Verdict | Evidence (clean and noisy) |
| --- | --- | --- |
| Eight weak or transient G4/G5 leak runs are 0.4–1.2 σ from their NORMAL reference | **VERIFIED** | Exactly 8 runs have a post-onset median \|clean difference to their own model's NORMAL\| below 2 σ on every position-matched channel (top channel 0.37–1.24 σ). They belong to **3 independence groups**. In noisy 60 s windows the same difference is a median of 4.7 window-σ on PS4, and 68% of windows exceed 3 window-σ, so averaging over 60 s makes the effect marginally visible *within* a model. |
| Cross-topology offsets of 0.13–0.60 MPa are 10–40× the weak-leak signatures | **REVISED** | The offsets are verified: NORMAL steady state on PS4 0.130–0.604 MPa, PS9 0.163–0.485 MPa. The ratio is **1.8–23×** for the six constant-segment weak leaks (onset signature 0.026–0.075 MPa), not 10–40×. The two transient G4 runs drop by 1.55–1.60 MPa at onset and then settle 0.0002–0.0005 MPa from their own NORMAL, which is 250–740× smaller than the offset. |
| Weak-leak trajectories converge to the model-specific NORMAL operating point after onset | **VERIFIED** | Clean \|difference to own NORMAL\| falls from a median of 0.043 MPa before onset to 0.0005 MPa after it, in **16 of 16** run × top-channel cases. Noisy: 0.021 → 0.0004. Example (up model, PS4): the weak G4 run sits at 6.475 MPa before onset, NORMAL at 6.432; after onset the weak G4 run reads 6.428 vs NORMAL 6.426 at 3,000 s, and 6.409 vs 6.408 at 5,000 s. |
| G5/G6 and G5_STRONG show visible signatures despite LEAK→NORMAL errors | **VERIFIED** for both | At the windows called NORMAL, the clean event visibility is 1,006 σ (G5G6 overlapped) and 555 σ (G5_STRONG: MFS1 +57 kg/s, PS4 −0.27 MPa). The third LEAK→NORMAL run, a transient G4 with 5 windows, is visible (9 σ) only early in its decaying transient, which is where its errors occur. |

**Pre-event difference: original maximum vs robust median.**

- The original statistic `pre_event_max_abs_z` is kept for reproducibility. It is the maximum over all pre-onset rows and channels.
- Every such maximum falls in the start-up phase: at t ≤ 395 s, and 94% before 500 s.
- The 6,782–6,848 σ values all occur at t = 25 s on PS7, where the supply-pressure step is applied and the runs differ by a sample.
- The additional, clearly labelled robust statistic `pre_event_median_abs_z_top_channel` (median over pre-onset rows) is 0–261 σ with a median of 87 σ. Before onset, no event run matches the NORMAL run's state.

## 2. Errors by independent scenario (`ERROR_INDEPENDENT_SUMMARY.csv`, `ERROR_BY_ANCESTOR.csv`)

Windows enter two folds' development sets. "Instances" counts window × fold pairs; the independent unit is the **independence group**.

| Error | Instances | Unique windows | Runs | **Independence groups** | Confident (≥ 0.9) instances / groups | k-NN majority = true class | k-NN majority = classifier label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NORMAL → LEAK | 3,930 | 1,981 | 3 | **1** (the only NORMAL scenario) | 3,151 / 1 | 0.006 | **0.991** |
| LEAK → NORMAL | 866 | 866 | 3 | **3** (G5G6 overlapped 467, G5_STRONG 394, transient G4 5) | 101 / 1 (G5G6) | **0.999** | 0.001 |
| DELAY → FAULT | 25 | 25 | 1 | 1 | 0 | 0.000 | 1.000 |
| FAULT → DELAY | 1 | 1 | 1 | 1 | 0 | 1.000 | 0.000 |

**Independent evidence behind the failures:**

- NORMAL→LEAK rests on **one** scenario.
- LEAK→NORMAL rests on three, and all three are scored with the down model or center model held out.
- **The 3,151 confident NORMAL→LEAK windows are therefore one independent failure, not 3,151.**

## 3. Error taxonomy (`ERROR_TAXONOMY.csv`; fixed rules, per run)

| Mechanism | Runs | Evidence | Not shown |
| --- | --- | --- | --- |
| **A. Physical overlap + insufficient independent NORMAL support + cross-model operating-point shift** | NORMAL runs of all three models (3,930 instances) | See below. | That the classifier *uses* the offset channels (its internals and per-class probabilities are not stored). |
| **B. Classifier failure on a visible event** | G5G6 overlapped and G5_STRONG (both down-model runs held out); transient G4 early windows (center model held out) | Visible signatures (≥ 9 σ at the error windows). The k-NN majority is the true class in 99.8–100% of these windows; the classifier says NORMAL. | *Why* the classifier fails. On pressure channels the down model's G5_STRONG leak state (PS4 6.22 MPa) lies about 0.14 MPa from the training (up) NORMAL operating point (6.36), which is *consistent with* reliance on absolute pressure. The leak flow is unmistakable on MFS1. Untestable without the model. |
| **C. Evidence agrees with the wrong class** | STARTDELAYC1 (25 windows, down model held out) | Both classifier and k-NN say FAULT. DELAY and FAULT act on the same compressor C1, and each class has 1 independence group. | Whether this is physical similarity or insufficient support. |
| Low-visibility event | none of the actual errors | The 8 low-visibility runs are *not* misclassified (they are predicted LEAK). They drive mechanism A instead. | — |

**Evidence for mechanism A, together:**

1. **Overlap.**
   - In each model, 2–3 LEAK-labelled runs sit at that model's NORMAL operating point after onset: 1,730 windows for each of center and down, 1,079 for up.
   - Each training topology has 665 NORMAL windows.
   - These runs differ from their own NORMAL by 0.4–1.2 σ per sample (about 5 window-σ).
2. **Shift.** The held-out NORMAL run differs from the training NORMAL run by **2,750–7,400 window-σ** on PS2, PS4 and PS9, all windows beyond 3 window-σ (`DISTINGUISHABILITY.csv`).
   - Within a model, the weak-leak vs NORMAL difference is about 5 window-σ.
   - Across models, the NORMAL vs NORMAL difference is about 1,500× larger, and it is the same size as the weak-leak vs other-model-NORMAL difference.
   - **Cross-topology, NORMAL and the low-visibility LEAK runs are equally far from each other's model: the labels are not separable by anything that transfers.**
3. **Neighbourhoods.**
   - The k = 25 training neighbours of held-out NORMAL windows are 72–83% LEAK, mostly the low-visibility runs plus G6.
   - Held-out NORMAL windows are nearer to a training LEAK window than to a training NORMAL window in 68–86% of cases.
   - Their distance to the training NORMAL run (2.73–2.93) is no larger than that run's own internal spacing (2.66–2.74).
4. **Two evidence sources fail together.**
   - Classifier and k-NN agree on LEAK for 99% of the failing windows.
   - The confidence median is 0.82–1.0 and 84–98% of windows have confidence ≥ 0.9, except one fold-topology at 0.006.
   - So no evidence-consistency rule can catch this failure: it is in the data, not in one model.

**Label question (unresolved).**

- Before onset, the weak-leak runs are at a *different* state from NORMAL (higher pressure). After onset they move *onto* NORMAL's state.
- **One explanation:** the anomalous models' pre-onset configuration differs from the normal models' configuration, and the "weak leak" restores the normal withdrawal. This is consistent with the diagram difference: restriction G3 is variable in the anomalous models and fixed open in the normal models.
- **The other:** the leaks are genuinely below sensor resolution.
- The release holds only the last-saved anomalous model state, so the per-run settings cannot be recovered. Only the dataset authors can decide.

## 4. Within- vs cross-topology distinguishability (noisy 60 s window means; steady period)

| Comparison | PS4 median \|Δ\| (window-σ) / share > 3 | PS9 | PS2 | MFS1 |
| --- | --- | --- | --- | --- |
| Low-visibility LEAK vs **own** model's NORMAL | 4.7 / 0.68 | 4.9 / 0.68 | 3.3 / 0.53 | 1.0 / 0.04 |
| NORMAL vs NORMAL, **different** models | 7,406 / 1.00 | 4,971 / 1.00 | 2,752 / 1.00 | 6.1 / 0.97 |
| Low-visibility LEAK vs **other** model's NORMAL | 7,396 / 1.00 | 4,978 / 1.00 | 2,747 / 1.00 | 6.0 / 0.98 |

## 5. Why D(x) improved standalone but adds nothing inside s_C (`DECISION_REPRODUCTION.csv`, `DX_DIAGNOSTIC.csv`)

**The registered metric saturates.**

- The matched selection at 0.6 is reproduced exactly from the stored scores: 18 of 18 fold × topology × method cases match the stored wrong-SPECIFIC counts and group risks.
- In 11 of 18 cases the **only** group with errors is NORMAL, and every selected NORMAL window is wrong (group risk ≥ 0.997). Group-balanced risk is then 1/11 = 0.0909 in all 11, however many NORMAL windows are selected.
- The other 7 cases add a second group with errors: G5_STRONG (fold 1, down model held out), G5G6 overlapped (fold 3, down) or transient G4 (fold 3, center; risk ≤ 0.005).
- To change that number, a score would have to remove *all* NORMAL windows from the selection.

**D(x) does change the selection.**

| Score | NORMAL windows selected | Wrong selected windows (window × fold instances) |
| --- | --- | --- |
| s_C | 3,073 | 3,920 |
| s_C−D | 3,609 | 4,456 (−12% with D) |
| confidence alone | 3,380 | **3,435** |

**Why standalone AUROC improved.** Errors concentrate in NORMAL windows: 57–100% of errors per held-out topology. There:

- the neighbourhood is mixed, so the median D is 0.44–0.68;
- confidence is about 1.0.

**Why it does not carry into s_C:**

- **Saturation:** 60–68% of all windows have D = 1 (no ranking information; ties fall to the hash key).
- **Unstable meta-model ranking:** the Spearman correlation of s_C with confidence ranges from −0.56 to 0.99 across held-out topologies.
- **Confidence alone selects fewer wrong windows than s_C.**

**Operational reading:**

- D(x) carries neighbourhood-disagreement information that partly flags the NORMAL failure.
- The meta-model does not exploit it reliably.
- The registered group-level contrast cannot register the effect while one all-wrong group is present.

## 6. Proposed remedies (untested; none is claimed to improve results)

| # | Remedy | Addresses | Owner | How it must be tested |
| --- | --- | --- | --- | --- |
| R1 | **Resolve the label/configuration question for the 8 low-visibility runs** with the authors: simulation parameters for G4_WEAK, G5_WEAK and transient G4, and whether the anomalous pre-onset configuration differs from the normal model. Until then, report a registered sensitivity analysis that excludes runs failing a prespecified detectability rule (clean post-onset < 2 σ on every channel, defined here before any rerun). | A | Yazan / authors | Rule fixed before use; sensitivity only, never replaces the primary analysis |
| R2 | **Matched counterfactual baselines:** each event run paired with a NORMAL run from the *same* model, configuration and seed baseline (event switched off) | A; label question | Yazan / authors (D6) | New simulations; verify pre-onset equality to within noise |
| R3 | **NORMAL support:** ≥ 3 independently parameterised NORMAL operating points per topology, spanning the cross-model offset range (at least 0.13–0.60 MPa on PS4) | A | D6 | Confirmation partition only |
| R4 | **Operating-point-invariant representation** (e.g. differences to a causal rolling baseline, or ratios between position-matched sensors), registered as a new development arm | A, B (absolute-pressure reliance) | Faisal (design), project lead (authorize) | Development arm, then independent confirmation; must not use future data |
| R5 | **Evidence-conflict rule E** (already implemented, default off in RC1): k-NN majority = true class in 99.9% of LEAK→NORMAL windows, so E would withhold SPECIFIC there. It would **not** help NORMAL→LEAK (sources agree in 99%). | B | Faisal | Prespecified; test only on independent data |
| R6 | **Report per-group and window-level risk beside the registered group-balanced risk**, and record when one all-wrong group saturates it | reporting | Faisal | No data needed; interpretation rule |
| R7 | **Instrumentation:** store per-class probabilities and meta-model coefficients in development outputs | the unresolved items below | project lead | Code change; no effect on decisions |

**Independent data needed to test them prospectively:**

- R1–R3 and the label question need the authors' parameters and new simulations from the D6 specification. Each class needs at least 3 independent scenarios per topology, and NORMAL needs at least 3 operating points per model.
- R4 and R5 additionally need a confirmation partition fixed before analysis.

## 7. What the available data cannot resolve

1. Whether the low-visibility "weak" leaks are intended physics or a configuration artifact. The per-run model settings are not in the release.
2. Why the classifier calls visible G5 leaks NORMAL. Its internals and per-class probabilities are not stored, and retraining is not permitted.
3. Whether COMPRESSOR_DELAY vs FAULT confusion is physical similarity or thin support (1 group each).
4. Whether NORMAL errors persist with independent NORMAL scenarios: the class has one independence group.
5. Any effect of D(x) at group level while one all-wrong group is selected.

**State of the record:** RC1, H's outputs and authorization, and all R2 artifacts are unchanged. The Yazan and Faisal approvals remain pending.
