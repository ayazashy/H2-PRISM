#!/usr/bin/env python3
"""
MODEL_DEVELOPMENT:H2NET_V1: load the generated normal-hydrogen tables (properties/H2_REALGAS_TLU2.json, Simscape units)
into the independent reference (src/h2prism/gas_physics.py, SI units) so that V2 steady-state targets can be computed
for the H2Net v1 operating points once its engineering parameters (PARAMETER_DECISIONS.yaml) are decided.
Pure conversion; no new physics. Usage (from Python): load_h2_tables() -> gas_physics.TabulatedGas
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from h2prism.gas_physics import TabulatedGas  # noqa: E402

TABLES = REPO / "06_audit_preparation" / "simulation" / "h2net_v1" / "properties" / "H2_REALGAS_TLU2.json"
HASHES = TABLES.parent / "OUTPUT_HASHES.sha256"


def load_h2_tables(path: Path = TABLES, verify: bool = True) -> TabulatedGas:
    if verify:
        pinned = {name: h for h, name in (l.split() for l in HASHES.read_text(encoding="utf-8").splitlines() if l.strip())}
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != pinned.get(Path(path).name):
            raise ValueError("hydrogen property tables differ from their recorded hash")
    j = json.loads(Path(path).read_text(encoding="utf-8"))
    d = j["data"]
    return TabulatedGas(R=d["R_kJ_per_kgK"] * 1e3, T=np.array(d["T_TLU2"]), p=np.array(d["p_TLU2"]) * 1e6,
                        Z=np.array(d["Z"]), cp=np.array(d["cp_TLU2"]) * 1e3, mu=np.array(d["mu_TLU2"]) * 1e-6,
                        k=np.array(d["k_TLU2"]) * 1e-3,
                        source=f"CoolProp {j['meta']['coolprop_version']} {j['meta']['references']}",
                        name="normal_hydrogen_H2Net_v1")
