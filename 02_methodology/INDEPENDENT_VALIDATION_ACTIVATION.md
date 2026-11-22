# Independent validation activation, protocol v1

Phase 8 found no new experimental package in the checked local repository data and handoff locations, prior phase artifacts, or matching local download files. The H2-SimNet archive is simulation evidence. No private communications or accounts were searched. There are zero newly eligible independent families and no independent validation metrics.

## Acquisition and preflight

Use the existing experimental CSV contract. Supply original timestamped pressure and signed mass-flow data, reusable rights covering the intended reporting, acquisition-to-file lineage, independent run histories, and independently recorded event labels and leak regions. Those are fatal gaps if unresolved. Geometry and sensor locations can be independently surveyed. Operating conditions, measurement calibration and leak parameters can be recovered or defensibly bounded from applicable independent evidence. Recovery and bounding must be documented before qualification. Numeric estimation cannot replace event truth, ancestry or rights.

For a real delivery, preserve the source bytes. Build an ExperimentManifest and EvidenceReference records. Call `validation_activation.accept(csv_path, manifest, evidence, rig_mapping, model_artifact_path)`. The rig mapping uses separate IDs for the rig and model. Check the signed graph, instrument locations, gas, governing equations, discharge and dynamic assumptions, uncertainty, and discrepancy against an independently reviewed model. A valid checksum and matching topology establish traceability. Physical validation requires independent evidence. No current reference topology is selected by default.

Use `protocol_preflight(intakes, splits, locked_sha256, analysis_plan_sha256=...)` before scoring. The analysis plan must be finalized before held-out outcome inspection and pin sample-size adequacy, family-level analysis and any tuning. Use development cases for fitting and separate validation cases to check applicability. Reserve held-out independent whole-run families, with both NORMAL and LEAK represented in validation and held-out groups. A minimum class check is not a sample-size justification. Archive the lock externally before scoring. The preflight checks drift against the supplied lock. It does not establish its timestamp or independently verify review attestations.

Use the same physics, measurements, uncertainty and solver for conventional joint set membership and the H2-PRISM policy. H2-PRISM adds evidence gating and conditional localization. Region scoring requires verified region truth and specific LEAK evidence. Existing family-level metrics in `phase2_evaluation.summarize` define coverage and selective risk, with unavailable metrics represented as null. No scorer was run in Phase 8.

## MATLAB source track

The last authorized attempt remains the Phase 6 startup failure with error 5202. Do not rerun the isolated probe until there is evidence of a working authorized startup. An authorized operator can restart Windows, open MATLAB normally, verify entitlement and successful checkout for Simulink and Simscape, and then run the isolated checksum-verified probe. If 5202 persists, share Service Host diagnostics privately with MathWorks or the license administrator and follow their instructions. A successful startup does not close source lineage, signed flow, storage, or uncertainty gaps. [MathWorks guidance](https://www.mathworks.com/matlabcentral/answers/1815390-why-do-i-receive-error-5202-unable-to-access-services-required-to-run-matlab)

## Reproduce from the repository root

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m h2prism.validation_activation --output phase8.json
.venv/Scripts/python.exe -m pytest -q tests/test_experimental_data.py tests/test_phase6.py tests/test_phase5.py tests/test_phase4.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```
