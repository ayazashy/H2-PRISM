# Protocol 2.0 development-stage ablation: results and scientific acceptance

**Scope.** Eight registered development-only arms (`06_audit_preparation/protocol2/ABLATION_MATRIX.md`), each authorized by the project lead on 2026-11-12 (`arm_authorizations/`).

- Each arm ran once from its pinned config.
- Each arm was evaluated only on inner topology-held-out predictions; no outer-test topology was scored.
- **Every number here is EXPLORATORY_DEVELOPMENT.** Each window was an R2 outer-test window, so nothing here confirms any claim (`02_methodology/INDEPENDENT_CONFIRMATION_DATA_SPEC.md`).
- Sources: `03_results/ablation/ARM_SUMMARY.csv` and `ABLATION_ACCEPTANCE.csv` (criteria applied literally; registered before any run).
- Window-level outputs are hash-listed in `03_results/ablation_runs/logs/`.

## 1. Results (means over the three outer folds' development data; same 27,993 windows in every arm)

| Arm | Accuracy | Balanced accuracy | Group-balanced accuracy | ECE | Min confidence AUROC | Errors with confidence ≥ 0.9 | Flag-free | Development-fixed targets | s_C group-balanced risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A protocol 1.1 | 0.478 | 0.416 | 0.468 | 0.465 | 0.073 | 0.696 | 0.213 | fold 1: 0.5 | 0.000 (1 topology) |
| B topology (v0.3) | **0.907** | 0.647 | **0.880** | 0.086 | **0.514** | **0.000** | 0.136 | none | not estimable |
| C common sensors | 0.524 | 0.461 | 0.488 | 0.411 | 0.005 | 0.799 | 0.267 | fold 1: 0.6 | 0.045 (2 topologies) |
| D group support | 0.478 | 0.416 | 0.468 | 0.465 | 0.073 | 0.696 | 0.213 | fold 1: 0.5 | 0.000 (1 topology) |
| E evidence conflict | 0.478 | 0.416 | 0.468 | 0.465 | 0.073 | 0.696 | 0.213 | fold 1: 0.5 | 0.000 (1 topology) |
| F evidence margin E_h | 0.478 | 0.416 | 0.468 | 0.465 | 0.073 | 0.696 | 0.213 | none (meta-model undefined in 2 folds) | not estimable |
| G1 = B + C | **0.913** | **0.722** | **0.902** | **0.046** | **0.615** | 0.612 | 0.244 | fold 2: 0.6 | 0.091 (2 topologies) |
| G2 = B + C + D + E + F | 0.913 | 0.722 | 0.902 | 0.046 | 0.615 | 0.612 | 0.244 | fold 2: 0.5 | 0.091 (2 topologies) |

**Reading the table:**

- D, E and F do not change the classifier, so their classifier rows equal A's (and G2's equal G1's).
- At G1's and G2's only development-fixed operating point, s_C, s_C−D and confidence have the **same** group-balanced risk: 0.091 (G2: 0.091 / 0.091 / 0.095).

## 2. Scientific acceptance per component (the ten questions)

| Question | B topology | C common sensors | D group support | E conflict policy | F E_h |
| --- | --- | --- | --- | --- | --- |
| 1 Implemented correctly | yes (manifest checks; preflight 26/26) | yes (104 inputs) | yes (unit tests; D unchanged) | yes (tests) | yes (10 counterexamples) |
| 2 Targeted mechanism removed | **yes**: high-confidence errors 0.70 → 0.00; confidence no longer anti-informative | no on its own (the swap dominates); with B, ECE 0.086 → 0.046 and balanced accuracy 0.647 → 0.722 | yes by construction (replicas counted once) | not observable: no wrong SPECIFIC decision at the only estimable point | no: undefined for 80% of windows, AUROC 0.49 ≈ D's 0.49 |
| 3 Prespecified metric improved | yes (criterion PASS) | criterion PASS, but confidence AUROC fell to 0.005 | criterion "PASS" is uninformative (0 vs 0 on 1 topology) | **FAIL** (floor: 0 vs 0) | **FAIL** |
| 4 New weaknesses | exposes OUT_OF_SUPPORT (0.17 → 0.67) where development pairs the `down` model with another | none observed | coverage cost (R2 impact: Center 0.258 → 0.184) | none observed | abstains almost everywhere; meta-model undefined in 2 folds |
| 5 Coverage change | targets lost in every fold (out of support) | targets: fold 1 at 0.6 | as A | as A | none |
| 6 Fair comparison | classifier metrics: same windows; development sets re-composed (fold-level values not paired) | yes | yes | yes | yes |
| 7 Exploratory or confirmatory | exploratory | exploratory | exploratory | exploratory | exploratory |
| 8 Holds at independence-group level | yes: group-balanced accuracy 0.47 → 0.88 | small (+0.02) | no classifier change | no data | no |
| 9 D(x) value separable from safeguards and meta-model | — | — | — | — | **No incremental value of D(x) or E_h.** At matched development coverage, s_C = s_C−D = confidence |
| 10 Missing evidence | dataset-owner confirmation (R-18), independent data | sensor-equivalence decision (D2) | independent thin-class scenarios | estimable operating points with errors | independent scenarios: E_h needs ≥ 2 independent groups per neighbourhood, which this dataset rarely has |

## 3. What the program shows

1. **The dominant failure is the data, and correcting it is the largest improvement available.** The topology attribution alone raises development group-balanced accuracy from 0.47 to 0.88, and removes confidently wrong predictions.
2. **The `down` model's data are out of support relative to the other two models, even on the 13 shared sensors.** Only the consistently configured pair (Center + Upstream development, fold 2) yields usable coverage (73% flag-free). Whether this is real physics (a different withdrawal point) or different sensor placement is Yazan's decision D2. It decides whether cross-configuration transfer is a meaningful task at all.
3. **No component of the decision layer adds measurable value on this dataset**: the conflict policy, group support, E_h and D(x) in s_C. This is a negative result, reported as such. It is also not a refutation: the dataset has too few independent scenarios (13 groups; 1 per thin class) for these mechanisms to act.
4. **E_h behaves as designed** (counterexample tests) and refuses to produce evidence that the data cannot support. That makes it unusable here and is the correct behaviour. It should be re-evaluated only on data meeting the independent-confirmation specification.

## 4. Objective criteria for selecting the final candidate (applied to development evidence only)

A component enters protocol 2.0 only if all of the following hold:

- (a) it is implemented and tested;
- (b) its registered development criterion passes **informatively**, i.e. not on a 0-vs-0 floor and not on a single topology;
- (c) it creates no unreported loss of estimability;
- (d) the responsible owner accepts it.

| Component | Recommendation to owners (not a decision) |
| --- | --- |
| B topology | include, if Yazan chooses option B |
| C common sensors | include **only if** Yazan confirms sensor equivalence (D2); otherwise redefine the shared set |
| D group support | include for validity (honest support counting); its coverage cost is accepted, not optimised |
| E conflict policy | keep as an owner design choice; no development evidence either way |
| F E_h | **do not include** now; keep the implementation and re-test on independent data |
| D(x) inside s_C | no demonstrated value; the registered contrast s_C vs s_C−D remains the RQ1 test for the confirmatory run |
