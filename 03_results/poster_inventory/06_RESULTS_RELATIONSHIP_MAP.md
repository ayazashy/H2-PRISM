# 06 — Results relationship map

The repository's results form **two evidence branches plus a transfer boundary**. They are not one linear chain.

- **Branch F — formal evidence (D(Y), Center).** Mathematically verified decision semantics, applied to controlled, model-conditional data.
- **Branch L — learned scores and selective classification (D(x), s_C, R2).** Registered and exploratory statistical results, dominated by a label-attribution defect.
- **Boundary T — transfer.** Cross-domain portability and gas qualification, mostly blocked.

The candidate sequence in the brief (formal integrity → isolability → sensor and uncertainty sensitivity → decision behaviour → robustness → engineering feasibility) fits Branch F well. It does not absorb Branch L, which answers a different question with different data.

## Dependency graph (edges labelled by relationship type)

```
                    [E0] Evidence base & independence
                    Q1_I06 · V2-T09 · AV-F02 (label defect)
                      |  qualifies everything below
          ┌───────────┴─────────────────────────────┐
          v                                          v
  BRANCH F (formal, Center)                 BRANCH L (learned, R2)
  [F1] Formal integrity                     [L1] Registered H1 status
       AV-F05 + A04a (+ proof)                   H1-F01 (+ H1-T02)
          | answers next Q: "what CAN              | qualifies: why only exploratory
          |  be distinguished?"                     v
          v                                 [L2] Exploratory selective risk
  [F2] Observability → isolability               H1-F02a / AV-F01, H1-F02b
       Q1_C01 or V2-F04 → V2-F03 or AV-F07          | reveals limitation
          | answers next Q: "what does the          v
          |  engine actually decide?"        [L3] Label-defect attribution
          v                                      AV-F02, V2-T09, Q1_I05
  [F3] Decision semantics & behaviour             | answers next Q: "is D(x) the
       Q1_C15 (+ Q1_C14, T07b)                    |  cause of any gain?"
          | reveals limitation                     v
          v                                 [L4] D(x) incremental value: negative
  [F4] Library completeness                      V2-F01 (+ V2-T01), H1-F02b
       AV-F04 / H1-F06 (+ A05)
          | strengthens/qualifies F3
          v
  [F5] Robustness: sensors, faults, timing
       AV-F08, V2-F02 (synthetic), AV-F09
          | independent evidence on same captures (not independent data)
          v
  [F6] Engineering feasibility
       A14b / AV-F12 (compute), A16b (min sensors), AV-F13 (count; no prices)

  BOUNDARY T: V2-F05 (HY2RES Level-A port) · AV-F14 / A13 (gas: blocked) · Q1_I07
  SYNTHESIS:  V2-F06 / HYPOTHESIS_REGISTRY (H1–H10 statuses)
```

## Edge-by-edge assessment

| From → to | Relationship | Justification |
|---|---|---|
| E0 → F1, L1 | Qualifies | One Center source family; 17 R2 templates; disputed labels in 36/57 R2 runs |
| F1 → F2 | Answers a new question | Once exclusions are sound, which hypothesis pairs can be excluded at all? |
| F2 → F3 | Answers a new question | Isolability is a template property; F3 shows decisions on captured observations |
| F2 → F3 | Strengthens | The SID 215–Normal inseparability (V2-F03/F04) explains the 2 wrong SPECIFIC decisions in Q1_C14 |
| F3 → F4 | Reveals a limitation | Restricted-universe wrong SPECIFIC decisions arise from library incompleteness |
| F3 → F5 | Answers a new question | How do decisions change when sensors are lost or corrupted? |
| F5 → F6 | Qualifies | Resource feasibility (0.36 s per decision; MFS1+MFS3 minimum set) is conditional on the same bounds |
| L1 → L2 | Qualifies | Registered test not estimable, so the exploratory curves are the only available view |
| L2 → L3 | Reveals a limitation | 7,347/8,012 errors and all 1,019 s_C errors at 0.25 sit in disputed runs |
| L3 → L4 | Answers a new question | Is the s_C advantage due to D(x)? Out-of-template, D adds nothing |
| F3 ↔ L2 | **Do not merge** | Different engines, data and decision rules; "SPECIFIC" means certified exclusion in F and threshold acceptance in L |
| F2 ↔ AV-F07 vs V2-F03 | Duplicate | Same pairs; binary at REF vs onset scale. Choose one |
| F3: Q1_C15 vs T07b vs TAB_C06 | Duplicate | Same decisions at different granularity |
| F4: AV-F04 vs H1-F06 | Duplicate | H1-F06 adds sensor-group rows |
| L2: AV-F01 vs H1-F02a | Duplicate | Same curves |
| T: V2-F05 vs AV-F15 | Supersedes | V2-F05 adds executed Level-A portability |
| Synthesis: V2-F06 vs AV-F16 vs Q1_I09 vs H1-F07 | Supersedes or duplicate | V2-F06 is the current registry view |

## Stages that should not be forced together

- Branch L's selective-risk curves and Branch F's decision shares share the words "SPECIFIC" and "coverage", but the definitions differ.
- HY2RES and MHC reference prediction (persistence vs Ridge) is context for measurement resolution. It is not diagnostic evidence and belongs in no diagnostic stage.
- Synthetic studies (V2-F02, V2-F01 panel b) may sit beside the real-data result they qualify. They cannot replace it.

## Alternative orderings the evidence supports

1. **Capability-first (F1→F6, then L as a limitation box).** Leads with what is verified.
2. **Question-first (L1→L4 then F).** Follows the registered research question (H1), then shows the formal engine as the response to its non-estimability.
3. **Claim-ledger.** Groups by evidence class (verified / conditional / exploratory / negative / blocked), using V2-F06 as the spine.

All three are worked out in `07_POSTER_STRUCTURE_ALTERNATIVES.md`.
