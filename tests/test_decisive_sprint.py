import numpy as np

from h2prism.decisive_sprint import cusum, evidence, policy


def test_evidence_replay_prefix_matches_truncated_input():
    x=np.random.default_rng(42).normal(size=(90,16))
    full=evidence(x)
    for actual,expected in zip(evidence(x[:50]),full):
        np.testing.assert_allclose(actual,expected[:46])


def test_suspicion_confirmation_recovery_and_invalid_reset():
    alert,suspect,states=policy([3.,3.,0.,0.,0.,3.,np.nan,3.,3.],2.5,.6,2,3)
    assert alert.tolist()==[0,1,1,1,0,0,0,0,1]
    assert suspect.tolist()==[1,1,1,1,0,1,0,1,1]
    invalid = next(state for state in states if state[0] == 6)
    assert invalid[1]=="SENSOR_INVALID"
    assert invalid[2]=="invalid_score_reset"


def test_bounded_cusum_cannot_go_negative_or_explode():
    x=cusum([100]*20+[0]*20)
    assert x.max()==20 and x[-1]==0 and x.min()==0
