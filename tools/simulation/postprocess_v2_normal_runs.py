#!/usr/bin/env python3
"""
Post-processing for SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION (package v3). Run after
generate_v2_normal_support(..., 'run') and before validate_v2_normal_outputs.py.

1. Resample the clean solver-grid output (fixed step 0.8 s centre, 0.9 s down/up) onto the RELEASE grid,
   t = 0, 1, ..., 19999 s (20,000 rows), by linear interpolation per channel. The released files use this grid; the
   authors' resampling method is undocumented, so this method is stated explicitly and recorded in the provenance.
2. Add Gaussian white measurement noise on that grid with the per-run seed from DESIGN.csv and the per-channel sigma
   measured in the released noise_added data (pressure 0.0005 MPa, flow 0.25 kg/s; white). A seed is not a scenario.
Writes <run>_clean.csv and <run>_noise_added.csv and records method, sigma, seed and hashes in the provenance.
Confirmation runs are processed mechanically (needed to generate them); nothing is summarised, printed or plotted.
Refuses to run if any <run>_FAILED.json exists or any expected run is missing.
Usage: python tools/simulation/postprocess_v2_normal_runs.py <outDir> [--design DESIGN.csv]
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
DESIGN = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support" / "DESIGN.csv"
SIGMA = {"PS": 0.0005, "MFS": 0.25}
GRID = np.arange(20000, dtype=float)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sigma_for(col: str) -> float:
    for k in ("MFS", "PS"):
        if col.startswith(k):
            return SIGMA[k]
    raise ValueError(f"unknown channel {col}")


def resample(raw: pd.DataFrame) -> pd.DataFrame:
    t = raw.Timestamp.to_numpy(float)
    if not (np.diff(t) > 0).all():
        raise ValueError("solver time grid is not strictly increasing")
    if t[0] > GRID[0] or t[-1] < GRID[-1]:
        raise ValueError("solver output does not cover 0..19999 s")
    out = {"Timestamp": GRID}
    for c in raw.columns:
        if c != "Timestamp":
            out[c] = np.interp(GRID, t, raw[c].to_numpy(float))
    return pd.DataFrame(out)


def add_noise(clean: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = clean.copy()
    for c in clean.columns:
        if c != "Timestamp":
            out[c] = clean[c].to_numpy(float) + rng.normal(0.0, sigma_for(c), len(clean))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--design", type=Path, default=DESIGN)
    a = ap.parse_args(argv)
    from v2_normal_authorization import require_claimed
    require_claimed(a.out_dir)           # fail closed: only the claimed attempt's folder, unchanged bound files
    failed = sorted(a.out_dir.rglob("*_FAILED.json"))
    if failed:
        raise SystemExit(f"failed runs present ({len(failed)}); follow the failure procedure, do not post-process")
    D = pd.read_csv(a.design)
    for r in D.itertuples():
        base = a.out_dir / r.partition / f"{r.scenario_id}_{r.model}"
        raw_p, prov_p = Path(f"{base}_clean_solver_grid.csv"), Path(f"{base}_provenance.json")
        if not raw_p.exists() or not prov_p.exists():
            raise SystemExit(f"missing run {base.name}; do not post-process a partial set")
        prov = json.loads(prov_p.read_text(encoding="utf-8"))
        if prov.get("clean_solver_grid_csv_sha256") != _sha(raw_p):
            raise SystemExit(f"solver-grid file changed after generation: {raw_p.name}")
        clean = resample(pd.read_csv(raw_p))
        clean_p, noisy_p = Path(f"{base}_clean.csv"), Path(f"{base}_noise_added.csv")
        clean.to_csv(clean_p, index=False, lineterminator="\n", float_format="%.10g")
        add_noise(clean, int(r.noise_seed)).to_csv(noisy_p, index=False, lineterminator="\n", float_format="%.10g")
        prov.update({"resampling": {"method": "linear_interpolation", "grid_s": [0, 19999, 1],
                                    "tool": "tools/simulation/postprocess_v2_normal_runs.py"},
                     "noise": {"type": "gaussian_white", "sigma_pressure_MPa": SIGMA["PS"], "sigma_flow_kg_s": SIGMA["MFS"],
                               "seed": int(r.noise_seed)},
                     "clean_csv_sha256": _sha(clean_p), "noise_added_csv_sha256": _sha(noisy_p)})
        prov_p.write_text(json.dumps(prov, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
