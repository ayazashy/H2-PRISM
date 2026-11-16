import numpy as np
import pytest

from h2prism.phase12_acceptance import normal_area, same, trace


def test_plain_capture_tree_comparison_detects_nested_changes():
    a = {"log": [{"value": np.array([1., 2.])}]}
    assert same(a, {"log": [{"value": np.array([1., 2.])}]})
    assert not same(a, {"log": [{"value": np.array([1., 3.])}]})
    assert not same(a, {"extra": 0, **a})


def test_normal_requires_the_constant_area_command():
    normal_area(np.array([0.001, 0.001]))
    with pytest.raises(ValueError, match="area changed"):
        normal_area(np.array([0.001, 0.0011]))


@pytest.mark.parametrize("signal", [
    {"time": [0., 0.2], "unit": "K", "values": [1., 2.]},
    {"time": [0., 0.2], "unit": "MPa", "values": [1., np.inf]},
    {"time": [0., 0.4], "unit": "MPa", "values": [1., 2.]},
])
def test_trace_rejects_wrong_unit_value_or_clock(signal):
    with pytest.raises(ValueError):
        trace(signal, np.array([0., 0.2]), "MPa", "PS1")
