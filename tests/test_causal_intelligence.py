import numpy as np
import pytest

from h2prism.causal_intelligence import RobustStream, scoring, states
from h2prism.causal_prefix_ranking import rank_prefix


def test_batch_matches_stream_and_cannot_see_future():
    rng=np.random.default_rng(42)
    x=rng.normal(size=(140,16))
    stream=RobustStream()
    result=[stream.update(t,r) for t,r in enumerate(x)][4:]
    _,score=scoring(x)
    np.testing.assert_allclose([r["score"] for r in result],score)
    assert [r["state"] for r in result]==list(states(score))
    short=scoring(x[:90])[1]
    np.testing.assert_allclose(short,score[:86])


def test_invalid_sensor_rows_never_produce_a_diagnosis_or_advance_clock():
    s=RobustStream()
    s.update(0,np.ones(16))
    for t,row in ((0,np.ones(16)),(-1,np.ones(16)),(2,np.ones(16)),(1,np.ones(15))):
        rejected=s.update(t,row)
        assert rejected["state"]=="SENSOR_INVALID"
        assert rejected["diagnosis"]=="UNRESOLVED"
        assert rejected["alert"] is None
    assert s.update(1,np.ones(16))["state"]=="WARMUP"


def test_ranking_uses_exact_observed_prefix_and_rejects_short_templates():
    a=np.arange(12,dtype=float).reshape(6,2)
    obs=a[2:4]
    order,scores=rank_prefix(obs,{"match":(a,2),"rival":(a*2,2)},[0,1],[0])
    assert order[0]=="match" and scores["match"]==0
    with pytest.raises(ValueError):
        rank_prefix(obs,{"bad":(a,5)},[0],[0])
