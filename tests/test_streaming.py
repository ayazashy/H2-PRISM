"""X21: causal windowing, data-quality gate (sensor faults -> UNRESOLVED), synthetic replay benchmark."""

import numpy as np
import pytest

from h2prism.streaming import PASS, UNRESOLVED, CausalWindower, DataQualityGate, QualityLimits, replay_benchmark

C = 4
LIM = QualityLimits(lower=[0.0] * C, upper=[10e6] * C, max_step=[2e5] * C)


def _stream(n=600, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(n) * 0.1
    X = 5e6 + np.cumsum(rng.normal(0, 1e3, (n, C)), 0)
    return t, X


def test_windows_are_causal_and_regular():
    t, X = _stream()
    w = CausalWindower(50, 25)
    got = [(i, w.push(t[i], X[i])) for i in range(len(t))]
    em = [(i, o) for i, o in got if o is not None]
    assert [i for i, _ in em][:3] == [49, 74, 99]
    for i, (te, W) in em:
        assert te == t[i] and np.array_equal(W, X[i - 49:i + 1])     # only samples up to the emission time


def test_future_samples_never_change_emitted_windows():
    t, X = _stream()
    Y = X.copy(); Y[300:] += 1e6
    a, b = CausalWindower(50, 25), CausalWindower(50, 25)
    for i in range(300):
        oa, ob = a.push(t[i], X[i]), b.push(t[i], Y[i])
        assert (oa is None) == (ob is None) and (oa is None or np.array_equal(oa[1], ob[1]))


@pytest.mark.parametrize("fault,reason", [("nan", "missing"), ("stuck", "stuck"), ("spike", "spike"),
                                          ("range", "out_of_range"), ("inf", "non_finite")])
def test_sensor_faults_are_unresolved_not_a_class(fault, reason):
    _, X = _stream()
    W = X[:50].copy()
    if fault == "nan": W[10, 1] = np.nan
    if fault == "stuck": W[:, 2] = 5_000_123.456789          # large offset: std of a constant is not exactly 0
    if fault == "spike": W[20, 0] += 1e6
    if fault == "range": W[5, 3] = -1.0
    if fault == "inf": W[7, 0] = np.inf
    status, reasons = DataQualityGate(LIM).check(W)
    assert status == UNRESOLVED and any(reason in r for r in reasons)
    assert DataQualityGate(LIM).check(X[:50])[0] == PASS


def test_replay_benchmark_reports_latency_memory_and_unresolved_windows():
    t, X = _stream(2000)
    X[1000:1100, 2] = 4e6                                        # injected stuck sensor
    calls = []
    r = replay_benchmark(X, t, CausalWindower(50, 25), DataQualityGate(LIM), lambda W: calls.append(1))
    assert r["evidence"].startswith("ENGINEERING_EVIDENCE") and r["n_windows"] == (2000 - 50) // 25 + 1
    assert r["n_unresolved"] >= 2 and len(calls) == r["n_windows"] - r["n_unresolved"]
    assert r["latency_ms_p99"] > 0 and r["peak_traced_memory_kB"] > 0
