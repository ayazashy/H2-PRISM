# Distinguishability v2: definitions, evidence and validation design

**Status:** research component, not registered.

- Not used by R2, arms A–H, RC1 or the primary runner.
- The original D(x) and E_h are unchanged and remain comparators.
- Evidence baseline: `06_audit_preparation/protocol2/v2/EVIDENCE_BASELINE.md`.

**Code:**

- `src/h2prism/distinguishability_v2.py` (the statistic);
- `src/h2prism/feature_representations.py` (causal representations);
- `tests/test_distinguishability_v2.py` (17 constructed counterexamples);
- `tests/test_feature_representations.py`.

**Diagnostics:** in `03_results/diagnostics/`, folders `distinguishability_v2/` and `feature_representation/`. All are EXPLORATORY_DIAGNOSTIC: no model was fitted and no held-out output was used for selection.

The question this framework must answer remains falsifiable: **does distinguishability add diagnostic value beyond predictive confidence and support safeguards?** Nothing below assumes that it does.

## 1. Four separate quantities

Notation:

- **Reference R:** development windows only, with class y, independence group g (scenario ancestor) and window start time t.
- **Query x.**
- **Groups linked to x:** its own independence group, which includes cross-topology replicas. They are always removed from R.
- **Scaling z(·):** per feature, median and 1.4826·MAD of R (SD fallback). Constant columns are dropped and counted, never divided by zero.

### 1.1 Evidence sufficiency (eligibility)

n_h(x) = number of independence groups of class h in R after removing the groups linked to x.

| State | Condition | Meaning |
| --- | --- | --- |
| SUPPORTED | n_h ≥ m (registered default m = 2) | evidence about h can be evaluated |
| INSUFFICIENT_EVIDENCE | 1 ≤ n_h < m | some evidence, but not independently corroborated |
| UNSUPPORTED | n_h = 0 | no evidence can exist |

Every quantity that needs h is **undefined (NaN with a named state)** unless h is SUPPORTED. Missing evidence is never encoded as distance, zero or "evidence against".

### 1.2 Hypothesis separability

1. **Group distance:**

   δ_G(x) = min over windows w ∈ G of ‖z(x) − z(w)‖ / √p / s

   Each scenario contributes one number however many (overlapping, autocorrelated) windows it has. Duplicated windows cannot add weight (test 11).
2. **Resolution s:** the median, over reference windows, of the distance to the nearest window of the **same** group that does not overlap in time (|Δt| ≥ 60 s).
   - s is the representation's within-scenario resolution: noise plus within-run variation.
   - All distances are in units of s.
   - If no within-group non-overlapping pair exists, s is undefined and every margin is DEGENERATE_SCALE.
3. **Corroborated class distance:**

   D_h(x) = the m-th smallest δ_G(x) over the groups G of class h

   x lies within D_h of at least m independent scenarios of h. A single scenario, however duplicated, cannot make D_h small (test 2).
4. **Separability margin:**

   M(x; h) = min over eligible h′ ≠ h of D_h′(x) − D_h(x)

   It is **signed, unbounded, uncalibrated, and not a probability**.

   | Value of M | State | Meaning |
   | --- | --- | --- |
   | M ≥ τ | SEPARATED | x is at least τ resolution units closer to m independent scenarios of h than to m independent scenarios of any eligible competitor |
   | \|M\| < τ | NOT_SEPARATED | h is not separated from a competitor at this resolution |
   | M ≤ −τ | CONFLICT | evidence separates another class from h |
   | — | UNTESTABLE | no eligible competitor exists |

   The registered default is τ = 1. Pairwise separability is S(x; a, b) = D_b − D_a.
5. **Assumptions:**
   - the representation is position-matched (no pooling of non-equivalent sensors, test 12);
   - reference labels are correct;
   - the reference covers x's operating configuration (otherwise the out-of-support rule applies);
   - Euclidean distance in robust-scaled features reflects physical similarity.

   Operating-point shifts are **not** removed by the statistic. They are detected (§1.4) or handled by the representation (§3).

