#!/usr/bin/env python3
"""
Fixed design for SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION (H-R1, 02_methodology/DISTINGUISHABILITY_V2.md).

Factors (released Normal_HNetwork_gest_*.slx, identical block SIDs in all three models):
  F1 compressor lift    PS Step (SID 59) final_value -> Pressure Source (G)3 pressure-rise set-point after 25 s
                                                           levels 6.1 / 6.4 / 6.7 MPa   (released: 6.4)
  F2 let-down ramp      PS Ramp (SID 241) slope -> Pressure Source (G)1 differential (initial -0.3 MPa)
                                                           levels 0 / -1e-5 / -2e-5 MPa/s (released: -1e-5)
  F3 withdrawal load    restrictions G3-G6 (SIDs 213, 222, 312, 215) restriction_area, jointly
                                                           levels 0.75e-3 / 1.0e-3 / 1.25e-3 m^2 (released: 1e-3)
Design: the 3^(3-1) fraction {(a, b, c): c = (a + b) mod 3} (9 points, each level of each factor three times). It does
not contain the released NORMAL ancestor (1, 1, 1). Partition, fixed before any simulation and without labels:
confirmation = the three points with (a - b) mod 3 == 0 (each level of each factor exactly once); development = the
other six (each level twice). Every point is simulated in all three models; one point = one new independence group
(replicas across models share it). Noise seeds are derived, not independent scenarios.
Writes 06_audit_preparation/simulation/v2_normal_support/DESIGN.csv and DESIGN.sha256.
Usage: python tools/simulation/build_v2_normal_design.py
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support"
F1 = [6.1, 6.4, 6.7]
F2 = [0.0, -1e-5, -2e-5]
F3 = [0.75e-3, 1.0e-3, 1.25e-3]
RELEASED = (1, 1, 1)
MODELS = {"center": "Normal_HNetwork_gest_center", "down": "Normal_HNetwork_gest_down", "up": "Normal_HNetwork_gest_up"}
STEP = {"center": 0.8, "down": 0.9, "up": 0.9}   # fixed steps of the released models_launcher.m


def seed(sid: str, model: str) -> int:
    return int(hashlib.sha256(f"h2prism-v2n|{sid}|{model}".encode()).hexdigest()[:8], 16)


def design() -> pd.DataFrame:
    rows = []
    for a in range(3):
        for b in range(3):
            c = (a + b) % 3
            if (a, b, c) == RELEASED:
                raise SystemExit("design would reproduce the released NORMAL ancestor")
            sid = f"V2N_A{a}B{b}C{c}"
            part = "confirmation" if (a - b) % 3 == 0 else "development"
            for model, name in MODELS.items():
                rows.append({"scenario_id": sid, "independence_group": f"IG_{sid}", "partition": part, "model": model,
                             "model_name": name, "fixed_step_s": STEP[model],
                             "ps_step_final_value_MPa": F1[a], "ps_ramp_slope_MPa_per_s": F2[b],
                             "withdrawal_restriction_area_m2": F3[c],
                             "level_codes": f"{a}{b}{c}", "noise_seed": seed(sid, model)})
    return pd.DataFrame(rows)


def main() -> int:
    D = design()
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "DESIGN.csv"
    D.to_csv(p, index=False, lineterminator="\n", float_format="%.10g")
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT / "DESIGN.sha256").write_text(f"{h}  DESIGN.csv\n", encoding="utf-8")
    print(D.drop_duplicates("scenario_id")[["scenario_id", "partition", "ps_step_final_value_MPa",
                                            "ps_ramp_slope_MPa_per_s", "withdrawal_restriction_area_m2"]].to_string(index=False))
    print(h)
    return 0


if __name__ == "__main__":
    sys.exit(main())
