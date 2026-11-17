"""Alert-anchored causal-prefix ranking against controlled Center templates."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

from .phase13 import CAPTURE,sensor_values,sha256
from .sequential_replay import ChangeStream,decision_stream


def rank_prefix(values,templates,idx,offsets):
    """Compare observed prefix only; time offsets apply to known templates."""
    if values.ndim!=2 or not len(values) or not idx or not np.isfinite(values[:,idx]).all():
        raise ValueError("invalid observation prefix")
    scores={}
    for key,(control,anchor) in templates.items():
        distances=[]
        for offset in offsets:
            start=anchor+offset
            if start<0 or start+len(values)>len(control):
                raise ValueError("template does not cover prefix and offset")
            distances.append(float(np.sqrt(np.mean((values[:,idx]-control[start:start+len(values),idx])**2))))
        scores[key]=min(distances)
    return sorted(scores,key=scores.get),scores


def analyze(base,out, alert_delays=(0,), offset_steps=(0,5,10)):
    work=base/"work"
    evidence=json.loads((base/"outputs/phase13_recovered_final/evidence.json").read_text(encoding="utf8"))
    timing=json.loads((base/"outputs/phase13_integrated_timing/evidence.json").read_text(encoding="utf8"))
    historical={x["id"]:x for x in evidence["historical"]}
    names=list(CAPTURE)
    clock=None
    pairs={}
    paths={"A":"phase12_sdi_retry_01","sid312":"final_research_matrix/sid312",
           "sid215":"final_research_matrix/sid215","pressure_rival":"phase13_02/pressure_rival",
           "alternate_profile":"phase13_02/alternate_profile","timing":"phase13_command_delay_01"}
    for name,folder in paths.items():
        pair=[]
        for case in ("normal","outlet_opening"):
            path=work/folder/case/"center_raw.mat"
            if name=="alternate_profile" and case=="outlet_opening":
                path=work/"phase13_alternate_retry_02"/case/"center_raw.mat"
            key=name+":"+case
            receipt=timing["accepted"][case] if name=="timing" else evidence["accepted"].get(key) or historical[key]
            hashes=receipt.get("capture_hashes") or receipt["receipt"]["capture_hashes"]
            if sha256(path)!=hashes["center_raw.mat"]:
                raise ValueError("source capture changed")
            saved=loadmat(path,simplify_cells=True,variable_names=["sensors"])
            if clock is None:
                clock=saved["sensors"]["pressure_sensor1"]["time"]
            pair.append(np.column_stack([sensor_values(saved,clock)[n] for n in names]))
        pairs[name]=pair
    scale=np.sqrt(np.mean(pairs["A"][0][clock<1000]**2,axis=0))
    contrast={key:(b-a)/scale for key,(a,b) in pairs.items()}
    anchors={key:np.searchsorted(clock,25 if key=="timing" else 1000) for key in contrast}
    templates={key:(contrast[key],anchors[key]) for key in contrast if key!="alternate_profile"}
    templates["NORMAL"]=(np.zeros_like(contrast["timing"]),anchors["pressure_rival"])
    subsets=dict(all=list(range(len(names))),pressure=[i for i,n in enumerate(names) if n.startswith("PS")],
                 flow=[i for i,n in enumerate(names) if n.startswith("MFS")])
    subsets.update({"omit_"+n:[j for j in range(len(names)) if i!=j] for i,n in enumerate(names)})
    rows,alerts=[],[]
    for query,(_,observed) in pairs.items():
        detector=ChangeStream(names)
        # Process full archived stream starting at the original first sample.
        stream=[v for t,x in zip(clock[::5],observed[::5]) if (v:=detector.update(t,x)) is not None]
        flag=list(decision_stream(np.array(stream)[:,1],5,2))
        starts=clock[::5][4:][np.diff(np.r_[0,flag])==1]
        # Two fixed, analyst-defined monitoring scopes, never simulator onset.
        for scope,begins in (("startup",0),("after_startup",200)):
            eligible=starts[starts>=begins]
            alert=float(eligible[0]) if len(eligible) else None
            alerts.append(dict(query=query,scope=scope,start_s=begins,first_alert_s=alert))
            if alert is None:
                continue
            for alert_delay in alert_delays:
                j=np.searchsorted(clock,alert+alert_delay)
                for horizon in (0,1,2,5,10,30):
                    stop=j+round(horizon/.2)+1
                    if stop>len(clock):
                        continue
                    # Paired reference readings must be contemporaneous; no future sample is used.
                    prefix=contrast[query][j:stop]
                    for subset,indices in subsets.items():
                        for offset in offset_steps:
                            ordered,scores=rank_prefix(prefix,templates,indices,range(-offset,offset+1))
                            rows.append(dict(query=query,scope=scope,alert_s=alert,deadline_s=clock[stop-1],
                                alert_delay_s=alert_delay,window_s=horizon,subset=subset,hypothetical_offset_s=offset*.2,
                                rank=" ".join(ordered),margin=scores[ordered[1]]-scores[ordered[0]],
                                rms=json.dumps(scores),self_template=query in templates,
                                candidate_locations="213 312 215",formal="UNRESOLVED / L0"))
    pd.DataFrame(rows).to_csv(out/"prefix_ranks.csv",index=False)
    pd.DataFrame(alerts).to_csv(out/"rank_alerts.csv",index=False)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--alert-delays",type=int,nargs="+",default=[0])
    p.add_argument("--offset-steps",type=int,nargs="+",default=[0,5,10])
    a=p.parse_args()
    if min(a.alert_delays+a.offset_steps)<0:
        p.error("timing limits must be nonnegative")
    a.out.mkdir(parents=True)
    analyze(a.base,a.out,a.alert_delays,a.offset_steps)