### 1.3 Detectability (separate from distinguishability)

- **Definition:** Det(x) = D_NORMAL(x), compared with θ_det. θ_det is the 0.99 quantile of D_NORMAL over NORMAL reference windows, each scored against the **other** NORMAL groups (leave-one-group-out).
- **States:** DETECTED if D_NORMAL > θ_det, NOT_DETECTED otherwise.
- **Support needed:** at least m + 1 NORMAL groups, so the leave-one-group-out step keeps m. Otherwise UNDEFINED_INSUFFICIENT_NORMAL_SUPPORT, never NOT_DETECTED (test 15).

Detectability asks "does x differ from credible normal operation?". Distinguishability asks "which hypothesis does x support over its competitors?". The four combinations are all representable:

- **Detectable but ambiguous:** D_NORMAL large, but \|M\| < τ among the event classes.
- **Likely but unsupported:** the classifier's class is INSUFFICIENT_EVIDENCE.
- **Confident but conflicting:** M(x; ŷ) ≤ −τ.
- **NORMAL and weak LEAK indistinguishable:** NOT_DETECTED and NOT_SEPARATED (test 6).

### 1.4 Out of support

x is OUT_OF_SUPPORT if its nearest group distance (any class, linked groups removed) exceeds θ_oos. θ_oos is the 0.99 quantile of the same statistic for reference windows scored against the other groups (leave-one-group-out).

### 1.5 Conflict-aware decision (`decide`)

The classifier label ŷ and its confidence are inputs; neither ŷ nor the evidence is assumed correct. Rules, in order:

