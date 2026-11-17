"""
H2-PRISM family-level uncertainty for paired method comparisons (F-D13; F11 support).

STATUS: IMPLEMENTED + TESTED (synthetic). Resamples independence units (families), never
windows, WITHIN strata (held-out topologies), keeping the number of units per stratum fixed,
and recomputes a pooled ratio metric (e.g. selective risk = errors / accepted) for two methods
on the SAME resampled units (paired). The interval is conditional on the observed strata:
with 3 topologies it says nothing about unseen topologies. Strata with a single unit cannot
be resampled and are held fixed (reported as a warning).
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

REQUIRED = ("unit", "stratum", "num_a", "den_a", "num_b", "den_b")


def _ratio(num, den):
    d = float(np.sum(den))
    return float(np.sum(num)) / d if d > 0 else float("nan")


def paired_stratified_bootstrap(units: pd.DataFrame, n_boot: int, seed: int, ci: float = 0.95) -> Dict[str, object]:
    miss = [c for c in REQUIRED if c not in units.columns]
    if miss:
        raise KeyError(f"missing columns: {miss}")
    if units["unit"].duplicated().any():
        raise ValueError("one row per independence unit is required (aggregate windows first)")
    u = units.sort_values(["stratum", "unit"], kind="mergesort").reset_index(drop=True)
    est_a, est_b = _ratio(u.num_a, u.den_a), _ratio(u.num_b, u.den_b)
    rng = np.random.default_rng(seed)
    groups = [np.flatnonzero(u.stratum.to_numpy() == s) for s in sorted(u.stratum.unique(), key=str)]
    warns: List[str] = [f"stratum {u.stratum.iloc[g[0]]!r} has 1 unit: held fixed" for g in groups if len(g) < 2]
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.concatenate([rng.choice(g, size=len(g), replace=True) if len(g) > 1 else g for g in groups])
        diffs[b] = _ratio(u.num_a.to_numpy()[idx], u.den_a.to_numpy()[idx]) - _ratio(u.num_b.to_numpy()[idx], u.den_b.to_numpy()[idx])
    valid = diffs[np.isfinite(diffs)]
    lo, hi = (np.quantile(valid, [(1 - ci) / 2, 1 - (1 - ci) / 2]) if valid.size else (np.nan, np.nan))
    return {"estimate_a": est_a, "estimate_b": est_b, "difference": est_a - est_b,
            "ci_low": float(lo), "ci_high": float(hi), "ci_level": ci, "n_boot": n_boot,
            "n_boot_undefined": int(n_boot - valid.size), "n_units": len(u),
            "units_per_stratum": u.groupby("stratum").size().to_dict(), "seed": seed,
            "interpretation": "conditional on the observed strata; not a generalisation interval",
            "warnings": warns}


def per_stratum_estimates(units: pd.DataFrame) -> pd.DataFrame:
    """Descriptive per-stratum (per held-out topology) ratios and differences; no inference."""
    rows = []
    for s, d in units.groupby("stratum", sort=True):
        a, b = _ratio(d.num_a, d.den_a), _ratio(d.num_b, d.den_b)
        rows.append({"stratum": s, "n_units": len(d), "estimate_a": a, "estimate_b": b, "difference": a - b})
    return pd.DataFrame(rows)
