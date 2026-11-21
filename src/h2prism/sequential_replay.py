"""Causal change-alert replay on archived 1 Hz telemetry."""
import argparse
from collections import deque
from itertools import combinations
import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.signal import lfilter

from .data.loader import load_scenario
from .phase13 import CAPTURE, sensor_values, sha256
from .phase13_alarms import assess, summarize
from .simnet_study import annotation, archive_path, catalog_tables

CHANNELS = tuple([f"PS{i}" for i in range(1,13)] + [f"MFS{i}" for i in range(1,5)])
CADENCES = (1,2,5,10,30,120)
DEADLINES = (5,10,30,60,120)
MODES = ("clean","white","correlated","bias","drift","stuck","delay")
FLOORS = np.array([.001]*12+[.005]*4)


class ChangeStream:
    """Five-knot difference plus EWMA; no case labels or event times."""
    def __init__(self, channels=CHANNELS):
        self.channels = tuple(channels)
        self.floors = np.array([.001 if n.startswith("PS") else .005 for n in self.channels])
        self.window = deque(maxlen=5)
        self.last = None
        self.scale = None
        self.ewma = 0.

    def update(self,t,x,channels=None):
        if (channels is not None and tuple(channels)!=self.channels) or not np.isfinite(t):
            raise ValueError("unexpected schema or clock")
        x = np.asarray(x,dtype=float)
        if x.shape!=(len(self.channels),) or not np.isfinite(x).all() or (self.last is not None and t-self.last!=1):
            raise ValueError("invalid sensor row or unsupported clock")
        if self.scale is None:
            self.scale = np.maximum(self.floors,.005*abs(x))
        self.last = t
        self.window.append(x.copy())
        if len(self.window)<5:
            return None
        score = float(np.max(abs(x-self.window[0])/self.scale))
        self.ewma = .25*score+.75*self.ewma
        return score,self.ewma


def decision_stream(scores,high,low):
    state = False
    for score in scores:
        state = score > (low if state else high)
        yield int(state)


def diagnostic_state(alert, qualified_result=None):
    """Timing of early alert is independent of the formal result."""
    return dict(alert=bool(alert),
                diagnosis=qualified_result.status.value if qualified_result is not None else "UNRESOLVED",
                provisional_rank=None,qualified_specific_time=None)


