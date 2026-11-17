# HY2RES targeted operating-state distinguishability

**Conclusion.** The record supports a descriptive distinction between two electrical-power states, driven chiefly by whether electrolyzer hydrogen flow is zero. When production is positive, substantial overlap remains. The development-only candidate-set rule yields some specific decisions for the dominant state and none for the compressor-powered state. Formal diagnostic hypotheses remain **INDETERMINATE**. Fault classification and leak localization are **NOT ESTABLISHED**.

## Verified state definitions and alignment

I used the checksum-matched HY2RES release and the existing Study C split and segment registry. The existing zero-watt rule yields two observed states. **Electrolyzer only** means positive electrolyzer power with zero compressor and fuel-cell power. **Electrolyzer + compressor** means positive power on both with zero fuel-cell power. Recorded electrolyzer power ranges from 9 to 1,992 W, compressor power from 0 to 780 W, and fuel-cell power is always zero. Positive electrolyzer draw can coexist with zero measured production. The labels describe electrical draw and do not certify a mechanical state or production. The record contains no supported all-off, compressor-only or fuel-cell-powered contrast under this rule. [Publisher channel definitions](https://zenodo.org/records/15166733)

At the Study C forecast origin, the label uses three same-row power readings. The distinguishing measurements use only buffer pressure, tank pressure and electrolyzer H₂ flow from that same origin, exactly 5 s before the indexed Study C target within the same segment. No target-time measurements or power variables enter the rule as predictors. This is contemporaneous state recognition. The preceding-interval flow measurement and the power label are physically coupled. Unknown power or absence of an admissible origin is counted separately. This task uses a single origin row and therefore has different eligibility from the three-lag frozen prediction comparison.

| Partition | Electrolyzer only, rows / segments | Electrolyzer + compressor, rows / segments | Segments containing both |
|---|---:|---:|---:|
| Development | 205,281 / 1,900 | 3,316 / 47 | 33 |
| Previously inspected test | 43,167 / 405 | 817 / 12 | 8 |

The retained development and test groups share no segment IDs. Segment counts are distinct recording segments, with statistical independence unverified. The same pilot contributes all observations. Validation contained no compressor-powered comparison rows, and the archived test had already been inspected. No unused evaluation partition was established.

## Empirical pressure–flow distinction

Statistics below use previously inspected test observations. Pairwise rank probability is the chance that a randomly drawn compressor-powered row exceeds an electrolyzer-only row on the channel, with half credit for ties. It measures descriptive row-level separation and supplies no independent accuracy estimate.

| Origin measurement | Electrolyzer only median [IQR] | Electrolyzer + compressor median [IQR] | Rank probability |
|---|---:|---:|---:|
| Buffer pressure, bar | 30.8 [30.3–31.2] | 31.3 [30.1–32.6] | 0.583 |
| Tank pressure, bar | 107.8 [106.5–108.9] | 108.4 [106.8–109.4] | 0.528 |
| Electrolyzer H₂ flow, NL/h | 0 [0–0] | 322.972 [321.456–329.079] | 0.945 |

The pressures overlap substantially. The central 90% flow ranges overlap from about 319.3 to 327.4 NL/h. The electrolyzer-only group contains 37,814 zero-flow rows. Among its 5,353 positive-flow rows versus 817 compressor-powered rows, the flow rank probability falls to **0.554**. Thus flow gives a strong marginal contrast, but positive production with overlapping pressures is empirically ambiguous. The two groups share about 10.4% of their probability mass on the development-defined joint grid. This overlap depends on bin resolution and is not an irreducible error bound.

## Exploratory candidate-set behavior

I used a single empirical rule. Pooled development quartiles define bins per channel, with positive-flow quartiles and a separate exact-zero flow bin. Each state is admitted in a joint cell if at least two distinct development segments support it. Two segments are a minimum replication heuristic. No extrapolation beyond the development ranges is allowed. A singleton is specific under this rule. Two candidates mean ambiguous. An empty set means unresolved. No test-driven adjustment was used.

| Power reference | Specific: electrolyzer only | Specific: electrolyzer + compressor | Ambiguous | Unresolved |
|---|---:|---:|---:|---:|
| Electrolyzer only | 10,762 | 0 | 1,126 | 31,279 |
| Electrolyzer + compressor | 0 | 0 | 201 | 616 |
| Unknown | 0 | 0 | 0 | 413 |

Among 43,984 rows with known power labels, specific coverage was **24.47%**, ambiguity **3.02%**, and unresolved **72.51%**. Nonfinite origin observations or observations outside the development ranges accounted for 32,002 unresolved rows including the 413 unknown-power rows. The remaining 306 unresolved rows fell in cells with insufficient development support. All specific calls matched the dominant power label in this descriptive replay. The development-majority baseline makes exactly the same decisions on those rows. On all labeled rows that baseline would agree with 43,167 of 43,984 power labels, with zero compressor-state recognition. The candidate rule preserves ambiguity or abstains on the compressor-powered rows, but adds no specific recognition of that state. These agreements do not establish a classifier error rate on an independent evaluation.

## Formal qualification and diagnostic eligibility

Formal D(Y) needs admissible observation bounds, qualified state-conditional physical predictions with uncertainty, synchronization uncertainty, and an applicable competing-hypothesis set. The source describes equipment and recorded channels. The related digital-twin deposit describes a model trained on HY2RES measurements and does not supply independently qualified bounds for this decision. Empirical cell support and observed range checks do not supply those prerequisites. Formal D(Y) diagnostic exclusion is not established by the available HY2RES evidence. Retain **INDETERMINATE**. The source documents no independently labeled faults or leak locations. Fault classification and leak localization are **NOT ESTABLISHED**. [Dataset](https://zenodo.org/records/15166733) · [Digital-twin deposit](https://zenodo.org/records/15551164)

[State signatures PNG](FIG_01_STATE_SIGNATURES.png) · [Editable SVG](FIG_01_STATE_SIGNATURES.svg)
[Candidate-set decisions PNG](FIG_02_EMPIRICAL_DECISIONS.png) · [Editable SVG](FIG_02_EMPIRICAL_DECISIONS.svg)
