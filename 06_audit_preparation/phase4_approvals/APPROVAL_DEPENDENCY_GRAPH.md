# Approval Dependency Graph

A dependency model, **not** an approval. Arrows mean "must be decided before".

```mermaid
flowchart TD
  G[G-D01 local commit plan - user] -.independent.- Y01
  subgraph Yazan
    Y01[Y-D01 identity] --> Y02[Y-D02 realizations]
    Y01 --> Y03[Y-D03 19 links] --> Y04[Y-D04 family view]
    Y01 --> Y05[Y-D05a-d labels]
    Y05 --> Y06[Y-D06a/b timing]
    Y04 --> Y07[Y-D07 manifest v0.2]
    Y05 --> Y07
    Y06 --> Y07
    Y07 --> Y08[Y-D08 readiness]
    Y09[Y-D09 portability]:::par
    Y10[Y-D10 checksums]:::par
  end
  subgraph Faisal
    F15[F-D15 code acceptance]:::par
    F16[F-D16 contracts]:::par
    F14[F-D14 RF grid]:::par
    F01[F-D01 realization] --> F04[F-D04 windows]
    F05[F-D05 pre/post-event policy] --> F04
    F02[F-D02 outer design] --> F03[F-D03 inner scheme]
    F04 --> F06[F-D06 features]
    F03 --> F08[F-D08 D settings]
    F03 --> F09[F-D09 calibration]
    F10[F-D10 comparators/meta-model impl.]:::par --> F12[F-D12 threshold rule]
    F11[F-D11 policy params] --> F12
    F07[F-D07 thin classes] --> F13[F-D13 metrics/uncertainty]
    F18[F-D18 A12-A16 acceptance]:::par
  end
  subgraph Ahmed
    A05[A-D05 class definitions]
    A01[A-D01 RQ1] --> A03[A-D03 scope]
    A02[A-D02 RQ2] --> A03
    A04[A-D04 significance threshold]
    A06[A-D06 dataset description]:::par
    A07[A-D07 math sign-off]:::par
    A08[A-D08 claim register]:::par
    A09[A-D09 docs]:::par
    A11[A-D11 plans to assets]:::par
  end
  Y05 --> A05
  A05 --> F05
  Y06 --> F05
  Y04 --> F02
  Y04 --> F13
  F07 --> A01
  Y08 --> A10[A-D10 gates]
  F02 --> A03
  Y07 --> F17[F-D17 frozen config]
  F01 & F02 & F03 & F04 & F06 & F08 & F09 & F11 & F12 & F13 & F14 & F15 & F16 & A04 & A05 --> F17
  F17 --> A10
  A10 --> X[[Explicit user authorization for primary experiments]]
  classDef par fill:#eef,stroke:#88a
```

## Can start now, in parallel (no upstream decision)

- **Yazan:** Y-D01, Y-D02, Y-D03, Y-D05a–d, Y-D09, Y-D10.
- **Faisal:** F-D01, F-D02, F-D10 (implementation), F-D14, F-D15, F-D16, F-D18. F-D11 is independent of the data.
- **Ahmed:** A-D01, A-D02, A-D04, A-D06–A-D09, A-D11.
- **User:** G-D01.

## Critical path to a valid primary experiment

```
Y-D01 → Y-D05 → (A-D05 + Y-D06) → F-D05 → F-D04 → F-D06 → F-D17 → A-D10 → user authorization
            └→ Y-D03 → Y-D04 → (Y-D07 → Y-D08) and (F-D02 → F-D03 → F-D08/F-D09) ─┘
plus implementation: F-D10 meta-model and the window/feature table builder (needs F-D01, F-D04, F-D05)
```

## Reopening rule

A change to any pinned hash in `CANDIDATE_DATASET_FREEZE_SPEC.md` or `CANDIDATE_EVALUATION_FREEZE_SPEC.md` reopens every decision downstream of it in this graph.