def perturb(x,seed):
    rng=np.random.default_rng(seed)
    noise=rng.normal(size=x.shape)*np.maximum(FLOORS,.01*abs(x[0]))
    yield "clean",x
    yield "white",x+noise
    yield "correlated",x+lfilter([1.],[1.,-.8],noise,axis=0)
    bias=x.copy()
    bias[len(x)//2:,0]+=.01*abs(x[0,0])
    yield "bias",bias
    drift=x.copy()
    drift[:,12]+=.02*abs(x[0,12])*np.arange(len(x))/max(1,len(x)-1)
    yield "drift",drift
    stuck=x.copy()
    stuck[:,0]=x[0,0]
    yield "stuck",stuck
    delay=x.copy()
    delay[2:,0]=x[:-2,0]
    delay[:2,0]=x[0,0]
    yield "delay",delay


def replay(frozen,out):
    registry=pd.read_csv(frozen/"provenance.csv").set_index("scenario")
    manifest,_=catalog_tables()
    source={r.Scenario_ID:r for r in manifest.itertuples(index=False)}
    rows,latencies=[],[]
    for seed,(sid,meta) in enumerate(registry.iterrows(),42):
        record=source[sid]
        if record.sha256_clean!=meta.archive_sha256:
            raise ValueError("archive lineage mismatch")
        frame=load_scenario(archive_path(record))
        t=frame.index.to_numpy(dtype=float)
        x=frame.loc[:,list(CHANNELS)].to_numpy(dtype=float)
        # All cadences share the 120 s baseline's last observation and exposure.
        stop=t[0]+4+120*((t[-1]-t[0]-4)//120)
        size=np.searchsorted(t,stop,side="right")
        for mode,values in perturb(x,seed):
            stream=ChangeStream()
            start_ns=perf_counter_ns()
            stats=np.array([v for clock,row in zip(t[:size],values[:size])
                            if (v:=stream.update(clock,row)) is not None])
            elapsed=perf_counter_ns()-start_ns
            latencies.append(dict(scenario=sid,mode=mode,samples=size,mean_update_us=elapsed/size/1000))
            # Get truth only after the causal statistic is complete.
            if mode=="clean":
                labels,issues=annotation(frame,record)
                if issues:
                    raise ValueError(issues)
                onset,last=labels["onset_s"],labels["last_active_s"]
            for interval in CADENCES:
                clock=t[4:size:interval]
                for detector,value,hi,lo in (("change",stats[:,0],5.,2.),("ewma",stats[:,1],5.,2.)):
                    decision=list(decision_stream(value[::interval],hi,lo))
                    decision_rows=pd.DataFrame(dict(decision_s=clock,prediction=decision,
                        truth=frame.label_anomaly.iloc[4:size:interval].to_numpy()))
                    metrics,alarms=assess(decision_rows,onset,last,t[0],stop,interval)
                    delay=metrics["alarm_delay_s"]
                    false=[a for a,_ in alarms if onset is None or not onset<=a<=last]
                    duration=sum((stop if b is None else b)-a for a,b in alarms)
                    rows.append(dict(scenario=sid,component=meta.group,subtype=meta.event,
                        mode=mode,detector=detector,interval_s=interval,
                        duty_cycle=duration/(stop-clock[0]),alarm_duration_s=duration,
                        false_restarts_300s=int(np.sum(np.diff(false)<=300)),
                        **metrics,**{f"within_{d}s":int(delay is not None and delay<=d) for d in DEADLINES}))
    result=pd.DataFrame(rows)
    result.to_csv(out/"scenario_metrics.csv",index=False)
    pd.DataFrame(latencies).to_csv(out/"update_timing.csv",index=False)
    for name,extras in (("summary",[]),("by_component",["component"]),("by_subtype",["subtype"])):
        keys=["detector","mode","interval_s",*extras]
        report=summarize(result,keys)
        supplemental=result.groupby(keys).agg(
            p90_delay_s=("alarm_delay_s",lambda a:a.quantile(.9)),max_delay_s=("alarm_delay_s","max"),
            mean_duty_cycle=("duty_cycle","mean"),false_restarts_300s=("false_restarts_300s","sum"),
            **{f"within_{d}s":(f"within_{d}s","sum") for d in DEADLINES}).reset_index()
        report.merge(supplemental,on=keys).to_csv(out/(name+".csv"),index=False)
    result[result.alarm_delay_s.notna()].groupby(["detector","mode","interval_s"]).alarm_delay_s.quantile(
        [0,.25,.5,.75,.9,1]).to_csv(out/"delay_quantiles.csv")


def timing_geometry(base,out):
    work=base/"work"
    old=json.loads((base/"outputs/phase13_recovered_final/evidence.json").read_text(encoding="utf8"))
    new=json.loads((base/"outputs/phase13_integrated_timing/evidence.json").read_text(encoding="utf8"))
    registry={r["id"]:r for r in old["historical"]}
    names=list(CAPTURE)
    def observations(folder,c,receipt):
        path=folder/c/"center_raw.mat"
        hashes=receipt.get("capture_hashes") or receipt["receipt"]["capture_hashes"]
        if sha256(path)!=hashes["center_raw.mat"]:
            raise ValueError("raw capture changed")
        saved=loadmat(path,simplify_cells=True,variable_names=["sensors"])
        clock=saved["sensors"]["pressure_sensor1"]["time"]
        return clock,np.column_stack(list(sensor_values(saved,clock).values()))
    pairs={}
    reference_clock=None
    folders={"A":"phase12_sdi_retry_01","sid312":"final_research_matrix/sid312",
             "sid215":"final_research_matrix/sid215","pressure_rival":"phase13_02/pressure_rival",
             "alternate_profile":"phase13_02/alternate_profile","timing":"phase13_command_delay_01"}
    for name,folder in folders.items():
        values=[]
        for case in ("normal","outlet_opening"):
            path=work/folder
            if name=="alternate_profile" and case=="outlet_opening":
                path=work/"phase13_alternate_retry_02"
            key=name+":"+case
            receipt=new["accepted"][case] if name=="timing" else old["accepted"].get(key) or registry[key]
            clock,x=observations(path,case,receipt)
            if reference_clock is None:
                reference_clock=clock
            if not np.array_equal(clock,reference_clock):
                raise ValueError("controlled saved clocks differ")
            values.append(x)
        pairs[name]=values
    scale=np.sqrt(np.mean(pairs["A"][0][clock<1000]**2,axis=0))
    onset_rows=[]
    for name,(control,treated) in pairs.items():
        for variant,x in (("control",control),("treated",treated)):
            truth = (25 if variant=="control" else 26) if name=="timing" else (1000 if variant=="treated" else None)
            stream=ChangeStream(names)
            update=[r for t,row in zip(clock[::5],x[::5]) if (r:=stream.update(t,row)) is not None]
            flags=np.array(list(decision_stream(np.array(update)[:,1],5.,2.)))
            starts=clock[::5][4:][np.diff(np.r_[0,flags])==1]
            eligible=starts[(starts>=truth)&(starts<=truth+120)] if truth is not None else np.array([])
            onset_rows.append(dict(pair=name,case=variant,
                first_alert_s=starts[0] if len(starts) else None,
                annotated_onset_s=truth,first_new_alert_within_120s=eligible[0] if len(eligible) else None,
                retrospective_delay_s=eligible[0]-truth if len(eligible) else None))
    pd.DataFrame(onset_rows).to_csv(out/"controlled_alert_timing.csv",index=False)
    contrasts={name:((b-a)/scale,np.searchsorted(clock,25 if name=="timing" else 1000))
               for name,(a,b) in pairs.items()}
    a,b=pairs["timing"]
    offset=round(1/.2)
    contrasts["timing_event_aligned"]=((b[offset:]-a[:-offset])/scale,np.searchsorted(clock,25))
    contrasts["NORMAL"]=(np.zeros_like(pairs["A"][0]),np.searchsorted(clock,1000))
    p=[i for i,n in enumerate(names) if n.startswith("PS")]
    f=[i for i,n in enumerate(names) if n.startswith("MFS")]
    subsets=dict(all=list(range(len(names))),pressure=p,flow=f)
    for i,name in enumerate(names):
        subsets[name]=[i]
        subsets["omit_"+name]=[j for j in range(len(names)) if j!=i]
    rows=[]
    for a,b in combinations(contrasts,2):
        u,i=contrasts[a]
        v,j=contrasts[b]
        for window in (1,5,30,120):
            size=round(window/.2)+1
            for subset,idx in subsets.items():
                for limit in (0,.2,.6,1,2):
                    steps=round(limit/.2)
                    scores=[float(np.sqrt(np.mean((u[i:i+size,idx]-v[j+k:j+k+size,idx])**2)))
                            for k in range(-steps,steps+1)]
                    rows.append(dict(a=a,b=b,seconds=window,subset=subset,hypothetical_offset_s=limit,
                                     min_rms=min(scores),max_rms=max(scores),best_offset_s=(int(np.argmin(scores))-steps)*.2))
    pd.DataFrame(rows).to_csv(out/"timing_geometry.csv",index=False)
    loc=["A","sid312","sid215"]
    candidates=[]
    for observed in ("alternate_profile","pressure_rival","timing"):
        for subset in ("all","pressure","flow","omit_MFS1","omit_MFS2","omit_MFS3"):
            for limit in (0,.6,1,2):
                scores={}
                for r in rows:
                    if (r["seconds"],r["subset"],r["hypothetical_offset_s"],r["b"])==(30,subset,limit,observed) and r["a"] in loc:
                        scores[r["a"]]=r["min_rms"]
                ranking=sorted(scores,key=scores.get)
                candidates.append(dict(observation=observed,subset=subset,offset_s=limit,
                    ranking=" ".join(ranking),rms=json.dumps(scores),candidate_set="A sid312 sid215",
                    warning="One source family; no qualified exclusions. Location ranking only conditional on withdrawal."))
    pd.DataFrame(candidates).to_csv(out/"location_candidates.csv",index=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base",type=Path)
    parser.add_argument("out",type=Path)
    a=parser.parse_args()
    a.out.mkdir(parents=True)
    replay(a.base/"outputs/phase13_causal_validation",a.out)
    timing_geometry(a.base,a.out)


if __name__=="__main__":
    main()
