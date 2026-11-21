import pandas as pd
import pytest

from h2prism.phase13_alarms import assess, episodes


def test_episode_reset_and_open_tail():
    assert episodes([4,124,244,364,484],[1,1,0,1,1]) == [(4,244),(364,None)]


def test_persistent_pre_event_alarm_is_not_credited_as_new_detection():
    rows = pd.DataFrame(dict(decision_s=[4,124,244,364],truth=[0,1,1,0],prediction=[1,1,1,1]))
    r,_ = assess(rows,100,299,0,400,120)
    assert r["false_episodes"] == 1
    assert r["new_alert_detection"] == 0
    assert r["active_positive_detection"] == 1
    assert r["active_positive_delay_s"] == 24
    assert r["inactive_hours"] == pytest.approx(160/3600)


def test_postevent_start_does_not_count_as_detection():
    rows = pd.DataFrame(dict(decision_s=[4,124,244,364],truth=[0,1,1,0],prediction=[0,0,0,1]))
    r,_ = assess(rows,100,299,0,400,120)
    assert r["false_episodes"] == 1
    assert r["new_alert_detection"] == 0


def test_missing_decision_cannot_contribute_exposure():
    rows = pd.DataFrame(dict(decision_s=[4,244],truth=[0,0],prediction=[0,0]))
    with pytest.raises(ValueError,match="schedule"):
        assess(rows,None,None,0,300,120)
