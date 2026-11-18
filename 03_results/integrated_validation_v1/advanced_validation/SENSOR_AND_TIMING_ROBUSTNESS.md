# Sensor and timing robustness

**Setup.** Center formal D(Y), restricted universe, CONDITIONAL_HYPOTHETICAL_BOUNDS. Each configuration gives 24 decisions (6 queries × S3, S4, S5, REF). Results R6–R8; tables A08–A10 and A16.

## Missing sensors (13 real channels: PS1–PS10, MFS1–MFS3)

| Configuration | Correct SPECIFIC | Wrong SPECIFIC | Ambiguous (truth in / out) | Unresolved |
|---|---|---|---|---|
| All 13 | 8 | 2 | 0 / 0 | 14 |
| Pressure only (10) | 2 | 0 | 6 / 4 | 12 |
| Flow only (3) | 8 | **4** | 0 / 1 | 11 |
| Without MFS3 | 2 | 0 | 6 / 2 | 14 |
| SID 213 branch outage (MFS3, PS1) | 2 | 0 | 6 / 3 | 13 |
| SID 215 branch outage (PS4, PS8, PS9) | 8 | 3 | 0 / 0 | 13 |
| Without MFS1 | 8 | 0 | 0 / 4 | 12 |
| Any single PS removal | 8 | 2 | 0 / 0 | 14 |
| 3 random removals (20 masks, 480 decisions) | 124 | 26 | 36 / 19 | 275 |
| 4 random removals (480) | 118 | 12 | 42 / 42 | 266 |
| 7 random removals (480) | 100 | 4 | 60 / 71 | 245 |

**Answers:**

- **When pressure sensors disappear,** correct SPECIFIC decisions collapse from 8 to 2 and become ambiguity sets. No new wrong decision appears.
- **When flow sensors disappear,** pressure-only sensing gives the same result, because MFS3 carries the SID 213 separation.
- **When flow is kept and pressure is lost,** wrong SPECIFIC decisions double (2 → 4). Pressure is what excludes normal operation for the flow-blind SID 215 withdrawal.
- **Does missing evidence lead to abstention or false certainty?**
  - The engine **never creates new formal exclusions** when sensors are removed: 0 violations.
  - The *decision* can still become wrongly SPECIFIC. This happens when the removed channel was the one excluding a rival, and the truth is absent from the library.
  - Abstention and false certainty both occur. Which one depends on channel identity, not on channel count.

## Timing (R7, A09)

- **Widening the admissible clock bound τ** from 0 to 10 s changes no decision, as the invariant requires.
- **A fixed observation delay ≥ 2 s with τ = 1 s:**
  - correct SPECIFIC decisions drop from 8 to 0, and every case becomes UNRESOLVED/MODEL_MISMATCH;
  - wrong SPECIFIC decisions stay at 2, because the normal-operation template is constant and therefore delay-invariant.
- **Declaring τ = delay** restores all correct decisions.
- **A 1 s delay** is absorbed by τ = 1 s.
- **Jitter** was not tested. The captures use a fixed-step simulation clock, and the measurement contract rejects non-uniform grids.

## Pairwise isolability and minimum sensor sets (R8, A16b)

- **At the REF bounds:**

  | Channels | Hypothesis pairs separable (of 15) |
  |---|---|
  | All 13 | 14 |
  | Flow only | 14 |
  | Pressure only | 9 |

  Normal operation versus the SID 215 withdrawal is never separable at REF.
- **Exhaustive search (8,191 subsets):** two channels (MFS1 + MFS3) keep all 14 separable pairs at REF. Three channels are needed at S4, for example PS4 + MFS1 + MFS3.
- These are template-level, conditional results. They are not a field sensor-placement design.
