# Phase 4 validation scope and interpretation correction

The Phase 3 gamma-3 constructed gas and four-storage discrete results are an **exact mathematical benchmark**. Phase 3's comparator is coordinate-wise outer-envelope retention. It does not solve joint set membership. Phase 4 preserves those artifacts and adds a distinct **physically parameterized reference model** with pinned normal-hydrogen thermophysical data. The Center SLX and Parquet are **source-derived simulation evidence**. Independent experimental validation remains unavailable.

## Shared trajectory constraints

The three-sample solver uses precisely the Phase 3 equations and parameter boxes, fixed initial masses and fixed internal branch transfers. For a storage with retention r and shared rate increment b, the samples are m0, r m0+b, and r² m0+(1+r)b. Each measured channel at that storage bounds these same states. Intersect the implied lower and upper bounds on b. Because r is nonnegative, multiplying by the denominators gives polynomial inequalities with unchanged signs. In a leak storage r is coupled to the product of the declared opening and discharge coefficient. Nonnegative parameter boxes make the attainable product an interval. Accepted witnesses reconstruct an admissible pair.

Subdivision can reject a cell only when a necessary inequality is strictly violated throughout. The exact rational proof records a covering partition of the retention domain and one violated polynomial per cell. The engine checks the cover and signs. Full replay reconstructs the model, original observations, inequalities and outcome. Unresolved boundary cases, irrational-only witnesses, exhausted budgets and unsupported domains may remain indeterminate. The result is therefore a sound joint procedure with incomplete termination, including exact decisions for the executed cases. It makes no claim for general continuous-time networks.

Conventional joint-set evaluation and the H₂-PRISM policy use the same solver. A difference with Phase 3 coordinate retention or midpoint search is a solver-information difference. A QC counterfactual preserves values but marks one channel resampled. The ungated consistency calculation stays mathematically feasible while the policy correctly withholds diagnosis.

## Pressure-driven reference

The benchmark is two symmetric branches with pressure-controlled supply and sink, two long capillaries per branch and a junction at which loss may occur. The steady, inertia-free, fully developed isothermal laminar closure is

`q = (pi D^4 / (128 L)) integral[p_down,p_up] (rho(p,T) / mu(p,T)) dp`.

This follows from local Poiseuille flow with mass conservation. It omits wall slip, entrance effects, and inertial and thermal corrections. The numerical root balances inlet, outlet and separate leakage at each junction. Junction mass is rho V. The separate analytical limit has equal sealed storages, a fixed coefficient multiplying the signed pressure-squared difference, and no leak. Pressure sum is constant and the difference decays exponentially. The alternating-series remainder bounds the continuous analytical solution for decay times time between zero and one. These bounds do not apply to the tabulated or leaky system. [NIST capillary closure and corrections](https://www.nist.gov/publications/simple-flow-meter-and-viscometer-high-accuracy-gases)

Use 300 K and 0.10–0.22 MPa absolute within the pinned normal-hydrogen table. The existing loader verifies the table hash and uses the existing interpolator without extrapolation. The property basis is Leachman's hydrogen EOS and the table's recorded transport correlations. Geometry, pressures, isotherm, discharge area and coefficient are explicit constructed inputs. Laminar and low-velocity screening limits are engineering choices. They are not experimentally determined error bounds. The leak calculation freezes the upstream heat capacity in a local ideal-gas isentropic orifice approximation. It distinguishes choked, unchoked and zero loss in domain. It is not a validated real-gas critical-flow model. Root and quadrature refinement, mass balance and constant-property checks provide numerical verification. Physical discrepancy and instrument error remain unbounded. [NIST hydrogen EOS](https://www.nist.gov/publications/fundamental-equations-state-parahydrogen-normal-hydrogen-and-orthohydrogen) · [NASA Glenn ideal-gas choking](https://www.grc.nasa.gov/www/k-12/BGP/mflchk.html)

## Source gate and reproduction

The Center checksum matched. MATLAB R2026b and Simulink, Simscape and Foundation library files were present. The previous isolated probe reached startup error 5202 before model loading. Phase 4 checked the recorded console evidence and installation without repeating the failed startup or altering licensing. Service Host was not observed running at the check. The public status page listed Online Licensing and License Center as operational. This evidence supports a local startup blocker and does not identify its root cause or prove an invalid entitlement. Authorized local diagnosis and successful license checkout are required before running the Phase 3 probe. Effective signed flows, runtime histories and the release transformation remain unknown. [Official MathWorks 5202 guidance](https://www.mathworks.com/matlabcentral/answers/1815390-why-do-i-receive-error-5202-unable-to-access-services-required-to-run-matlab) · [MathWorks service status](https://status.mathworks.com/)

Run from the repository root using new output files.

```powershell
$env:PYTHONPATH='src'
.venv/Scripts/python.exe -m h2prism.phase4 benchmark --output phase4-results.json
.venv/Scripts/python.exe -m h2prism.phase4 replay --input phase4-results.json
.venv/Scripts/python.exe -m h2prism.phase4 figure --input phase4-results.json --output phase4.png
.venv/Scripts/python.exe -m h2prism.phase4 source --input <probe-console-log> --matlab-root <MATLAB-directory> --output source-status.json
.venv/Scripts/python.exe -m pytest -q tests/test_phase4.py tests/test_network_reference.py tests/test_physical_reference.py tests/test_certified_evidence.py tests/test_data_contracts.py tests/test_gas_physics.py
.venv/Scripts/python.exe -m pytest -q -m 'not slow'
```

All controlled records share a constructed configuration and are ineligible for confirmatory evaluation. They cannot establish independent diagnostic performance. No empirical source risks, physical leak localization rates, or deployment claims follow.
