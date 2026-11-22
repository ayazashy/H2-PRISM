# Advanced validation — Discussion

**Overarching question.** Does H₂-PRISM improve justified diagnostic decision-making beyond established approaches, and under what conditions?

## 1. What the evidence now supports

**H1.** It is still not estimable as registered.

- The new accounting shows that every policy's error structure is dominated by the attribution defect.
- None of the policies makes a single error on runs with consistent attribution, except the one NORMAL template.
- The evidence guard's apparent advantage is therefore real *on these data*: it withholds 650–655 confident NORMAL → LEAK errors and the confident errors of the misattributed Center runs.
- It is not separable from the defect it reacts to.
- There is no evidence for or against H1 on independently labelled diagnostic difficulty.

**Formal D(Y).** The engine is mathematically sound on these inputs:

- monotone in information and uncertainty;
- every certificate verifiable.

The new experiments convert three earlier qualitative statements into measured conditional behaviour:

1. An incomplete library is the decisive failure mode. Removing the truth produces wrong SPECIFIC decisions; the full declared universe never decides.
2. Missing evidence does not create new exclusions. Decisions can still become wrong when the lost channel was the one excluding a rival (flow-only: wrong SPECIFIC decisions double).
3. Timing mismatch beyond the declared alignment produces abstention (MODEL_MISMATCH), not false certainty. The exception is time-invariant rivals.

**Identifiability is sensor-specific and partly impossible.**

- Normal operation and the SID 215 withdrawal are formally inseparable at the REF bounds even with all 13 channels.
- Two flow meters preserve every separable pair.

This is the most engineering-relevant new result. It is conditional on templates and hypothetical bounds.

## 2. Misleading-looking results to avoid

| Apparent result | Why it misleads |
|---|---|
| "0 wrong SPECIFIC for s_C at coverage 0.10" | The errors at stake are attribution artefacts from 1–3 templates. |
| "s_C 0.146 vs conventional 0.422 at coverage 0.25" | Same reason. |
| "Removing MFS1 eliminates wrong decisions" | It replaces them with ambiguity sets that exclude the truth. |
| "Flow-only keeps all correct decisions with 3 sensors" | It also doubles the wrong ones. |
| "MRR = 1.0" | One location, two near-duplicate captures. |
| "16 gas tests pass" | They test property routing and refusal, not diagnosis in hydrogen. |
| "Runtime ≈ linear" | One CPU, a narrow range, an implementation-specific exact-arithmetic cost. |

## 3. Which further analyses are not worth conducting now

- **New RF/SVM/XGBoost baselines on R2:** they would be fitted after inspection and would not change estimability.
- **An "Evidence Sufficiency Index":** the objective axes (channel count, bound scenario, library completeness) already carry the information. A composite score would be built after seeing the outcome.
- **An unrestricted UNKNOWN hypothesis:** it is identical to the full universe by construction.
- **Random-percentage dropout beyond the exhaustive minimum-set search:** it adds no information.
- **Cost optimisation without prices.**
- **Literature head-to-head numbers:** every comparability gate fails.

## 4. What would materially strengthen the case

1. The D1 decision, followed by the corrected exploratory replication.
2. New, independent scenario templates (H2Net v1), with ≥ 2 independent templates per class and per outlet.
3. Qualified observation bounds from instrument specifications.
4. Adapters for the three unmodelled declared hypotheses.
5. A structural isolability analysis to complement the template-level one.
6. Persisting exclusion certificates and model-bound values in exported decision records.
