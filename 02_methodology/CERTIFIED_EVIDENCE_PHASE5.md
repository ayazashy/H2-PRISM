# Phase 5 source recovery and evaluation readiness

## Source execution and reconciliation

The original Center model remains blocked before model loading. The retained probe hash identifies the isolated console record containing MathWorks service error 5202. Installed MATLAB, Simulink, and Simscape files establish installation evidence only. No new launch was attempted against the known startup blocker. Presence of a proxy environment variable alone cannot identify a network cause. The source report stores no authentication or proxy values.

An authorized operator should restart Windows, open MATLAB normally, verify account and Simulink/Simscape entitlement, and then run the isolated Phase 3 Center probe once. If 5202 persists, collect Service Host logs privately for the license administrator or MathWorks support. Resume source reconciliation only after the probe loads and runs. [MathWorks error 5202 guidance](https://www.mathworks.com/matlabcentral/answers/1815390-why-do-i-receive-error-5202-unable-to-access-services-required-to-run-matlab)

The recorded source-model graph and exporter identify the same 13 reported signals in two byte-identical solver CSV aliases. The reconciliation checks the archival hashes and compares exact equality of stored decimal timestamps against the clean Parquet. It does not infer resampling or processing. Differences are expressed in native released units. Static connectivity does not supply effective signed boundary rates, complete boundary coverage or storage histories. The required conservation comparison therefore remains blocked. The source gas constant is air-like and source mixture information is unresolved.

## Numerical verification and physical eligibility

The new enclosure uses the Phase 4 steady capillary closure at the frozen table's 300 K row. Its exact mathematical input is the decimal piecewise-linear interpolant. For each rational panel, integrate pressure exactly and bound the positive product of compressibility and viscosity by endpoint ranges before outward rounding. At each candidate pressure enclose inlet minus outlet using the admitted outlet-to-inlet conductance ratio. A strict residual sign puts the unique root on one side for the entire ratio domain. Bisection relies only on these sign witnesses and the guaranteed boundary bracket.

This encloses the no-leak steady junction of the declared model. It does not enclose a real hydrogen instrument or a leaky transient. The validation matrix records verification separately from physical validation. A one-percent conductance-ratio variation is a prespecified assumption-conditional sensitivity case. The uncertainty ledger tracks pressure, mass flow, temperature, clocks, boundary inputs, initial state, gas properties, geometry, leak parameters, model discrepancy, and numerical error separately. All eleven source entries remain unknown. Model discrepancy cannot be filled with sensor calibration or the numerical enclosure width.

## Contribution and evaluation status

Trajectory consistency and guaranteed model invalidation are established set-membership ideas. Model-based fault isolation and identifiability also precede this project. Selective prediction already studies risk versus coverage, and published provenance standards distinguish evidence entities and derivations. [Set-membership model invalidation](https://arxiv.org/abs/1609.05921) · [Causal fault isolation](https://doi.org/10.1016/j.automatica.2004.06.021) · [Set-membership identifiability](https://www.sciencedirect.com/science/article/pii/S1367578813000114) · [Selective classification](https://proceedings.neurips.cc/paper/2017/hash/4a8423d5e91fda00bb7e46540e2b0cf1-Abstract.html) · [W3C PROV-DM](https://www.w3.org/TR/prov-dm/)

The matched evidence comparison tests ungated joint membership, measurement gating, replay, and conditional spatial output. The same solver yields the same joint hypothesis sets on valid matched inputs. The resampling challenge shows one withheld decision attributable to the input gate. Replay and conditional localization improve auditability in these fixtures. Neither the observed integration nor the limited literature review establishes novelty, empirical accuracy or a performance advantage.

The evaluation register counts provisional archival scenario IDs by supplied labels. Asset count, scenario labels, and related generation do not establish independent family status. No confirmatory split was frozen. Final evaluation requires separately verified generating cases with ground truth, physical bounds, and prelocked model, sensor, eligibility and comparator definitions. The proposed ontology is a draft for an instrumented two-region experiment. It is not a claim of source-wide fault coverage.

## Reproduce

From the repository root, use the existing virtual environment and new output paths.

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m h2prism.phase5 run --probe-log <isolated-console-log> --matlab-root <MATLAB-directory> --output phase5.json
.venv/Scripts/python.exe -m h2prism.phase5 replay --input phase5.json
.venv/Scripts/python.exe -m h2prism.phase5 figure --input phase5.json --output phase5.png
.venv/Scripts/python.exe -m pytest -q tests/test_phase5.py tests/test_phase4.py tests/test_network_reference.py tests/test_physical_reference.py tests/test_certified_evidence.py tests/test_data_contracts.py tests/test_gas_physics.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```

Replay regenerates the exact-alignment source comparisons, eligibility register, joint records, and steady bracket. Wall-time fields are observations. The scientific report distinguishes mathematical verification, controlled physical-model checks, archived source simulation, and independent experiments.
