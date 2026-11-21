# Phase 2 physical reference and source bridge

## Controlled model

One fixed-volume, well-mixed, isothermal control volume uses the existing constant-property gas equation of state. Its exact affine pressure is

`p(t) = (Z R T / V) [M0 + (t - t0) (q_in - q_out - q_leak)]`.

Mass is in kg, directional rates in kg/s, pressure in Pa, time in s. Each rate is nonnegative in its declared direction. The outlet excludes the separately modeled extra withdrawal. The model rejects domains with nonpositive possible mass. The LEAK fixture is a controlled constant withdrawal at the volume. It has no orifice, spatial propagation, or validated pipeline fault mechanism. Geometry, gas, initial storage, and uncertainty are constructed benchmark inputs. Clock and discrepancy are exactly zero for this fixture. The affine engine evaluates the declared numeric values as exact rationals, checks joint witnesses, and excludes only by disjoint coordinate intervals over the full parameter box. Midpoint search is incomplete and may leave feasible cases indeterminate.

## Source observation

Selection used an eligible clean NORMAL Parquet with a named local source model and a stored time index. The Center case was chosen before diagnosis. The runner verifies data and model hashes and records the installed inventory, block-port connectivity, serialized geometry and initial targets, sensor block/converter identities, uncertainty gaps, and window ancestry. Source inputs are read directly through the existing loader and retain native units and timestamps. Rows 0–2 form one QC window from the single manifest family, FAM_NORMALITY.

The source converter units are MPa for PS1–PS10. MFS1–MFS3 trace to mass-flow-rate blocks with inherited converter units and documented kg/s in the release. Their control-volume roles and signs are unresolved. PS11, PS12, and MFS4 are absent from the Center exporter and are excluded from this bridge. Temperature is absent from the export. Static XML records pipe lengths and areas, initial targets, controlled and atmospheric reservoirs, and controlled pressure sources. It cannot establish the actual initialized state, time-varying operating inputs, or full signed boundary flows used for the released observation. The launcher and exporter trace the model to an original solver CSV. The transformation from those logs to the 1 s Parquet and exact effective model settings are unverified.

Gas block SID 4 has R = 0.287 kJ/(kg K), Z = 0.998386, and a serialized perfect-gas configuration. This is an air-like specific gas constant. The title does not establish composition. The listed model parameter limits are not a physical validation domain. No bench gas is substituted into source outputs. The source case has no finite verified error sets and no admissible source adapter. All four declared hypotheses stay indeterminate. The source run supplies no diagnostic risk estimate.

## Reproduce from the repository root

Use the existing virtual environment with pandas, a Parquet engine, and pytest. Matplotlib is used by the optional figure command. Each execution expects a fresh output directory.

```powershell
$env:PYTHONPATH = 'src'
.venv/Scripts/python.exe -m h2prism.phase2 normal --output example-runs/normal
.venv/Scripts/python.exe -m h2prism.phase2 leak --output example-runs/leak
.venv/Scripts/python.exe -m h2prism.phase2 overlap --output example-runs/overlap
.venv/Scripts/python.exe -m h2prism.phase2 missing --output example-runs/missing
.venv/Scripts/python.exe -m h2prism.phase2 source --output example-runs/source
.venv/Scripts/python.exe -m h2prism.phase2 replay --output example-runs/normal/result.json
.venv/Scripts/python.exe -m h2prism.phase2 figure --input example-runs/overlap/result.json --output example-runs/overlap.png
.venv/Scripts/python.exe -m pytest -q tests/test_physical_reference.py tests/test_certified_evidence.py tests/test_data_contracts.py tests/test_gas_physics.py
```

Result JSON contains deterministic evidence and exact replay inputs. Wall time is separate. Replay checks a claimed proof against the named reference configuration and its measured interval. Per-case accounting identifies decision and hypothesis rates. These deliberately constructed cases share a model and cannot support an independent diagnostic performance estimate. The evaluation utility requires one eligible decision per declared family and separates evidence domains. It reports undefined risk as null. No fitting or calibration is run. Source-derived compressor, delay, localization, and empirical comparisons remain deferred.
