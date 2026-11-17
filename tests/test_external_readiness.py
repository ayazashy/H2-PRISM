import copy
import hashlib
import numpy as np
import pytest

from h2prism.external_readiness import Adapter, open_partition, qualify


SCHEMA = {"clock":{"column":"tick","unit":"ms","timebase":"test clock","nominal_step_s":1},
          "sensors":[
              {"id":"P","column":"gauge","kind":"pressure","unit":"kPa","polarity":1,
               "role":"node","positive_direction":"absolute"},
              {"id":"Q","column":"rate","kind":"mass_flow","unit":"g/s","polarity":-1,
               "role":"edge","positive_direction":"into monitored region"},
          ]}


def record(path, data, sid, partition, family):
    path.write_bytes(data)
    return {"scenario_id":sid,"partition":partition,"root_id":sid,"family_id":family,
            "parent_hashes":[],"ancestry_complete":True,"path":path.name,
            "sha256":hashlib.sha256(data).hexdigest(),"event_class":"NORMAL",
            "mechanism":"nominal","label_receipt":"synthetic"}


def test_adapter_unit_conversion_signed_flow_and_causal_cut():
    obs=Adapter(SCHEMA).parse(b"tick,gauge,rate,label\n0,250,400,0\n1000,260,-800,1\n",deadline=0)
    np.testing.assert_array_equal(obs.clock,[0.])
    np.testing.assert_allclose(obs.values,[[.25,-.4]])
    with pytest.raises(ValueError,match="nonmonotone"):
        Adapter(SCHEMA).parse(b"tick,gauge,rate\n0,250,400\n0,260,-800\n")
    invalid=copy.deepcopy(SCHEMA)
    invalid["sensors"][0]["column"]="label"
    with pytest.raises(ValueError,match="metadata"):
        Adapter(invalid)


def test_sealed_partition_and_duplicate_canonical_trace(tmp_path):
    a=record(tmp_path/"a.csv",b"tick,gauge,rate\n0,250,400\n1000,260,800\n","a","development","x")
    b=record(tmp_path/"b.csv",b"tick,gauge,rate,ignored\n2000,250,400,X\n3000,260,800,Y\n","b","untouched_test","y")
    manifest={"schema":SCHEMA,"records":[a,b],"dataset_id":"fixture","regions":[]}
    assert list(open_partition(tmp_path,manifest,"development"))[0][0]=="a"
    with pytest.raises(ValueError,match="sealed"):
        list(open_partition(tmp_path,manifest,"untouched_test"))
    result=qualify(tmp_path,manifest,{})
    assert any("normalized_trace" in msg for msg in result["issues"]["structure"])
    assert {r["status"] for r in result["claims"].values()}=={"BLOCKED"}


def test_unknown_ancestry_and_checksum_fail_closed(tmp_path):
    r=record(tmp_path/"a.csv",b"tick,gauge,rate\n0,250,400\n1000,260,800\n","a","calibration","x")
    r["ancestry_complete"]=False
    r["sha256"]="0"*64
    result=qualify(tmp_path,{"schema":SCHEMA,"records":[r]}, {})
    assert any("ancestry unresolved" in msg for msg in result["issues"]["structure"])
    assert any("checksum mismatch" in msg for msg in result["issues"]["structure"])



def test_review_registry_is_bound_to_manifest_and_scope(tmp_path):
    import json
    from h2prism.external_readiness import QUALIFICATIONS

    records=[]
    for i,part in enumerate(("development","calibration","untouched_test")):
        for j,label in enumerate(("NORMAL","LEAK","FAULT","DELAY")):
            sid=f"{i}-{j}"
            raw=f"tick,gauge,rate\n0,{250+4*i+j},400\n1000,260,800\n".encode()
            r=record(tmp_path/f"{sid}.csv",raw,sid,part,sid)
            r["event_class"]=label
            if label!="NORMAL":
                r.update(onset_s=0,end_s=1)
            if label=="LEAK":
                r["location"]="L1"
            records.append(r)
    manifest={"dataset_id":"fixture","schema":SCHEMA,"regions":["L1"],"records":records}
    doc=tmp_path/"review.txt"
    doc.write_bytes(b"synthetic approval receipt for gate test")
    h=hashlib.sha256(doc.read_bytes()).hexdigest()
    registry={"dataset_id":"fixture","manifest_canonical_sha256":hashlib.sha256(
        json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "accepted_label_receipts":{r["scenario_id"]:{"receipt":r["label_receipt"],"sha256":r["sha256"]}
                                   for r in records},
        "minimum_roots_per_class":{p:1 for p in ("development","calibration","untouched_test")},
        "approved_evidence":{k:{"reviewed":True,"path":doc.name,"sha256":h} for k in QUALIFICATIONS["multiclass"]}}
    flags=qualify(tmp_path,manifest,registry)["claims"]
    assert flags["multiclass"]["status"]=="ELIGIBLE_FOR_EXTERNAL_REVIEW"
    assert all(flags[name]["status"]=="BLOCKED" for name in ("formal","localization","calibration","incremental_value"))
    manifest["records"][0]["mechanism"]="changed after review"
    assert qualify(tmp_path,manifest,registry)["claims"]["multiclass"]["status"]=="BLOCKED"


def test_cross_partition_checkpoint_alias_is_blocked(tmp_path):
    a=record(tmp_path/"a.csv",b"tick,gauge,rate\n0,250,400\n1000,260,800\n","a","development","x")
    b=record(tmp_path/"b.csv",b"tick,gauge,rate\n0,290,400\n1000,310,800\n","b","calibration","y")
    b["parent_hashes"]=[a["sha256"]]
    r=qualify(tmp_path,{"schema":SCHEMA,"records":[a,b]}, {})
    assert "b: artifact crosses partitions" in r["issues"]["structure"]


def test_deadline_cut_does_not_inspect_future_sensor_or_tail_clock():
    adapter=Adapter(SCHEMA)
    raw=b"tick,gauge,rate\n0,250,400\n1000,inf,broken\ninvalid,garbage,garbage\n"
    result=adapter.parse(raw,deadline=0)
    np.testing.assert_allclose(result.values,[[.25,-.4]])
    with pytest.raises(ValueError):
        adapter.parse(raw)
