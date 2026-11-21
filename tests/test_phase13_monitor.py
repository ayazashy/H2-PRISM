import numpy as np
import pandas as pd
import pytest

pytest.importorskip("xgboost")

from h2prism.phase13_monitor import CHANNELS, causal_features, mapped_window_features, stream_windows


def test_window_rejects_future_sample_and_metadata():
    x = np.ones((5,len(CHANNELS)))
    with pytest.raises(ValueError, match="noncausal"):
        causal_features(np.arange(5),x,3)
    with pytest.raises(ValueError, match="metadata"):
        causal_features(np.arange(5),x,4,(*CHANNELS[:-1],"label_anomaly"))
    with pytest.raises(ValueError, match="noncausal"):
        causal_features([0,1,1.5,3,4],x,4)


def test_future_values_and_labels_do_not_change_first_decision():
    frame = pd.DataFrame(np.ones((240,len(CHANNELS))),columns=CHANNELS)
    ends, before = stream_windows(frame)
    frame.loc[5:,CHANNELS[0]] = 10000
    frame["label_anomaly"] = 1
    _, after = stream_windows(frame)
    assert ends[0] == 4
    for name in before:
        np.testing.assert_array_equal(before[name][0],after[name][0])


def test_missing_channels_rejected():
    with pytest.raises(ValueError, match="missing"):
        stream_windows(pd.DataFrame({"PS1":[1.]}))



def test_explicit_units_and_named_channel_mapping():
    actual = {name: "sensor_" + name for name in CHANNELS}
    frame = pd.DataFrame({actual[name]: np.full(5, 1e6 if name.startswith("PS") else 1.)
                          for name in reversed(CHANNELS)})
    units = {actual[name]: "Pa" if name.startswith("PS") else "kg/s" for name in CHANNELS}
    np.testing.assert_array_equal(mapped_window_features(frame,4,actual,units)[:len(CHANNELS)],1.)
    units[actual["PS1"]] = "kg/s"
    with pytest.raises(ValueError, match="unsupported units"):
        mapped_window_features(frame,4,actual,units)
