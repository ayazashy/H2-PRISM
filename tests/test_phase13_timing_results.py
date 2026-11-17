import numpy as np
import pytest

from h2prism.phase13_alarm_sensitivity import debounce
from h2prism.phase13_timing_results import aligned, step_time


def test_time_alignment_uses_only_shared_relative_clock():
    control = np.array([0.,1.,2.,3.,4.])
    delayed = np.array([0.,0.,1.,2.,3.])
    np.testing.assert_array_equal(aligned(control,delayed,1),0.)
    with pytest.raises(ValueError):
        aligned(control,delayed,5)
    assert step_time(np.arange(5),np.array([3.,3.,6.4,6.4,6.4])) == 2


def test_debounce_waits_for_two_consecutive_opens_and_resets():
    assert debounce([1,0,1,1,0,1,0,0],2,2)==[0,0,0,1,1,1,1,0]
