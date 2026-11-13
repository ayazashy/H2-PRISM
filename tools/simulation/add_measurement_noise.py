#!/usr/bin/env python3
"""
Noise step for SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION.

Adds Gaussian white measurement noise to each *_clean.csv written by generate_v2_normal_support.m, with the per-run
seed from DESIGN.csv and per-channel sigma equal to what the RELEASED noise_added data actually contain
(03_results/diagnostics/feature_representation/NOISE_AUTOCORRELATION.csv: pressure 0.0005 MPa, flow 0.25 kg/s,
white). This reproduces the released noise procedure as measured; the README's "1-2% of range" is not what the data
show and is not used. A new seed is NOT a new scenario.
Writes <run>_noise_added.csv next to the clean file and records sigma, seed and both hashes in the provenance JSON.
Usage: python tools/simulation/add_measurement_noise.py <outDir> [--design DESIGN.csv]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DESIGN = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support" / "DESIGN.csv"
SIGMA = {"PS": 0.0005, "MFS": 0.25}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sigma_for(col: str) -> float:
    for k in ("MFS", "PS"):
        if col.startswith(k):
            return SIGMA[k]
    raise ValueError(f"unknown channel {col}")


def add_noise(clean: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = clean.copy()
    for c in clean.columns:
        if c == "Timestamp":
            continue
        out[c] = clean[c].to_numpy(float) + rng.normal(0.0, sigma_for(c), len(clean))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--design", type=Path, default=DESIGN)
    a = ap.parse_args(argv)
    D = pd.read_csv(a.design)
    for r in D.itertuples():
        base = a.out_dir / r.partition / f"{r.scenario_id}_{r.model}"
        clean_p, prov_p = Path(f"{base}_clean.csv"), Path(f"{base}_provenance.json")
        prov = json.loads(prov_p.read_text(encoding="utf-8"))
        if prov.get("clean_csv_sha256") != _sha(clean_p):
            raise SystemExit(f"clean file changed after generation: {clean_p.name}")
        noisy = add_noise(pd.read_csv(clean_p), int(r.noise_seed))
        noisy_p = Path(f"{base}_noise_added.csv")
        noisy.to_csv(noisy_p, index=False, lineterminator="\n", float_format="%.10g")
        prov.update({"noise": {"type": "gaussian_white", "sigma_pressure_MPa": SIGMA["PS"], "sigma_flow_kg_s": SIGMA["MFS"],
                               "seed": int(r.noise_seed), "tool": "tools/simulation/add_measurement_noise.py"},
                     "noise_added_csv_sha256": _sha(noisy_p)})
        prov_p.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
