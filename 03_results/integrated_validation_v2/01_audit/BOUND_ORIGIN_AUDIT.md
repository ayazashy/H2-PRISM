### BOUND_ORIGIN_AUDIT — Origin of every bound used in the formal D(Y)

No bound is experimentally calibrated; D(Y) results are conditional on these declarations and are not field safety guarantees.

| component | used_in_DY | value_basis | classification | what_would_qualify_it |
|---|---|---|---|---|
| measurement error | eps_obs = 0.5 x eps_total | hypothetical ladder S1-S6 and REF | HYPOTHETICAL | sensor datasheet accuracy or calibration records |
| sensor calibration uncertainty | not separated | none | NOT AVAILABLE | calibration certificates per sensor |
| timing uncertainty | admissible clock shift ±tau (default 1 s) | declared; Center clock is a fixed simulation grid | HYPOTHETICAL | measured synchronization error of a DAQ |
| parameter uncertainty | not separated | none | NOT AVAILABLE | parameter distributions + propagation |
| model discrepancy | eps_model = 0.5 x eps_total | hypothetical | HYPOTHETICAL | validation of the simulator against measurements |
| numerical approximation error | REF scenario | solver-refinement delta: pressure 0.03445 MPa, flow 0.01822 kg/s | COMPUTED (solver refinement), not a sensor bound | convergence study across solver settings |
| scenario variability | templates and admissible shifts | one capture per mechanism (plus one replicate for SID 213) | NOT CHARACTERIZED | multiple independent realizations per mechanism |
