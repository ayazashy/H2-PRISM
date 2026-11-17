# Problem Formulation and Motivation (A2)

- **Status:** PRE-EXPERIMENT DRAFT. Ahmed's approval NOT_RECORDED.
- No sentence claims demonstrated superiority, novelty or performance.
- External literature is deliberately not cited here: references need source verification (plan A2 step 19) and are added only once checked.

## Motivation

Monitoring a hydrogen-blend pipeline network produces pressure and flow time series in which different events can look alike. A leak, a compressor fault, a delayed compressor start and normal operation may produce overlapping signatures, especially in short windows and at sensors far from the event.

A classifier trained on such data always returns a single label. That label says nothing about **whether the evidence actually separates the candidate events**. We treat this as a research motivation, not as an established universal failure: in cases where events are empirically hard to tell apart, a forced single label may overstate what the data support.

Three notions are kept distinct:
- **Confidence** C(x) = max_k p_k(x): how strongly the classifier prefers its top class.
- **Predictive uncertainty**: spread of p(x), measured by margin M(x) and entropy H(x).
- **Empirical distinguishability** D(x) = q_(1)(x) − q_(2)(x): how one-sided the labelled reference windows near x are, with x's own family excluded. It is a property of the reference neighbourhood, not of the classifier, and **not** physical identifiability.

**Selective diagnosis** replaces the forced label with three outcomes:
- SPECIFIC (one class);
- AMBIGUITY_SET (a small set of plausible classes);
- UNRESOLVED (no reliable decision).

Support flags prevent SPECIFIC decisions resting on one run or on out-of-support evidence.

**Hypothesis to investigate, not a claim:** D(x) carries decision-relevant information that C, M and H do not.

## Formulation

The formal definitions are in `02_methodology/DIAGNOSTIC_PROBLEM_FORMULATION.md` and `DISTINGUISHABILITY_MATHEMATICAL_SPEC.md`:
- x is a 60 s window (128 features);
- y ∈ {NORMAL, LEAK, COMPRESSOR_FAULT, COMPRESSOR_DELAY};
- p(x) is the calibrated RF probability vector;
- q(x) and D(x) are reference-neighbourhood support;
- the decision is g(x) ∈ {SPECIFIC, AMBIGUITY_SET, UNRESOLVED}.

This leads directly to the two research questions:
- **RQ1:** at matched coverage, does an acceptance score that uses D (s_C) give lower selective risk than the same score without D (s_C−D)?
- **RQ2:** does the policy produce specific, ambiguous and unresolved outcomes in a reproducible, class-interpretable way?

**Scope:** simulated H₂-SimNet data (three network topologies). Results will be conditional on these topologies (`DATASET_LIMITATIONS.md`).
