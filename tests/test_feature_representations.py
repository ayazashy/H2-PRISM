"""Invariants of the causal window representations (src/h2prism/feature_representations.py)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from h2prism import feature_representations as fr


def _series(v):
    return pd.Series(np.asarray(v, float), index=np.arange(len(v), dtype=float))


def test_causal_no_future_information():
    """Changing samples AFTER a window's end must not change that window's value (any causal representation)."""
    rng = np.random.default_rng(0)
    x = _series(rng.normal(0, 1, 6000))
    y = x.copy()
    y.iloc[4000:] += 50.0                      # future perturbation
    st = fr.window_starts(x.index)
    early = st + 60 <= 4000
    for f in (fr.absolute_mean, fr.causal_baseline_deviation, fr.causal_robust_change, fr.window_slope):
        a, b = f(x, st), f(y, st)
        assert np.allclose(a[early], b[early], equal_nan=True), f.__name__
        assert not np.allclose(a[~early], b[~early], equal_nan=True), f.__name__   # and later windows do see it


def test_baseline_undefined_until_full_past_baseline():
    """No baseline exists before B seconds of past data: the value is NaN (never zero-filled)."""
    x = _series(np.ones(4000))
    st = fr.window_starts(x.index)
    v = fr.causal_baseline_deviation(x, st, b=1800)
    assert np.isnan(v[st < 1800]).all() and np.isfinite(v[st >= 1800]).all()


def test_baseline_deviation_sees_a_step_and_then_absorbs_it():
    """A persistent step is visible after onset and is absorbed once the baseline lies entirely after the step: this is
    why change features reveal onsets but not persistent states (DISTINGUISHABILITY_V2.md section 3)."""
    v = np.zeros(8000)
    v[3000:] = 1.0
    x = _series(v)
    st = fr.window_starts(x.index)
    d = fr.causal_baseline_deviation(x, st, b=1800)
    assert d[st == 3000][0] == pytest.approx(1.0)
    assert d[st == 3000 + 1800][0] == pytest.approx(0.0)


def test_robust_change_scales_by_baseline_noise():
    rng = np.random.default_rng(1)
    v = rng.normal(0, 2.0, 6000)
    v[4000:] += 20.0
    c = fr.causal_robust_change(_series(v), fr.window_starts(pd.Index(np.arange(6000.0))))
    st = fr.window_starts(pd.Index(np.arange(6000.0)))
    assert c[st == 4020][0] == pytest.approx(10.0, rel=0.25)     # step / sigma = 20 / 2


def test_spatial_difference_requires_simultaneous_samples():
    a = _series(np.arange(200.0))
    b = pd.Series(np.arange(200.0), index=np.arange(200.0) + 0.5)
    with pytest.raises(ValueError):
        fr.spatial_difference(a, b, fr.window_starts(a.index))
    assert np.allclose(fr.spatial_difference(a, a * 0 + 1, fr.window_starts(a.index)),
                       fr.absolute_mean(a - 1, fr.window_starts(a.index)))


def test_window_slope_matches_least_squares():
    t = np.arange(600.0)
    x = pd.Series(3.0 + 0.25 * t, index=t)
    assert np.allclose(fr.window_slope(x, fr.window_starts(x.index)), 0.25)


def test_rejects_unsorted_time():
    x = pd.Series([1.0, 2.0, 3.0], index=[0.0, 2.0, 1.0])
    with pytest.raises(ValueError):
        fr.absolute_mean(x, [0.0])
