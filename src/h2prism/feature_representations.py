"""
Physically motivated window representations (RESEARCH MODULE; not used by any registered run or RC1).

All functions act on one run's 1 Hz series (index = seconds) and are CAUSAL: the value for a window ending at t uses
samples at or before t only. None of them uses labels, scenario identifiers or another run (no matching NORMAL run is
assumed to exist at inference time). Spatial differences are formed only between position-matched sensors at the two
ends of the same pipe (diagram registry, PIPE_SENSOR_PAIRS.csv). Absolute measurements stay available; these are
additional representations, not replacements.

  absolute_mean(x)              mean of the window (60 s)
  spatial_difference(xa, xb)    mean over the window of xa - xb (pressure drop along a pipe; ~ friction x flow^2)
  causal_baseline_deviation(x)  window mean minus the median of the preceding baseline period [t0 - B, t0)
  causal_robust_change(x)       the same deviation divided by 1.4826 x MAD of the baseline period (+ floor);
                                undefined (NaN) until a full baseline period exists
  window_slope(x)               least-squares slope over the window
Baseline length B and window W are fixed parameters, not tuned on outcomes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

W_DEFAULT = 60
STRIDE_DEFAULT = 30
B_DEFAULT = 1800


def window_starts(index: pd.Index, w: int = W_DEFAULT, stride: int = STRIDE_DEFAULT, start: float = 0.0) -> np.ndarray:
    t0, t1 = max(float(index.min()), start), float(index.max())
    return np.arange(t0, t1 - w + 2, stride)


def _arrays(x: pd.Series):
    t = x.index.to_numpy(float)
    if np.any(np.diff(t) <= 0):
        raise ValueError("series index must be strictly increasing time in seconds")
    return t, x.to_numpy(float)


def _seg(x, a: float, b: float) -> np.ndarray:
    """Samples with a <= t < b. x is a pd.Series or a pre-split (t, v) tuple."""
    t, v = x if isinstance(x, tuple) else _arrays(x)
    return v[np.searchsorted(t, a, "left"):np.searchsorted(t, b, "left")]


def absolute_mean(x: pd.Series, starts, w: int = W_DEFAULT) -> np.ndarray:
    xa = _arrays(x)
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        seg = _seg(xa, s, s + w)
        if len(seg):
            out[i] = seg.mean()
    return out


def spatial_difference(xa: pd.Series, xb: pd.Series, starts, w: int = W_DEFAULT) -> np.ndarray:
    if not xa.index.equals(xb.index):
        raise ValueError("spatial difference needs simultaneous samples of both sensors")
    return absolute_mean(xa - xb, starts, w)


def causal_baseline_deviation(x: pd.Series, starts, w: int = W_DEFAULT, b: int = B_DEFAULT) -> np.ndarray:
    x = _arrays(x)
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        base = _seg(x, s - b, s)
        if len(base) < b:          # no full past baseline yet: undefined, never zero-filled
            continue
        win = _seg(x, s, s + w)
        if len(win):
            out[i] = win.mean() - np.median(base)
    return out


def causal_robust_change(x: pd.Series, starts, w: int = W_DEFAULT, b: int = B_DEFAULT, floor: float = 1e-12) -> np.ndarray:
    x = _arrays(x)
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        base = _seg(x, s - b, s)
        if len(base) < b:
            continue
        win = _seg(x, s, s + w)
        if len(win):
            med = np.median(base)
            out[i] = (win.mean() - med) / max(1.4826 * np.median(np.abs(base - med)), floor)
    return out


def window_slope(x: pd.Series, starts, w: int = W_DEFAULT) -> np.ndarray:
    t, v = _arrays(x)
    out = np.full(len(starts), np.nan)
    for i, s in enumerate(starts):
        a, b = np.searchsorted(t, s, "left"), np.searchsorted(t, s + w, "left")
        if b - a >= 2:
            tt = t[a:b] - t[a:b].mean()
            out[i] = float((tt * (v[a:b] - v[a:b].mean())).sum() / (tt ** 2).sum())
    return out
