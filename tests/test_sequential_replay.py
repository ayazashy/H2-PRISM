import numpy as np
import pytest

from h2prism.sequential_replay import CHANNELS, ChangeStream, decision_stream, diagnostic_state


def run(values):
    stream = ChangeStream()
    return [stream.update(i,row) for i,row in enumerate(values)]


def test_prefix_identical_and_warmup_explicit():
    data = np.ones((9,16))
    original = run(data)
    data[6:] *= 3
    modified = run(data)
    assert original[:6] == modified[:6]
    assert original[:4] == [None]*4
    assert modified[6][0] > 0


def test_invalid_sample_leaves_state_unmodified():
    s = ChangeStream()
    s.update(10,np.ones(16))
    with pytest.raises(ValueError):
        s.update(12,np.ones(16))
    with pytest.raises(ValueError):
        s.update(11,np.ones(15))
    with pytest.raises(ValueError):
        s.update(11,np.ones(16),CHANNELS[::-1])
    assert s.update(11,np.ones(16)) is None


def test_alarm_hysteresis_and_independent_diagnostic_output():
    assert list(decision_stream([0,6,3,1,3,6],5,2)) == [0,1,1,0,0,1]
    assert diagnostic_state(True)["diagnosis"] == "UNRESOLVED"
    assert diagnostic_state(True)["alert"] is True
