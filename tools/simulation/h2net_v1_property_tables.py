#!/usr/bin/env python3
"""
MODEL_DEVELOPMENT:H2NET_V1 step (a): normal-hydrogen property tables in the layout and units of the Simscape
Gas Properties (G) REAL-GAS fields (as stored in the released block: T_TLU2 [K] x p_TLU2 [MPa]; rho kg/m^3,
s kJ/(kg K), h kJ/kg, cp kJ/(kg K), mu uPa s, k mW/(m K), beta (isothermal bulk modulus) MPa, alpha (isobaric
expansion) 1/K; matrices of shape len(T) x len(p)), plus the V1 validation report.

Reference: CoolProp (version pinned and recorded) fluid 'Hydrogen' = normal hydrogen; the equation-of-state and
transport references are read from the library at run time and recorded (expected Leachman 2009, Muzny 2013,
Assael 2011). V1 checks (HYDROGEN_MODEL_SPECIFICATION.md section 4):
  * interpolation fidelity: bilinear table interpolation vs direct EOS at >= 50 off-grid points inside the
    envelope 250-400 K x 0.1-10 MPa (rho <= 0.1 %, cp <= 0.5 %, mu and k <= 1 %);
  * physical consistency: gamma = cp/cv (EOS) in (1, 5/3], Prandtl in (0.5, 1.0), R = R_u/M, Z -> 1 at low p;
  * an independent anchor: density at 273.15 K, 101.325 kPa = 0.0899 kg/m^3 (+-0.3 %).
Must run in the isolated environment: .venv-h2props/Scripts/python.exe tools/simulation/h2net_v1_property_tables.py
Writes 06_audit_preparation/simulation/h2net_v1/properties/{H2_REALGAS_TLU2.json, H2_REALGAS_TLU2_params.m,
V1_REPORT.json, ENVIRONMENT.txt}.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np

import CoolProp
import CoolProp.CoolProp as CP

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "properties"
FLUID = "Hydrogen"
R_U = 8.314462618
T_GRID = np.arange(200.0, 500.0 + 1e-9, 10.0)                                     # K (31 points)
P_GRID_MPA = np.array([0.05, 0.08, 0.1, 0.15, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
                       10.0, 12.0])                                              # MPa (20 points)
ENVELOPE = {"T": (250.0, 400.0), "p_MPa": (0.1, 10.0)}
TOL = {"rho": 1e-3, "cp": 5e-3, "mu": 1e-2, "k": 1e-2}


def props(T, p_pa):
    g = lambda k: CP.PropsSI(k, "T", T, "P", p_pa, FLUID)  # noqa: E731
    return {"rho": g("Dmass"), "s": g("Smass") / 1e3, "h": g("Hmass") / 1e3, "cp": g("Cpmass") / 1e3,
            "cv": g("Cvmass") / 1e3, "mu": g("viscosity") * 1e6, "k": g("conductivity") * 1e3,
            "beta": 1.0 / g("isothermal_compressibility") / 1e6, "alpha": g("isobaric_expansion_coefficient"),
            "Z": g("Z")}


def tables():
    keys = ("rho", "s", "h", "cp", "mu", "k", "beta", "alpha", "Z", "cv")
    out = {k: np.empty((len(T_GRID), len(P_GRID_MPA))) for k in keys}
    for i, T in enumerate(T_GRID):
        for j, p in enumerate(P_GRID_MPA):
            pr = props(T, p * 1e6)
            for k in keys:
                out[k][i, j] = pr[k]
    return out


def bilinear(tab, T, p_mpa):
    i = min(np.searchsorted(T_GRID, T, "right") - 1, len(T_GRID) - 2)
    j = min(np.searchsorted(P_GRID_MPA, p_mpa, "right") - 1, len(P_GRID_MPA) - 2)
    tt = (T - T_GRID[i]) / (T_GRID[i + 1] - T_GRID[i])
    pp = (p_mpa - P_GRID_MPA[j]) / (P_GRID_MPA[j + 1] - P_GRID_MPA[j])
    return ((1 - tt) * (1 - pp) * tab[i, j] + tt * (1 - pp) * tab[i + 1, j]
            + (1 - tt) * pp * tab[i, j + 1] + tt * pp * tab[i + 1, j + 1])


def mat(a):
    a = np.atleast_2d(a)
    return "[" + "; ".join(" ".join(f"{v:.10g}" for v in row) for row in a) + "]"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    tab = tables()
    M = CP.PropsSI("M", FLUID)
    R = R_U / M
    # ---- V1 interpolation fidelity at off-grid points (cell centres) inside the envelope
    Ts = [T for T in (T_GRID[:-1] + 5.0) if ENVELOPE["T"][0] <= T <= ENVELOPE["T"][1]]
    ps = [p for p in 0.5 * (P_GRID_MPA[:-1] + P_GRID_MPA[1:]) if ENVELOPE["p_MPa"][0] <= p <= ENVELOPE["p_MPa"][1]]
    errs = {k: [] for k in TOL}
    gam, prn, n_pts = [], [], 0
    for T in Ts:
        for p in ps:
            ref = props(T, p * 1e6)
            n_pts += 1
            for k in TOL:
                errs[k].append(abs(bilinear(tab[k], T, p) / ref[k] - 1))
            gam.append(ref["cp"] / ref["cv"])
            prn.append(ref["cp"] * 1e3 * ref["mu"] * 1e-6 / (ref["k"] * 1e-3))
    max_err = {k: float(np.max(v)) for k, v in errs.items()}
    anchor = CP.PropsSI("Dmass", "T", 273.15, "P", 101325.0, FLUID)
    checks = {
        "interpolation_points": n_pts,
        "interpolation_max_relative_error": max_err,
        "interpolation_pass": {k: max_err[k] <= TOL[k] for k in TOL},
        "gamma_range": [float(min(gam)), float(max(gam))],
        "gamma_pass": bool(1.0 < min(gam) and max(gam) <= 5.0 / 3.0),
        "prandtl_range": [float(min(prn)), float(max(prn))],
        "prandtl_pass": bool(0.5 <= min(prn) and max(prn) <= 1.0),
        "R_J_per_kgK": R, "molar_mass_kg_per_mol": M,
        "Z_at_lowest_pressure_range": [float(tab["Z"][:, 0].min()), float(tab["Z"][:, 0].max())],
        "Z_low_pressure_pass": bool(np.all(np.abs(tab["Z"][:, 0] - 1) < 0.01)),
        "Z_envelope_range": [float(tab["Z"][(T_GRID >= 250) & (T_GRID <= 400)][:, P_GRID_MPA <= 10].min()),
                             float(tab["Z"][(T_GRID >= 250) & (T_GRID <= 400)][:, P_GRID_MPA <= 10].max())],
        "anchor_density_273K_1atm": anchor, "anchor_reference": 0.0899,
        "anchor_pass": bool(abs(anchor / 0.0899 - 1) <= 3e-3),
    }
    checks["V1_PASS"] = bool(all(checks["interpolation_pass"].values()) and checks["gamma_pass"] and checks["prandtl_pass"]
                             and checks["Z_low_pressure_pass"] and checks["anchor_pass"] and n_pts >= 50)
    refs = {k: CP.get_fluid_param_string(FLUID, k) for k in ("BibTeX-EOS", "BibTeX-VISCOSITY", "BibTeX-CONDUCTIVITY")}
    meta = {"fluid": FLUID, "aliases": CP.get_fluid_param_string(FLUID, "aliases"),
            "coolprop_version": CoolProp.__version__, "coolprop_gitrevision": CP.get_global_param_string("gitrevision"),
            "references": refs, "python": platform.python_version(),
            "reference_state": "CoolProp default for Hydrogen (h, s offsets are arbitrary; only differences matter)",
            "units": {"T_TLU2": "K", "p_TLU2": "MPa", "rho_TLU2": "kg/m^3", "s_TLU2": "kJ/(kg*K)", "h_TLU2": "kJ/kg",
                      "cp_TLU2": "kJ/(kg*K)", "mu_TLU2": "uPa*s", "k_TLU2": "mW/(m*K)", "beta_TLU2": "MPa",
                      "alpha_TLU2": "1/K"},
            "shape": [len(T_GRID), len(P_GRID_MPA)], "envelope_validated": ENVELOPE}
    data = {"T_TLU2": T_GRID.tolist(), "p_TLU2": P_GRID_MPA.tolist(),
            **{f"{k}_TLU2": tab[k].tolist() for k in ("rho", "s", "h", "cp", "mu", "k", "beta", "alpha")},
            "Z": tab["Z"].tolist(), "R_kJ_per_kgK": R / 1e3,
            "limits": {"T_min_real": float(T_GRID[0]), "T_max_real": float(T_GRID[-1]),
                       "p_min_real": float(P_GRID_MPA[0]), "p_max_real": float(P_GRID_MPA[-1])}}
    lf = {"encoding": "utf-8", "newline": "\n"}   # identical bytes on every platform (hash-recorded)
    (OUT / "H2_REALGAS_TLU2.json").write_text(json.dumps({"meta": meta, "data": data}, indent=1), **lf)
    lines = ["% Normal-hydrogen real-gas parameters for Simscape Gas Properties (G) (H2Net v1, step S1).",
             f"% Generated by tools/simulation/h2net_v1_property_tables.py with CoolProp {CoolProp.__version__}.",
             "% Values are strings for set_param on the Gas Properties (G) block of an H2Net v1 COPY (never the released",
             "% models). The gas-specification value that selects 'real gas' must be confirmed in the R2025a documentation.",
             "H2 = struct();"]
    for k in ("T", "p", "rho", "s", "h", "cp", "mu", "k", "beta", "alpha"):
        lines.append(f"H2.{k}_TLU2 = '{mat(tab[k] if k not in ('T', 'p') else (T_GRID if k == 'T' else P_GRID_MPA))}';")
    lines.append(f"H2.pT_validity_TLU2 = 'ones({len(T_GRID)}, {len(P_GRID_MPA)})';")
    for k, v in data["limits"].items():
        lines.append(f"H2.{k} = '{v:.10g}';")
    (OUT / "H2_REALGAS_TLU2_params.m").write_text("\n".join(lines) + "\n", **lf)
    (OUT / "V1_REPORT.json").write_text(json.dumps({"meta": meta, "checks": checks, "tolerances": TOL}, indent=2), **lf)
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    (OUT / "ENVIRONMENT.txt").write_text(f"python {platform.python_version()}\n{freeze.replace(chr(13), '')}", **lf)
    hashes = "\n".join(f"{hashlib.sha256((OUT / f).read_bytes()).hexdigest()}  {f}" for f in
                       ("H2_REALGAS_TLU2.json", "H2_REALGAS_TLU2_params.m", "V1_REPORT.json", "ENVIRONMENT.txt"))
    (OUT / "OUTPUT_HASHES.sha256").write_text(hashes + "\n", **lf)
    print(json.dumps(checks, indent=2))
    return 0 if checks["V1_PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
