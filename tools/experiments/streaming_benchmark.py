#!/usr/bin/env python3
"""
X21 / scalability: synthetic replay benchmark of the streaming prototype (src/h2prism/streaming.py).
ENGINEERING EVIDENCE ONLY (synthetic random-walk signals, a fixed untrained linear scorer on mean/std/slope features);
not a performance claim for any real network. Scales the channel count 16 -> 64 -> 256 (network-size proxy).
Output: 03_results/diagnostics/streaming/STREAMING_BENCHMARK.json
"""
import json
import platform
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.streaming import CausalWindower, DataQualityGate, QualityLimits, replay_benchmark  # noqa: E402

FS_HZ, DURATION_S, WIN_S, STRIDE_S = 10.0, 3600.0, 60.0, 30.0


def run(C, seed=0):
    rng = np.random.default_rng(seed)
    n = int(FS_HZ * DURATION_S)
    t = np.arange(n) / FS_HZ
    X = 5e6 + np.cumsum(rng.normal(0, 1e2, (n, C)), 0)
    X[n // 2:n // 2 + 900, 0] = X[n // 2, 0]                        # injected stuck channel (90 s)
    W = rng.normal(size=(3 * C, 4))                                  # fixed, untrained scorer
    tt = np.arange(int(WIN_S * FS_HZ)) / FS_HZ
    tt = (tt - tt.mean()) / (tt ** 2).sum() ** 0.5

    def scorer(win):
        f = np.concatenate([win.mean(0), win.std(0), tt @ (win - win.mean(0))])
        return (f / 1e6) @ W

    lim = QualityLimits(lower=[0.0] * C, upper=[20e6] * C, max_step=[5e4] * C)
    r = replay_benchmark(X, t, CausalWindower(int(WIN_S * FS_HZ), int(STRIDE_S * FS_HZ)), DataQualityGate(lim), scorer)
    r.update(channels=C, sampling_hz=FS_HZ, duration_s=DURATION_S, window_s=WIN_S, stride_s=STRIDE_S,
             realtime_budget_ms_per_window=STRIDE_S * 1e3)
    return r


if __name__ == "__main__":
    out = {"status": "ENGINEERING_EVIDENCE_SYNTHETIC_REPLAY", "python": platform.python_version(),
           "machine": platform.machine(), "runs": [run(C) for C in (16, 64, 256)]}
    p = REPO / "03_results" / "diagnostics" / "streaming" / "STREAMING_BENCHMARK.json"
    p.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in out["runs"]:
        print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in
               ("channels", "n_windows", "n_unresolved", "latency_ms_p50", "latency_ms_p99", "latency_ms_max", "peak_traced_memory_kB")})
