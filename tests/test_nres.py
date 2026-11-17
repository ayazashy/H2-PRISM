import numpy as np
import pytest

from h2prism.nres import Observation, Sensor, distance, rank, residual


def test_canonical_units_and_deadline_only():
    t=np.arange(4.)
    sensors=(Sensor("P","pressure","Pa"),Sensor("F","mass_flow","g/s"))
    x=np.array([[1e6,-2000.]]*4)
    obs=Observation(t,x,sensors)
    ref=Observation(t,np.array([[1.,-2.]]*4),
                    (Sensor("P","pressure","MPa"),Sensor("F","mass_flow","kg/s")))
    assert residual(obs,ref,2)[0]=="OK"
    np.testing.assert_array_equal(residual(obs,ref,2)[1],np.zeros((3,2)))
    x[3]=[4e6,1000.]
    np.testing.assert_array_equal(residual(obs,ref,2)[1],np.zeros((3,2)))
    assert residual(obs,ref,2,operational=True)==("BLOCKED_REFERENCE",None)
    assert residual(obs,None,2)==("BLOCKED_REFERENCE",None)
    with pytest.raises(ValueError,match="timestamps"):
        residual(obs,Observation(t+.1,ref.values,ref.schema),2)


def test_shared_shift_preserves_per_channel_alignment():
    t=np.arange(20.)
    template=np.column_stack([t,t*t])
    query=template[7:11]
    d=distance(query,template,5,1.,2.,[1.,1.])
    assert d["selected_shift_s"]==2. and d["rms"]==0.
    query=np.column_stack([template[7:11,0],template[3:7,1]])
    assert distance(query,template,5,1.,2.,[1.,1.])["rms"]>0.
    with pytest.raises(ValueError):
        distance(query,template,5,1.,np.nan,[1.,1.])


def test_common_missing_support_permutation_and_no_narrowing():
    q=np.array([[3.,np.nan],[3.,np.nan]])
    a=np.ones((8,2))
    b=a*2
    all_r=rank(q,{"a":(a,2),"b":(b,2)},1.,1.,[1.,2.])
    assert all_r["ranks"][0]["candidate"]=="b"
    assert all_r["ranks"][0]["rms"]==1.
    assert all_r["ranks"][0]["invalid_channels"]==[1]
    assert all_r["candidate_set"]==["a","b"]
    other=rank(q[:,::-1],{"a":(a[:,::-1],2),"b":(b[:,::-1],2)},1.,1.,[2.,1.])
    assert [v["rms"] for v in all_r["ranks"]]==[v["rms"] for v in other["ranks"]]
    assert rank(q,{},1.,1.,[1.,2.])["policy"]=="RANKED_ONLY"
    np.testing.assert_array_equal(q[:,0],[3.,3.])



def test_operational_wrapper_blocks_unqualified_reference_and_future_changes():
    from h2prism.nres import evaluate
    t=np.arange(6.)
    schema=(Sensor("P","pressure","MPa"),)
    obs=Observation(t,np.arange(6.)[:,None],schema)
    ref=Observation(t,np.zeros((6,1)),schema)
    config={"step_s":1.,"bound_s":0.,"scales":[1.]}
    templates={"A":(np.arange(8.)[:,None],0)}
    blocked=evaluate(obs,ref,2,templates,config,operational=True)
    assert blocked["status"]=="BLOCKED_REFERENCE" and blocked["candidate_set"]==["A"]
    before=evaluate(obs,ref,2,templates,config)
    obs.values[3:]*=100
    assert evaluate(obs,ref,2,templates,config)==before
    assert before["evidence"]=="EXPLORATORY"