| Condition | Outcome |
| --- | --- |
| invalid features, degenerate scale, or out of support | UNRESOLVED |
| ŷ not SUPPORTED | UNRESOLVED (insufficient evidence to evaluate the diagnosis) |
| no eligible competitor (UNTESTABLE) | UNRESOLVED (configurable to AMBIGUITY_SET {ŷ}; the fail-closed default) |
| event predicted, detectability NOT_DETECTED | AMBIGUITY_SET {ŷ, NORMAL} |
| NORMAL predicted, detectability DETECTED | AMBIGUITY_SET {NORMAL, nearest eligible event} |
| M(x; ŷ) ≥ τ | SPECIFIC-eligible (rank by the method's score for matched coverage) |
| \|M\| < τ | AMBIGUITY_SET {ŷ} ∪ {eligible h: D_h − D_ŷ < τ} |
| M(x; ŷ) ≤ −τ | AMBIGUITY_SET {ŷ, evidence-best h}; **never** SPECIFIC for the evidence class (test 10) |

## 2. Comparison with D(x) and E_h

| Property | D(x) (protocol 1.1) | E_h (arm F) | v2 |
| --- | --- | --- | --- |
| Unit of evidence | window (k = 25 nearest) | window votes, re-weighted by group | **group** (one distance per independent scenario) |
| Duplicated or overlapping windows | add votes (D = 1 from one scenario, test 2) | can fill the neighbourhood: 54.1% of F's windows had a 25-NN from a single group | cannot add weight (test 11) |
| Missing evidence | not represented | UNSUPPORTED / INSUFFICIENT flags | per-class SUPPORTED / INSUFFICIENT / UNSUPPORTED; margin states |
| Distance scale | reference-standardised; meaning implicit | none (vote shares) | within-scenario resolution units |
| Sign / meaning | unsigned agreement, class-agnostic | signed, in [−1, 1], for a stated h | signed, unbounded, for a stated h against eligible competitors |
| Detectability | none | none | separate test against NORMAL with leave-one-group-out calibration |
| Out of support | mean k-NN distance vs quantile | same | nearest independent group vs leave-one-group-out quantile |

**Why E_h was undefined for 79.6% of arm F's windows.** Reproduced exactly; the stored scores match, NaN pattern included (`distinguishability_v2/EH_REPRODUCTION.json`):

| Share of windows | Cause | What it is |
| --- | --- | --- |
| 54.1% | INSUFFICIENT_INDEPENDENT_EVIDENCE: the 25 nearest windows came from 1 group (median n_units = 1) | a **construction artifact**: window neighbourhoods are filled by one run's overlapping windows |
| 9.7% | HYPOTHESIS_UNSUPPORTED: in **100%** of these cases the only group of class h was the query's own group, removed as a cross-topology replica | **data shortage** (FAULT 4,061, NORMAL 1,330, DELAY 62 instances) |
| 15.8% | OUT_OF_SUPPORT | arm F used the release attribution and name-matched channels |

v2 removes the first cause by construction. **It does not remove the second.** v2 needs at least 2 independent groups per compared class, and the current data do not have them:

- On H's development data, v2's margin is UNTESTABLE for 83.8% of window-fold instances and HYPOTHESIS_NOT_SUPPORTED for 16.2%. It is **undefined for 100%** (`distinguishability_v2/V2_ESTIMABILITY.json`).
- Detectability is undefined for 100%.
- Only LEAK ever has ≥ 2 groups in a reference (up to 10). NORMAL, COMPRESSOR_FAULT and COMPRESSOR_DELAY have ≤ 1.

This conclusion is preserved: m is not relaxed to manufacture outputs.

**Minimum support for v2 to be defined** (each scenario simulated in all three topologies forms one group):

| Quantity | Requirement |
| --- | --- |
| Separability between two classes | ≥ 3 independence groups per class in the development data (2 remain after removing the query's own group) |
| Detectability | ≥ 4 NORMAL groups (3 remain) |

## 3. Feature representations: physics assessment (no training; `feature_representation/`)

**Noise is white.**

- Noisy − clean residuals have \|ρ\| ≤ 0.026 at lags 1–59.
- The variance inflation of a 60 s mean is 0.89–1.17, so the window σ = σ/√60 assumption holds to within about 8% in SD.
- The earlier "4.7 window-σ" separation between weak leaks and their own NORMAL is therefore real **with respect to the simulated noise**.
- But it is a deterministic simulation difference of about 0.0005 MPa: the per-sample noise is 0.0005 MPa on pressure and 0.25 kg/s on flow, about 0.01% of pressure range. That is far below the README's "1–2% of range".
- No real sensor drift or model mismatch is represented. **The separation must not be read as practical sensor-level detectability.**

**Results** (each in the representation's own noise SD; medians over position-matched channels; PS4 shown where it differs):

| Family (causal; W = 60 s, baseline 1,800 s) | Cross-model NORMAL offset | False-alarm share on steady NORMAL | Weak-leak state difference (late) | Weak-leak onset change | Strong-leak state difference (late) |
| --- | --- | --- | --- | --- | --- |
| ABS absolute mean | 1,984 (PS4 9,135) | n/a | 1.4 (PS4 3.8) | 274 (PS4 733) | 2,348 |
| GRAD pipe pressure drop (5 diagram pairs) | 2,029 | n/a | 0.48 | 49 | 65 |
| CBD causal baseline deviation | 2.8 (PS4 12) | **0.38 (PS4 1.00)** | 0.18 | 166 | **1.0** |
| CRC robust change (noisy only; robust units) | 0.008 | 0.06 | 0.12 | 5.8 (PS4 7.4) | 0.13 |
| SLOPE window slope | 0.09 | 0.12 (PS4 0.38) | 0.005 | 34 | 0.03 |

**Physical reading:**

1. **Absolute and gradient features carry the cross-model operating-point offsets**, which are 1,000–9,000 noise SD. The weak-leak *state* differences are only a few noise SD. The pressure drop along a pipe scales with flow², and flow distributions differ between configurations, so gradients do not remove the offset.
2. **Change features (CBD/CRC/SLOPE) remove the offset and reveal weak-leak *onsets* strongly, but not *states*.**
   - The baseline absorbs any persistent condition, so late-event weak *and* strong leaks become invisible: the strong-leak state difference for CBD is 1.0 noise SD.
   - The supply-pressure ramp (−1e-5 MPa/s) makes plain baseline deviation fire on steady NORMAL: 38% of windows overall, 100% on PS4. A robust-scaled version reduces this to 6%.
   - A weak leak's change stays visible for about 470 s (CRC, PS4) to 1,175 s (CBD median) after onset.
3. **The onset-change *pattern* transfers across models.** For 11 of 13 leak stems simulated in all three models, the cosine similarity is ≥ 0.95, including G4_WEAK and G5_WEAK. The exceptions are the two transient stems: transient G4 reverses sign across models (−0.52), consistent with the earlier finding that its simulated effect differs by orders of magnitude between models.
4. **Unidentifiable from the sensors:** windows of a weak leak more than about 1,200 s after onset. Their state equals NORMAL's within a model and differs by less than the cross-model offset across models. No causal representation of the available signals can recover them. They should be reported as such, not "fixed".

No representation is selected here. Any future arm must pre-register its family before seeing results, and keep the absolute features available.

## 4. Falsifiable remediation hypotheses

| | Hypothesis | Intervention and comparison | Primary endpoint | Accept if | Fail if |
| --- | --- | --- | --- | --- | --- |
| **H-R1** NORMAL support | More independent NORMAL operating scenarios reduce false LEAK diagnoses and improve scenario-level transfer | ≥ 4 NORMAL groups for development and ≥ 3 for confirmation, each simulated in all three models. Factorial over supply pressure set-point (3 levels spanning ±0.3 MPa around 6.4 MPa), ramp rate (0, −1e-5, −2e-5 MPa/s) and withdrawal load (restriction areas ±25%). Noise seeds are **not** groups. Same classifier and representation as H, with (a) current NORMAL vs (b) augmented NORMAL. | NORMAL recall per independence group and scenario-balanced selective risk, on the untouched confirmation partition | NORMAL group-level recall ≥ 0.5 in every held-out topology, and scenario-balanced risk not worse than (a) | NORMAL recall stays < 0.2 for most held-out NORMAL groups. Then overlap with weak leaks, not support, is the limit. |
| **H-R2** Operating-point robustness | Causal change features plus absolute features separate weak-leak onsets from NORMAL across baselines better than absolute features alone, without losing strong-leak identification | Pre-registered families ABS + CRC (+ SLOPE); comparator ABS only; same windows and splits. Within-topology detectability and cross-topology transfer are reported separately. Weak-leak windows > 1,200 s after onset are declared **unidentifiable in advance** and reported, not scored as failures of either arm. | Scenario-balanced risk on identifiable windows; weak-leak onset recall (within 600 s); NORMAL false-alarm rate | Onset recall improves in the held-out topology with NORMAL false alarms ≤ 0.10 and no loss on strong leaks | No improvement across topologies, or false alarms > 0.10 (the operating ramp dominates) |
| **H-R3** Evidence-guided decisions | Support-controlled separability gating reduces wrong SPECIFIC diagnoses relative to confidence-only abstention at matched coverage | Matrix in §5; primary contrast E vs A | Scenario-balanced selective risk at the development-fixed coverage | E's risk is lower than A's, with the group-bootstrap interval excluding 0 | Interval includes 0, or E is NOT_ESTIMABLE. Report as null or not estimable. |

H-R1 is a precondition for H-R3: without at least 3 NORMAL groups, NORMAL is never eligible, so separability cannot test a NORMAL→LEAK diagnosis.

## 5. Registered development-experiment matrix (template; not registered, not authorized)

Config template: `06_audit_preparation/protocol2/v2/V2_EXPERIMENT_TEMPLATE.yaml`. Matrix: `V2_EXPERIMENT_MATRIX.csv`.

| Arm | Ranking score | SPECIFIC-eligible if | Role |
| --- | --- | --- | --- |
| A | confidence | current safeguards (support flags) | baseline |
| B | s_C−D | current safeguards | historical comparator |
| C | s_C (with D(x)) | current safeguards | historical comparator |
| D | confidence | A and ŷ SUPPORTED (≥ m groups) and not out of support | support-only control |
| F | confidence | D and not CONFLICT (M ≥ −τ) | conflict factor |
| E | confidence | D and SEPARATED (M ≥ τ) and no detectability contradiction | v2 |

**Design rules:**

- D ⊂ F ⊂ E are nested, so E − D isolates separability beyond support, and F − D isolates the conflict rule.
- All arms use the same classifier, windows, splits and independence groups.
- Matched coverage uses the exact-count rule, with a target fixed from development attainability. Where eligible windows are fewer than the target requires, the arm is NOT_ESTIMABLE (never forced).
- **One confirmatory contrast: E vs A**, on scenario-balanced selective risk with independence-group bootstrap. Everything else is secondary and exploratory: B/C, D vs A, F vs D, coverage, ambiguity inclusion, per-class rates.
- This matrix does not replace RC1's registered contrast (s_C vs s_C−D). Adopting it requires a new protocol version and Faisal's acceptance.

**On current data:**

- E and F are NOT_ESTIMABLE (v2 undefined for 100% of windows).
- D can only issue SPECIFIC for LEAK predictions. It would therefore *not* stop NORMAL→LEAK errors: LEAK is supported, and NORMAL is not eligible to contradict it.
- **Running this matrix on the current data would not be informative.**

## 6. Independent simulation specification (extends `INDEPENDENT_CONFIRMATION_DATA_SPEC.md`)

**Per model (center, down, up), separate development and confirmation partitions, every scenario a new independence group:**

| Class | Development groups | Confirmation groups | Variation |
| --- | --- | --- | --- |
| NORMAL | ≥ 4 | ≥ 3 | supply set-point, ramp rate, withdrawal load (H-R1 factorial) |
| LEAK | ≥ 3 positions × 3 severities | ≥ 1 per position | positions G3–G6; area weak/medium/strong set to a prespecified clean-signal detectability (e.g. 2, 10, 100 noise σ); onset times ≥ 3 distinct; durations: persistent and transient |
| COMPRESSOR_FAULT | ≥ 3 | ≥ 2 | severities and onset times |
| COMPRESSOR_DELAY | ≥ 3 | ≥ 2 | delay lengths |

**Every run records:**

- model file hash, solver and step;
- every changed block parameter;
- noise seed and σ per channel;
- the logged block identities (SIDs);
- an ancestry identifier (independence group);
- a matched counterfactual run with the event switched off (same model, same parameters, same seed).

**Supported by existing code:**

- NORMAL generation (`Normal_HNetwork_gest_*.slx`, `models_launcher.m`, `save_model_data_*.m`), by varying `PS Step`, `PS Ramp` and restriction areas;
- G3 leaks (variable restriction 213 driven by `PS Step1` in `Anomalous_HNetwork_gest_*.slx`);
- position mapping (`CANDIDATE_SENSOR_POSITION_MAP_V01.csv`);
- export (`save_model_script.m`).

**Needs new work:**

- making restrictions 222, 312 and 215 (G4–G6) variable, by copying the G3 mechanism;
- the compressor fault and delay mechanisms (not recoverable from the saved model state);
- block-identity export;
- a noise script with recorded seeds;
- provenance capture;
- confirmation of the weak-leak definitions with the authors (root-cause report §3).

No data are generated by this phase.

## 7. Quality control (this phase)

| Check | Result |
| --- | --- |
| Original D(x), E_h, R2, arms A–H reproducible and unchanged | hashes verified; E_h reproduced exactly from F's inputs |
| Clear mathematical meaning of the statistic | §1; M in within-scenario resolution units, explicitly not a probability |
| Detectability ≠ distinguishability | separate definitions, states and tests (5, 6, 15) |
| Independent ancestry respected | group-level distances; own group always removed; sufficiency counted in groups (tests 2, 8b, 16) |
| No pooling of non-equivalent sensors | position map required (test 12); gradients only between diagram-matched sensors at a pipe's ends |
| Temporal correlation | resolution uses only non-overlapping windows (test 11); noise verified white |
| No future data in baselines | all representations are causal; undefined until a full past baseline exists (feature tests) |
| No labels in features | representations take only the run's own signal |
| No score called a probability | M, D_h and Det are distances or margins |
| Undefined cases explicit | named states; NaN never replaced by 0 (tests 8, 14, 15) |
| Fair comparisons | nested matrix; same classifier, windows and splits; matched exact-count coverage |
| No claim beyond the evidence | v2 undefined on current data; no performance claim made |

## 8. Readiness and what remains unverified

**Ready:** the definitions, the tested research module, causal representations, the physics assessment, the matrix template and the data specification.

**Unverified (requires new independent data):**

- whether v2 separability reduces wrong SPECIFIC decisions (H-R3);
- whether NORMAL augmentation removes NORMAL→LEAK errors (H-R1);
- whether change features transfer (H-R2) beyond the onset-pattern similarity seen here;
- whether τ = 1 and m = 2 are adequate (fixed in advance, never tuned on current outcomes);
- whether the weak-leak definitions are intended physics.

**Not achievable with the current data:** any evaluation of v2's separability or detectability (both undefined for every window).

## 9. Authorization request (only one is needed, and it is not a real-data training run)

No further real-data execution on the current dataset is scientifically useful: v2 is undefined there, and the matrix's v2 arms are NOT_ESTIMABLE. The single scoped request that unblocks the next step is:

> **SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION**
>
> - **Owners:** Yazan (dataset owner) to execute or commission; project lead to authorize.
> - **Scope:** using only the released `Normal_HNetwork_gest_{center,down,up}.slx` and `models_launcher.m`, generate the H-R1 NORMAL factorial: ≥ 4 development and ≥ 3 confirmation operating points per model.
> - **Recording:** the §6 provenance per run.
> - **Partition:** the confirmation partition is hashed at creation and not opened.
> - **Excludes:** any training, any evaluation, any event scenario, and any change to existing data, R2, arms or RC1.

**Update (handoff review, 2026-11-13): the package v1 authorization below is VOID; package v2 is REQUESTED, not authorized.**

- The pre-execution review changed the generator, the noise tool and the validator:
  - R2025a requirement;
  - loading each model copy by explicit path;
  - preflight mode and failure records;
  - resampling to the release grid;
  - physical validity checks P1–P6;
  - fail-closed authorization.
- That voided the v1 hashes before any execution.
- The current state, commands, checks and failure procedure are in `06_audit_preparation/simulation/v2_normal_support/EXECUTION_CHECKLIST.md`.

**Status (2026-11-13, package v1, now void): AUTHORIZED by the project lead. Not yet executed.**

- MATLAB/Simulink is not available in this environment, so nothing has been generated.
- The package is in `06_audit_preparation/simulation/v2_normal_support/`:
  - fixed `DESIGN.csv`: 9 operating points × 3 models, 6 development and 3 confirmation;
  - the generator `generate_v2_normal_support.m`;
  - `tools/simulation/add_measurement_noise.py`;
  - `tools/simulation/validate_v2_normal_outputs.py`, which seals the confirmation partition by hash without reading it;
  - the authorization record bound to all four files' hashes.
- The package was validated by an end-to-end dry run on fabricated outputs (`tests/test_v2_simulation_package.py`).
- Execution acceptance by Yazan (or his designee) is not recorded.
