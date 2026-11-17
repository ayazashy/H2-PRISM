#!/usr/bin/env python3
"""
X20 feasibility probe (read-only, no tables written): can CoolProp (the H2Net v1 property environment, .venv-h2props,
CoolProp 7.2.0) evaluate H2-CH4 blends? Prints the binary-pair source, default-flash behaviour and imposed-gas-phase
properties at 300 K, 5 MPa. Output is evidence for 02_methodology/GAS_COMPOSITION_INTERFACE.md, not a property source.
Run: .venv-h2props/Scripts/python.exe tools/simulation/probe_h2ch4_feasibility.py
"""
import json

import CoolProp
import CoolProp.CoolProp as CP

out = {"coolprop_version": CoolProp.__version__, "state": {"T_K": 300.0, "p_Pa": 5e6}}
a, b = CP.get_fluid_param_string("Hydrogen", "CAS"), CP.get_fluid_param_string("Methane", "CAS")
out["binary_pair"] = {k: CP.get_mixture_binary_pair_data(a, b, k) for k in ("function", "F", "betaT", "gammaT", "betaV", "gammaV", "BibTeX")}
rows = []
for x in (0.05, 0.1, 0.2, 0.9):
    r = {"x_CH4": x}
    AS = CoolProp.AbstractState("HEOS", "Hydrogen&Methane")
    AS.set_mole_fractions([1 - x, x])
    try:
        AS.update(CoolProp.PT_INPUTS, 5e6, 300.0)
        r["default_flash"] = "OK"
    except ValueError as e:
        r["default_flash"] = "FAILED: " + str(e).split(" for ")[0]
    AS.specify_phase(CoolProp.iphase_gas)
    AS.update(CoolProp.PT_INPUTS, 5e6, 300.0)
    r.update(Z=AS.compressibility_factor(), rho=AS.rhomass(), cp=AS.cpmass(), mu=AS.viscosity(), k=AS.conductivity())
    rows.append(r)
out["imposed_gas_phase"] = rows
print(json.dumps(out, indent=1))
