# H₂-SimNet Phase 9 readiness

The pinned V03 candidate manifest and historical relationship ledger drive this report. Format twins, known same-injection prefixes, byte aliases and exact clean sensor trajectories are confirmed dependence evidence. Cross-topology scenario designs, extended family labels and short shared prefixes are potential dependence. The earlier solver-export association is retained as potential because its generating lineage has not been resolved. Unlisted pairs have unknown relations. Connected components use transitive closure. The split policy joins both confirmed and potential edges and does not join runs by topology or event alone.

Candidate partitions are retrospective and proposed. Each split keeps every connected component in one partition. Freeze one scoring representative per held-out component before outcomes are inspected. The original topology holdouts do not qualify under this dependency policy. The forensic case-attribution table establishes previous inspection of the archive and does not document exposure to every individual decision. A new confirmatory collection would require separately evidenced untouched generating runs.

At activation, `evaluate_heldout` requires the locked protocol and a separate hash-pinned review with status `APPROVED_AND_FROZEN`, the exact `protocol_sha256`, and an `approval_reference`. The protocol adds `evaluation_claim` set to `RETROSPECTIVE_DESCRIPTIVE_ONLY`, `independence_graph_sha256`, and `heldout_representatives` to the [source study contract](H2_SIMNET_SOURCE_STUDY.md). The review is supplied explicitly by the caller. The software checks the record and protocol binding and does not attest the authority of its author. No approval or scoring was issued in Phase 9.

The runtime physics gate also requires a structured effective gas record, absolute pressure, oriented port mappings for signed mass flow, storage history, a numerical error enclosure, and evidence for each mechanism in the scoped ontology. The static G labels are linked to restriction candidates for inspection. Topology conflicts and multisite flags are retained. A compiled leak command history and sensor response are required before any region becomes eligible.

The source track still needs authorized MATLAB startup and Simulink/Simscape checkout. Then follow the [isolated Center capture procedure](H2_SIMNET_SOURCE_STUDY.md) once. Reconcile the raw capture to the release before attempting a matched LEAK, certify the supported model and bounds, and review dependence and exposure before scoring. Keep compressor-fault and delay outside a restricted NORMAL/LEAK characterization unless their mechanisms and command histories qualify.

## Reproduce

From the repository root, write to fresh output paths.

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m h2prism.simnet_readiness --output readiness.json --figure readiness.png
.venv/Scripts/python.exe -m pytest -q tests/test_simnet_readiness.py tests/test_simnet_study.py tests/test_phase6.py tests/test_phase5.py tests/test_phase4.py tests/test_network_reference.py tests/test_certified_evidence.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```
