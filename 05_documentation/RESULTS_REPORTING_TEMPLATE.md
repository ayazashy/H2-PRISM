# Results Reporting Template (A5)

> **TEMPLATE, NOT RESULTS.** Every `⟨…⟩` placeholder is filled only from an authorized `PRIMARY_EXPERIMENT` run (`03_results/primary_protocol/PRIMARY/`). No value below exists yet. Wording follows `phase6_resolution/AHMED_RESOLUTION.md` C6, fixed before execution.

## 1. Run identity

`artifact_class` ⟨PRIMARY_EXPERIMENT⟩ · config ⟨sha256⟩ · git ⟨commit⟩ · code ⟨sha256⟩ · run_key ⟨…⟩ · authorization ⟨file, authorized_by, date, governance_clearance⟩.

## 2. Data actually used

⟨T0: runs, families, windows per class and topology⟩, with the restrictions from `DATASET_LIMITATIONS.md` L1–L11.

## 3. RQ1: incremental value of D(x) at matched coverage

- **Primary estimand:** s_C vs s_C−D, primary policy, rank-matched target 0.80.
  - **If estimable:** "Within the three evaluated simulated topologies, adding D changed selective risk by ⟨Δ⟩ (95% family-bootstrap interval ⟨lo, hi⟩, ⟨n_units⟩ families) at coverage ⟨c⟩."
  - **If NOT_ESTIMABLE:** "The 0.80 target was not attainable under the primary safeguards (⟨k⟩ of 3 folds); no comparison is reported at this target."
- **Wording rules:**
  - Interval includes 0: "no evidence of incremental value at this sample size" (not "equivalent").
  - Δ > 0: reported as a negative finding with the same prominence.
- **Secondary results (labelled):** targets 0.60 and 0.90, the warning-only variant, threshold transfer, C vs B and the other indicators, tie-order sensitivity, and the 9 sensitivity analyses.

## 4. RQ2: selective outcomes

⟨T_RQ2⟩ and ⟨T_ambiguity⟩. LEAK is restricted; the other classes are descriptive only. DELAY is not interpretable as the delay event (start-up confounding).

## 5. Limitations (mandatory paragraph)

- Three simulated topologies.
- Run fingerprint (interpret with the offset-invariant sensitivity).
- DELAY / start-up confounding.
- Thin classes.
- LEAK dominance.
- Unknown ancestry.
- Simulation only.

## 6. Prohibited statements

Industrial readiness, field validation, generalisation beyond the 3 topologies, physical identifiability, metric localisation, pure-hydrogen performance, a verified blend percentage, superiority of D beyond the reported effect sizes, or significance claims.
