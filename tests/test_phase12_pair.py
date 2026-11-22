import numpy as np
import pytest

from h2prism.phase10 import CAPTURE
from h2prism.phase12_pair import event_integral, first_sustained, framework


def test_multiple_observed_event_brackets_are_integrated_one_sided():
    t = np.arange(12, dtype=float)
    flow = np.where(t < 4, 2., np.where(t < 8, 10., 4.))
    result = event_integral(t, flow, (4, 8))
    np.testing.assert_allclose(np.diff(result), flow[:-1])
    with pytest.raises(ValueError, match='brackets'):
        event_integral(t, flow, (8, 4))


def test_transient_peak_does_not_count_as_sustained():
    t = np.arange(10, dtype=float)
    assert first_sustained(t, np.array([0, 3, 0, 0, 3, 3, 3, 3, 3, 0]), 2) == 4
    assert first_sustained(t, np.array([0, 3, 0, 0, 3, 3, 0, 3, 3, 0]), 2) is None


def test_unknown_bounds_leave_the_existing_framework_unresolved():
    t = 1000 + np.arange(31) * 0.2
    signals = {key: np.ones(t.size) for key in CAPTURE}
    result = framework(t, signals, 1000, 'fixture')
    assert result['diagnostic']['status'] == 'UNRESOLVED'
    assert result['diagnostic']['certificate']['measurement_issues'] == ['INVALID_UNCERTAINTY']
    assert len(result['diagnostic']['certificate']['indeterminate']) == 5
    assert result['localization']['level'] == 'L0'
