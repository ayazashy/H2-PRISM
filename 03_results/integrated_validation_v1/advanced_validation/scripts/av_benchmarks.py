"""Measured computational performance of the implemented algorithms (no diagnostic claims).

B1 formal D(Y) decision latency on the real Center captures, varying ONE dimension at a time
   (others fixed at query SID213, scenario S4, restricted universe, 13 channels, 151 samples, +/-1 s):
   M channels {1..13}; H hypotheses {1..6}; T window samples {31, 61, 91, 121, 151}; S shifts {1, 11, 21, 51, 101}.
   The window-length sweep shortens the frozen 151-sample focal window for timing purposes only.
B2 empirical D(x) (EmpiricalSupport.compute) on SYNTHETIC Gaussian arrays (128 features, 4 classes): numerical
   performance only, never a diagnostic result. Reference size N_ref {1k, 2k, 5k, 10k, 20k} at k = 25 and
   k {10, 25, 50} at N_ref = 10k; 500 queries.
Method: time.perf_counter, 2 warm-up + 15 timed repetitions (B1) / 5 (B2); tracemalloc peak in a separate pass;
single process; thread-count environment variables recorded as found.
Usage: python av_benchmarks.py --workspace <Center workspace>
"""
from __future__ import annotations

import argparse
import os
import platform
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

AV = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from h2prism import center_enhancement as ce  # noqa: E402
from h2prism.certified_evidence import diagnose  # noqa: E402
from h2prism.distinguishability import DConfig, EmpiricalSupport  # noqa: E402

import av_dy_experiments as ax  # noqa: E402


def hardware():
    import psutil
    info = {"platform": platform.platform(), "processor": platform.processor(), "machine": platform.machine(),
            "logical_cpus": psutil.cpu_count(logical=True), "physical_cpus": psutil.cpu_count(logical=False),
            "ram_GB": round(psutil.virtual_memory().total / 2 ** 30, 1), "python": platform.python_version(),
            "numpy": np.__version__, "pandas": pd.__version__}
    for v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
        info[v] = os.environ.get(v, "unset")
    try:
        import subprocess
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
                             capture_output=True, text=True, timeout=30).stdout.strip()
        info["cpu_model"] = out
    except Exception:
        info["cpu_model"] = "unavailable"
    return info


def timed(fn, warm=2, rep=15):
    for _ in range(warm):
        fn()
    ts = []
    for _ in range(rep):
        t = time.perf_counter()
        fn()
        ts.append(time.perf_counter() - t)
    tracemalloc.start()
    fn()
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    ts = np.array(ts)
    return dict(median_s=np.median(ts), p95_s=np.quantile(ts, 0.95), min_s=ts.min(), max_s=ts.max(), reps=len(ts),
                peak_tracemalloc_MB=peak / 2 ** 20)


def dy_call(d, idx, bound, n_models=None):
    eps = {"pressure": 1e-3, "mass_flow": 1e-2}
    eo = {k: v * 0.5 for k, v in eps.items()}
    em = dict(eo)
    meas = ax.measurement(d, "SID213", idx, eo, 0)
    models = ce.dy_models(d, "SID213", idx, em, bound, "restricted")
    if n_models:
        models = models[:n_models]
    return lambda: diagnose(meas, models)


def b1(d):
    rows = []
    allidx = np.arange(13)
    for m in range(1, 14):
        rows.append(dict(dimension="M_channels", value=m, **timed(dy_call(d, allidx[:m], 1.0))))
    for h in range(1, 7):
        rows.append(dict(dimension="H_hypotheses", value=h, **timed(dy_call(d, allidx, 1.0, h))))
    for s_bound in (0.0, 1.0, 2.0, 5.0, 10.0):
        rows.append(dict(dimension="S_shifts", value=int(round(s_bound / ce.STEP_S)) * 2 + 1,
                         **timed(dy_call(d, allidx, s_bound))))
    n0 = ce.N
    try:
        for n in (31, 61, 91, 121, 151):
            ce.N = n
            rows.append(dict(dimension="T_window_samples", value=n, **timed(dy_call(d, allidx, 1.0))))
    finally:
        ce.N = n0
    return pd.DataFrame(rows).assign(component="formal D(Y) decision (diagnose, 6 restricted hypotheses unless varied)",
                                     data="real Center captures (timing only)")


def b2():
    rng = np.random.default_rng(20261118)
    rows = []

    def run(nref, k):
        X = rng.normal(size=(nref, 128))
        y = rng.integers(0, 4, nref)
        fam = rng.integers(0, 30, nref)
        scen = rng.integers(0, 60, nref)
        es = EmpiricalSupport(DConfig(k=k)).fit(X, [str(v) for v in y], fam, scen, ["0", "1", "2", "3"])
        Xq = rng.normal(size=(500, 128))
        qf = rng.integers(30, 40, 500)
        return lambda: es.compute(Xq, qf)

    for nref in (1000, 2000, 5000, 10000, 20000):
        r = timed(run(nref, 25), warm=1, rep=5)
        rows.append(dict(dimension="N_reference_windows", value=nref, per_query_s=r["median_s"] / 500, **r))
    for k in (10, 25, 50):
        r = timed(run(10000, k), warm=1, rep=5)
        rows.append(dict(dimension="K_neighbours", value=k, per_query_s=r["median_s"] / 500, **r))
    return pd.DataFrame(rows).assign(component="empirical D(x) compute, 500 queries",
                                     data="SYNTHETIC Gaussian arrays (numerical benchmark only)")


def slope(df, col="median_s"):
    out = []
    for dim, g in df.groupby("dimension"):
        x, y = np.log(g.value.astype(float)), np.log(g[col])
        b = np.polyfit(x, y, 1)[0] if len(g) > 2 else np.nan
        out.append(dict(dimension=dim, points=len(g), range=f"{g.value.min()}–{g.value.max()}",
                        loglog_slope=b, ratio_max_over_min=g[col].iloc[-1] / g[col].iloc[0]))
    return pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", default=os.environ.get("H2PRISM_CENTER_WORKSPACE"))
    a = ap.parse_args()
    out = AV / "benchmarks"
    out.mkdir(parents=True, exist_ok=True)
    hw = hardware()
    pd.Series(hw).to_csv(out / "hardware.csv", header=["value"], lineterminator="\n")
    d = ce.load(Path(a.workspace))
    t = time.perf_counter()
    ce.load(Path(a.workspace))
    load_s = time.perf_counter() - t
    B1 = b1(d)
    B1.to_csv(out / "dy_scaling.csv", index=False, lineterminator="\n")
    B2 = b2()
    B2.to_csv(out / "dx_scaling.csv", index=False, lineterminator="\n")
    s = pd.concat([slope(B1).assign(component="D(Y)"), slope(B2).assign(component="D(x)")])
    s.to_csv(out / "scaling_fits.csv", index=False, lineterminator="\n")
    pd.DataFrame([dict(item="Center capture load + hash verification (setup, one-off)", seconds=load_s)]).to_csv(
        out / "setup_costs.csv", index=False, lineterminator="\n")
    print(B1.groupby("dimension").median_s.agg(["min", "max"]))
    print(s)


if __name__ == "__main__":
    main()
