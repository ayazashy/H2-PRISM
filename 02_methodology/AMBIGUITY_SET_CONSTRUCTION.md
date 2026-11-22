# Ambiguity-Set Construction (F9)

- **Status:** SPECIFIED from `policy.apply_policy`; TESTED.
- **Candidate source:** calibrated classifier probabilities p only (`candidate_source: p_only`). D(x) and q(x) do not add candidates.

1. **Eligibility:** only for windows refused as SPECIFIC (score below the acceptance rule, or a blocking flag) that are not UNRESOLVED by an unresolved flag or invalid input.
2. **Ordering:** classes by descending p, ties broken by the lower class index.
3. **Size:** the smallest prefix whose cumulative mass reaches 0.9.
4. **Rules:**
   - **Singleton** (top class alone reaches 0.9, yet SPECIFIC was refused): UNRESOLVED (`singleton_handling: unresolved`). A refused specific is never relabelled as a one-class set.
   - **All-class set** (m = K): UNRESOLVED. An uninformative set is never reported as an ambiguity.
   - **Breadth** above `max_set_size` = 2 (< K−1 = 3): UNRESOLVED (`SET_TOO_BROAD`).
   - Otherwise: AMBIGUITY_SET of size 2.
5. **Reporting (metrics.ambiguity_summary):** inclusion rate (true class ∈ S), mean and median size, and broad rate, always alongside the ambiguity count. UNRESOLVED and AMBIGUITY_SET are never counted as correct SPECIFIC decisions.

**Consequence:** with max_set_size 2, every ambiguity set is a pair of the two most probable classes whose combined mass is ≥ 0.9.
