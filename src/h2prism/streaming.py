"""
Streaming inference prototype (action X21; issues F-07, F-08, F-10). RESEARCH MODULE, synthetic replay only.
No industrial claim; no model is trained here.

  DataQualityGate    per-window sensor checks: missing samples, non-finite values, physical range, stuck sensor
                     (zero variance over the window), spikes (|step| above a limit). Any failure makes the window
                     UNRESOLVED with reasons -- a sensor fault is never mapped to a process class.
  CausalWindower     fixed-length windows emitted from a ring buffer using only samples already received
                     (t <= emission time); window length / stride are required arguments (no silent choice).
  replay_benchmark   pushes a synthetic stream through windower -> gate -> scorer and reports per-window latency
                     percentiles and peak traced memory (tracemalloc). Engineering evidence only.
"""

from __future__ import annotations

import time
import tracemalloc
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Tuple

import numpy as np

UNRESOLVED = "UNRESOLVED"
PASS = "PASS"


@dataclass(frozen=True)
class QualityLimits:
    lower: Sequence[float]                 # per channel physical lower bound (e.g. 0 Pa absolute)
    upper: Sequence[float]
    max_step: Sequence[float]              # per channel maximum |x[t] - x[t-1]|
    stuck_range: float = 0.0               # max - min <= this over the window => stuck (exact; a std threshold is
                                           # defeated by rounding at large offsets, e.g. 5 MPa)
    max_missing_fraction: float = 0.0


@dataclass
class DataQualityGate:
    limits: QualityLimits

    def check(self, W: np.ndarray) -> Tuple[str, List[str]]:
        W = np.asarray(W, float)
        lo, hi, st = (np.asarray(a, float) for a in (self.limits.lower, self.limits.upper, self.limits.max_step))
        reasons = []
        miss = np.isnan(W).mean(0)
        for c in np.flatnonzero(miss > self.limits.max_missing_fraction):
            reasons.append(f"ch{c}:missing({miss[c]:.2f})")
        if np.isinf(W).any():
            reasons.append("non_finite")
        F = np.where(np.isfinite(W), W, np.nan)
        with np.errstate(invalid="ignore"):
            for c in range(W.shape[1]):
                col = F[:, c][~np.isnan(F[:, c])]
                if len(col) == 0:
                    continue
                if col.min() < lo[c] or col.max() > hi[c]:
                    reasons.append(f"ch{c}:out_of_range")
                if len(col) > 1 and np.ptp(col) <= self.limits.stuck_range:
                    reasons.append(f"ch{c}:stuck")
                if len(col) > 1 and np.abs(np.diff(col)).max() > st[c]:
                    reasons.append(f"ch{c}:spike")
        return (UNRESOLVED, reasons) if reasons else (PASS, [])


@dataclass
class CausalWindower:
    window_samples: int
    stride_samples: int
    _buf: deque = field(default=None, repr=False)
    _n: int = 0

    def __post_init__(self):
        if self.window_samples < 2 or self.stride_samples < 1:
            raise ValueError("window_samples >= 2 and stride_samples >= 1 are required")
        self._buf = deque(maxlen=self.window_samples)

    def push(self, t: float, x: Sequence[float]) -> Optional[Tuple[float, np.ndarray]]:
        """Add one sample; return (emission time, window) when a window completes, built only from received samples."""
        self._buf.append((float(t), np.asarray(x, float)))
        self._n += 1
        if self._n >= self.window_samples and (self._n - self.window_samples) % self.stride_samples == 0:
            return float(t), np.vstack([s for _, s in self._buf])
        return None


def replay_benchmark(stream: np.ndarray, t: np.ndarray, windower: CausalWindower, gate: DataQualityGate,
                     scorer: Callable[[np.ndarray], object]) -> Dict[str, object]:
    lat, statuses = [], []
    tracemalloc.start()
    for ti, xi in zip(t, stream):
        t0 = time.perf_counter()
        out = windower.push(ti, xi)
        if out is not None:
            status, _ = gate.check(out[1])
            if status == PASS:
                scorer(out[1])
            statuses.append(status)
            lat.append(time.perf_counter() - t0)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    lat = np.array(lat) * 1e3
    return {"evidence": "ENGINEERING_EVIDENCE_SYNTHETIC_REPLAY", "n_samples": int(len(t)), "n_windows": int(len(lat)),
            "n_unresolved": int(sum(s == UNRESOLVED for s in statuses)),
            "latency_ms_p50": float(np.percentile(lat, 50)) if len(lat) else float("nan"),
            "latency_ms_p99": float(np.percentile(lat, 99)) if len(lat) else float("nan"),
            "latency_ms_max": float(lat.max()) if len(lat) else float("nan"),
            "peak_traced_memory_kB": float(peak / 1024)}
