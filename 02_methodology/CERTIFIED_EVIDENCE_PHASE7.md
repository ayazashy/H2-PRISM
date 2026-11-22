# Phase 7 experimental acceptance gate

The archive audit independently reads the pinned Center solver CSV aliases, the clean CSV and Parquet, and the separate top-level release CSV. It contrasts all 13 source-backed channels on their exact stored clocks. The 1e-9 native-unit threshold distinguishes numerical serialization equivalence. It supplies no physical error bound. The audit rejects five narrowly stated explanations acting alone. No producing run or exact transformation was recovered.

No successful authorized MATLAB startup evidence was found. The Phase 6 console record remains the latest execution evidence. An authorized operator should restart Windows if needed, open MATLAB normally, and verify toolbox entitlement before running the isolated Center probe once. If error 5202 persists, share the Service Host logs privately with the license administrator or MathWorks. Source certification still requires the effective model, raw logs, release lineage, signed flow and storage evidence, and bounded uncertainty. [MathWorks guidance](https://www.mathworks.com/matlabcentral/answers/1815390-why-do-i-receive-error-5202-unable-to-access-services-required-to-run-matlab)

The experimental adapter accepts UTF-8 common-clock CSV and a typed ExperimentManifest. An external, evidence-backed PhysicsApproval is a distinct input. It verifies file bytes, preserves original clock tokens, maps declared SI channels with absolute pressure and network-oriented signed flow into MeasurementContract, and exposes missing rows without imputation. Independently sourced instrument bounds and uncertainty records are required. File or label metadata alone cannot establish approval or physical truth. Profiles with other clocks or units require independently documented normalization before ingestion. Exact duplicate detection hashes the normalized channel sample vectors separately from source bytes. Shared-history and split protection also depends on verified whole-run ancestry. No algorithm can recover undocumented ancestry from overlapping windows alone.

T1 fixtures may demonstrate ingestion but cannot enter a confirmatory split. T2 is controlled simulation, T3 requires reproduced source simulation, and T4 requires independently measured experimental evidence. The Center archive is T3 provenance material with reproduction pending. No dataset was qualified in Phase 7 and no independent performance metrics were run. The Ibrahim data request is a draft. [Hydrogen experiments](https://doi.org/10.1016/j.jlp.2024.105452) · [Multiphase experimental plant](https://zenodo.org/records/16978349) · [PE pressure decay](https://zenodo.org/records/20582921)

Run from the repository root with fresh output paths.

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m h2prism.phase7 --phase6-probe-log <isolated-console.txt> --output phase7.json
.venv/Scripts/python.exe -m pytest -q tests/test_experimental_data.py tests/test_phase6.py tests/test_phase5.py tests/test_phase4.py tests/test_network_reference.py tests/test_physical_reference.py tests/test_certified_evidence.py tests/test_data_contracts.py tests/test_gas_physics.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```
