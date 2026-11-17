import numpy as np

from h2prism.mechanism_screen import MECHANISMS, NORMAL, WITHDRAWAL, reference, screen
from h2prism.nres import Observation, Sensor


def fixtures():
    t=np.arange(20.)
    loc=("SID213","SID312","SID215")
    data={name:(np.column_stack((t*0+v,t*0-v)),5)
          for name,v in zip(("NORMAL_ZERO",*loc,"PRESSURE","TIMING"),(0.,1.,2.,3.,10.,11.))}
    return data,loc


def test_rank_blocks_nonalarm_location_and_retains_all_if_routed():
    lib,loc=fixtures()
    p=lib["PRESSURE"][0][5:10]
    r=screen(p,lib,MECHANISMS,loc,1,1,[1,1])
    assert r["forced_location"]=="SID215" and not r["eligible"]
    assert r["formal"]=="UNRESOLVED" and r["localization"]=="L0"
    q=lib["SID213"][0][5:10]
    r=screen(q,lib,MECHANISMS,loc,1,1,[1,1])
    assert r["mechanism"]==WITHDRAWAL and r["location_ranked"]=="SID213"
    assert r["retained_locations"]==list(loc)
    mask=np.ones_like(q,dtype=bool)
    mask[:,1]=False
    assert not screen(q,lib,MECHANISMS,loc,1,1,[1,1],mask)["eligible"]


def test_order_permutation_and_reference_causality():
    lib,loc=fixtures()
    q=lib["SID213"][0][5:10]
    before=screen(q,lib,MECHANISMS,loc,1,1,[2,1])
    reverse={k:(x[:,::-1],i) for k,(x,i) in lib.items()}
    assert screen(q[:,::-1],reverse,MECHANISMS,loc,1,1,[1,2])["hypotheses"]==before["hypotheses"]
    t=np.arange(8.)
    schema=(Sensor("pressure","pressure","MPa"),)
    x=Observation(t,t[:,None],schema)
    y=Observation(t,np.zeros((8,1)),schema)
    assert reference(x,y,3,mode="operational",qualified=True)==("BLOCKED_REFERENCE",None)
    r=reference(x,y,3,mode="operational",source="past_only",qualified=True)[1]
    y.values[4:]=1e9
    np.testing.assert_array_equal(reference(x,y,3,mode="operational",source="past_only",qualified=True)[1],r)
