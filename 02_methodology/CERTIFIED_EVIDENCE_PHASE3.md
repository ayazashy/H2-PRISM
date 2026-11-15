# Phase 3 network benchmark

The controlled model uses a four-storage star with signed prescribed branch transfers, one net supply boundary, three withdrawal boundaries, four pressure sensors, and three branch mass-flow sensors. The orientation is from junction J to each leaf. Negative transfer reverses direction. Connecting transfers cancel in the network sum.

For storage i, each step integrates the declared discrete balance

`M_i[k+1] = M_i[k] + dt (b_i + sum(q_in) - sum(q_out) - q_leak,i[k])`.

The pressure relation is `p_i[k] = R T M_i[k] / V_i` for the constructed constant-temperature ideal gas. Branch rates are prescribed, so pressure does not drive branch flow. The model includes neither momentum propagation nor compressor control. It does not estimate a leak by flow-only sensing in this configuration.

The leak represents isentropic discharge from a lumped upstream storage to a specified ambient pressure. For choked flow, `q_leak = Cd A p sqrt(gamma/(RT)) (2/(gamma+1))^((gamma+1)/(2(gamma-1)))`. The benchmark deliberately sets gamma to 3 and RT to 30000 J/kg, giving a rational multiplier at every step. These properties are a constructed mathematical reference. The adapter rejects parameters or trajectories that cannot be shown to remain positive, choked and in the monotone Euler domain. The equal-pressure and unchoked checks use the existing generic orifice evaluator only as numerical verification. [NASA Glenn choked-flow derivation](https://www.grc.nasa.gov/www/k-12/BGP/mflchk.html)

The enclosure uses exact rational arithmetic. For a leak storage with update `M'=(1-dt*k)M+dt*b`, the entire prior positive mass interval, bounded nondirectional loss coefficient, signed-transfer range and bounded external rate give a monotone outer interval. Repeated uncertain inputs are relaxed across steps, which can widen enclosures. A disjoint measured coordinate proves exclusion over the declared discrete box. Feasibility checks a single shared parameter vector on the entire trajectory. Replay regenerates the configured case and compares the complete hash-bound record. The enclosure covers the discrete dynamics and supplies no continuous-time integration error bound.

Regions are normalized branch categories. One executed case splits a branch into two spatial labels sharing its lumped response. The policy returns L1 for those two regions after excluding non-leak alternatives. L2 requires one feasible region and exclusion of every declared competitor. Declared unsupported compressor and delay competitors keep localization at L0. No continuous spatial resolution is reported.

## Reproduction

Run from the repository root with the existing virtual environment. Output paths must be new. The figure requires Matplotlib.

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m pytest -q tests/test_network_reference.py tests/test_physical_reference.py tests/test_certified_evidence.py tests/test_data_contracts.py tests/test_gas_physics.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
.venv/Scripts/python.exe -m h2prism.phase3 benchmark --output network_benchmark.json
.venv/Scripts/python.exe -m h2prism.phase3 replay --input network_benchmark.json
.venv/Scripts/python.exe -m h2prism.phase3 source --output source_topology.json
.venv/Scripts/python.exe -m h2prism.phase3 figure --input network_benchmark.json --output network_benchmark.png
```

For a source probe, copy the versioned Center SLX into a fresh writable scratch directory, create a preferences subdirectory, and set `MATLAB_PREFDIR` to it. Run `matlab.exe -wait -batch "addpath('<repository>/tools/simulation'); h2prism_phase3_normal_probe('<scratch>')"` and capture console output. Pass that log to the source command with `--input`. The attempted probe failed during MATLAB startup with MathWorks service error 5202. It produced no solver output. The static source graph preserves port connections without inferring signed flow from Simulink wiring.

The matched comparator retains every hypothesis whose shared rectangular enclosure intersects the observation box. It uses the same physics, model domains, and measurements. A disagreement establishes the value of checking a common witness against coordinate-wise retention in that case. It does not establish an improvement over exact joint set-membership or empirical accuracy. Profiles vary window length on a fixed graph. The cases share a constructed model, so all reported rates are descriptive.
