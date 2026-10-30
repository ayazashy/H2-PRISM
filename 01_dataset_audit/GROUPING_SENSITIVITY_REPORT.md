# H2-PRISM Grouping Sensitivity Report (Task Y2)
**Author**: Yazan (Lead, Dataset Audit, Data Engineering & Dataset Readiness)  
**Date**: 2026-10-30 18:22:42 UTC

### Grouping Philosophies:
1. **Conservative Grouping (Recommended Baseline for Primary Evaluation)**:
   - Primary Unit: `Scenario_Family_ID` (13 families).
   - Keeps all parameter variants (weak/strong) and noisy variants strictly together in the same fold.
   - Prevents all configuration leakage.
2. **Topology-Stratified Grouping (Secondary Sensitivity)**:
   - Primary Unit: `(Scenario_Family_ID, Topology)`.
   - Tests whether a model trained on Center and Upstream topologies can generalize to Downstream topology.
3. **Strict Granular Grouping (Exploratory Only)**:
   - Primary Unit: `Scenario_ID` (61 scenarios).
   - Allows weak/strong variants to be separated only if explicit leakage testing confirms independence (NOT recommended for primary claims).
