#!/usr/bin/env python3
"""
X03 support / X06 tooling (H2Net v1): steady isothermal screening of the PROPOSED operating envelope on the RELEASED
pipe geometry with the hash-verified normal-hydrogen tables. ENGINEERING EVIDENCE for the owner decision in
PARAMETER_DECISIONS.yaml; it decides nothing and is not a V2 reference target (X06 needs decided operating points).

Inputs (all labelled): released pipe lengths / hydraulic diameters (traced from the .slx files by
tools/dataset/trace_slx_sensors.py), PROPOSED roughness 0.045 mm (S6), PROPOSED pressures 2-8 MPa and velocity <= 20 m/s
(operating_envelope_V8), PROPOSED temperatures 283.15 K (soil, S2) and 313.15 K (aftercooler, S3).
Per pipe and state: mass flow at a given inlet velocity, outlet pressure, outlet velocity, max Mach (gamma 1.4
approximation inside gas_physics for tabulated gases; H2 gamma ~1.40-1.41 in range) and envelope flags.

  python tools/simulation/h2net_v1_envelope_screening.py            -> candidate/ENVELOPE_SCREENING.csv
  python tools/simulation/h2net_v1_envelope_screening.py --targets  -> refuses unless PARAMETER_DECISIONS is decided
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from h2prism.gas_physics import Pipe, pipe_outlet_pressure  # noqa: E402
from h2net_v1_reference import load_h2_tables  # noqa: E402

H2 = REPO / "06_audit_preparation" / "simulation" / "h2net_v1"
RELEASED_PIPES = {  # SID: (length m, Dh m) -- released .slx geometry (identical across the six source models)
    47: (16000, 1.2), 48: (30000, 1.2), 49: (11000, 1.2), 106: (8000, 1.0),
    107: (4000, 0.355), 108: (3000, 0.4), 221: (4000, 1.0), 309: (11000, 1.2)}
PROPOSED = {"roughness_m": 0.045e-3, "p_in_MPa": (2.0, 5.0, 8.0), "v_in_m_s": (5.0, 10.0, 20.0),
            "T_K": (283.15, 313.15), "p_range_MPa": (2.0, 8.0), "v_max_m_s": 20.0}


def screen() -> pd.DataFrame:
    gas = load_h2_tables()
    rows = []
    for sid, (L, D) in RELEASED_PIPES.items():
        pipe = Pipe("a", "b", L, D, PROPOSED["roughness_m"])
        for T in PROPOSED["T_K"]:
            for p_in in PROPOSED["p_in_MPa"]:
                for v in PROPOSED["v_in_m_s"]:
                    rho_in = gas.rho(p_in * 1e6, T)
                    mdot = rho_in * pipe.area * v
                    r = {"status": "CANDIDATE_SCREENING", "pipe_sid": sid, "length_m": L, "Dh_m": D, "T_K": T,
                         "p_in_MPa": p_in, "v_in_m_s": v, "mdot_kg_s": mdot}
                    try:
                        p_out, mach = pipe_outlet_pressure(pipe, p_in * 1e6, mdot, T, gas)
                        v_out = mdot / (gas.rho(p_out, T) * pipe.area)
                        r.update(p_out_MPa=p_out / 1e6, dp_kPa=(p_in * 1e6 - p_out) / 1e3, v_out_m_s=v_out, max_mach=mach,
                                 within_pressure_envelope=PROPOSED["p_range_MPa"][0] <= p_out / 1e6 <= PROPOSED["p_range_MPa"][1],
                                 within_velocity_limit=v_out <= PROPOSED["v_max_m_s"], note="")
                    except ValueError as e:
                        r.update(p_out_MPa=float("nan"), dp_kPa=float("nan"), v_out_m_s=float("nan"), max_mach=float("nan"),
                                 within_pressure_envelope=False, within_velocity_limit=False, note=str(e)[:80])
                    rows.append(r)
    return pd.DataFrame(rows)


def main(argv) -> int:
    if "--targets" in argv:                       # X06: delegated; fail-closed on the owner decision record
        import h2net_v1_v2_targets as v2t
        return v2t.main([])
    df = screen()
    out = H2 / "candidate" / "ENVELOPE_SCREENING.csv"
    df.to_csv(out, index=False, float_format="%.6g", lineterminator="\n")
    print(f"{len(df)} rows -> {out.relative_to(REPO).as_posix()}")
    s = df.groupby(["v_in_m_s", "p_in_MPa"])[["within_pressure_envelope", "within_velocity_limit"]].mean()
    print(s.to_string())
    print("max dp kPa per pipe at v_in=20, p_in=2 MPa, T=313.15:")
    print(df[(df.v_in_m_s == 20) & (df.p_in_MPa == 2) & (df.T_K == 313.15)][["pipe_sid", "length_m", "Dh_m", "mdot_kg_s", "dp_kPa", "v_out_m_s", "max_mach"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
