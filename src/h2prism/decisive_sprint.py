"""Fixed 1 Hz sequential evidence experiments on previously examined archives."""
import argparse
import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import pandas as pd
from scipy.signal import lfilter

from .causal_intelligence import scoring
from .phase13_alarms import assess, summarize
from .sequential_replay import CHANNELS, FLOORS, decision_stream, perturb
from .data.loader import load_scenario
from .simnet_study import annotation, archive_path, catalog_tables

DEADLINES=(1,2,5,10,30,60,120)


def evidence(x):
    if x.ndim!=2 or x.shape[1]!=16 or len(x)<5 or not np.isfinite(x).all():
        raise ValueError("invalid canonical samples")
    signed=x[4:]-x[:-4]
    inc=np.vstack((np.zeros((1,16)),abs(np.diff(x,axis=0))))
    previous=pd.DataFrame(inc).rolling(31,min_periods=1).median().shift(1).fillna(0).to_numpy()[4:]
    scale=np.maximum(np.maximum(FLOORS,.005*abs(x[0])),4*previous)
    normalized=signed/scale
    # Clip individual excess before accumulating; asynchronously arriving evidence persists.
    bounded=np.clip(abs(normalized)-1.,0,3)
    channel_memory=lfilter([.25],[1,-.75],bounded,axis=0)
    accumulator=np.sort(channel_memory,axis=1)[:,-3:].sum(axis=1)
    innovation=np.max(abs(normalized),axis=1)
    return normalized,accumulator,innovation


def policy(score,opening,closing,confirm=1,recover=1):
    """Finite-state alarm; invalid scores require fresh confirmation."""
    active=False
    count=0
    previous="NORMAL_MONITORING"
    alerts,suspects,changes=[],[],[]
    for i,value in enumerate(score):
        if not np.isfinite(value):
            active,count=False,0
            state,reason="SENSOR_INVALID","invalid_score_reset"
        elif active:
            count=count+1 if value<=closing else 0
            if count>=recover:
                active,count=False,0
                state,reason="NORMAL_MONITORING","recovery_complete"
            elif count:
                state,reason="RECOVERY","low_evidence_pending_reset"
            else:
                state,reason="CONFIRMED_ALARM","above_reset"
        else:
            count=count+1 if value>opening else 0
            if count>=confirm:
                active,count=True,0
                state,reason="CONFIRMED_ALARM","confirmation_complete"
            elif count:
                state,reason="SUSPECTED_EVENT","above_open_pending_confirmation"
            else:
                state,reason="NORMAL_MONITORING","insufficient_evidence"
        alerts.append(int(active))
        suspects.append(int(active or state=="SUSPECTED_EVENT"))
        if state!=previous:
            changes.append((i,state,reason,None if not np.isfinite(value) else float(value)))
        previous=state
    return np.array(alerts),np.array(suspects),changes


def cusum(innovation):
    """Reflected, capped excess above a fixed engineering reference; no IID claim."""
    current=0.
    values=[]
    for value in innovation:
        current=min(20.,max(0.,current+min(4.,float(value))-1.5))
        values.append(current)
    return np.asarray(values)


def run(base,out):
    prior=base/"outputs/phase13_causal_intelligence"
    old=pd.read_csv(prior/"scenario.csv")
    old=old[old.model=="reference"].set_index(["scenario","mode"])
    metadata=pd.read_csv(base/"outputs/phase13_causal_validation/provenance.csv")
    manifest,_=catalog_tables()
    sources={r.Scenario_ID:r for r in manifest.itertuples(index=False)}
    rows,forensics,transition_rows,episode_rows,cost=[],[],[],[],[]
    for seed,meta in enumerate(metadata.itertuples(index=False),42):
        source=sources[meta.scenario]
        if source.sha256_clean!=meta.archive_sha256:
            raise ValueError("archive hash differs")
        frame=load_scenario(archive_path(source))
        t=frame.index.to_numpy(dtype=float)
        if not np.all(np.diff(t)==1):
            raise ValueError("invalid 1 Hz clock")
        end=t[0]+4+120*((t[-1]-t[0]-4)//120)
        n=np.searchsorted(t,end,side="right")
        clock=t[4:n]
        x=frame[list(CHANNELS)].to_numpy()
        truth=None
        for mode,values in perturb(x,seed):
            start=perf_counter_ns()
            norm,acc,innovation=evidence(values[:n])
            c=cusum(innovation)
            flags={}
            for name,series,hi,lo,k,r in (("accumulator",acc,2.5,.6,1,1),
                                          ("two_stage",acc,2.5,.6,2,3),
                                          ("cusum",c,8,2,1,1)):
                flags[name]=policy(series,hi,lo,k,r)
            cost.append(dict(scenario=meta.scenario,mode=mode,combined_us_per_row=(perf_counter_ns()-start)/n/1000))
            if mode=="clean":
                label,issues=annotation(frame,source)
                if issues:
                    raise ValueError(issues)
                onset,last=label["onset_s"],label["last_active_s"]
                truth=frame.label_anomaly.iloc[4:n].to_numpy()
            ref,_=scoring(values[:n])
            reference=np.array(list(decision_stream(ref,5,2)))
            flags["reference"]=(reference,reference,[])
            for name,(alarms,suspects,changes) in flags.items():
                common=dict(decision_s=clock,truth=truth)
                metrics,episodes=assess(pd.DataFrame(dict(**common,prediction=alarms)),onset,last,t[0],end,1)
                suspected,_=assess(pd.DataFrame(dict(**common,prediction=suspects)),onset,last,t[0],end,1)
                delay=metrics["alarm_delay_s"]
                duration=sum((end if b is None else b)-a for a,b in episodes)
                rows.append(dict(scenario=meta.scenario,component=meta.group,subtype=meta.event,mode=mode,model=name,
                    **metrics,duty=duration/(end-clock[0]),suspicion_delay_s=suspected["alarm_delay_s"],
                    suspected=suspected["new_alert_detection"],open_tail=int(bool(alarms[-1])),
                    **{f"within_{d}s":int(delay is not None and delay<=d) for d in DEADLINES}))
                if name=="reference":
                    frozen=old.loc[(meta.scenario,mode)]
                    if (metrics["false_episodes"],metrics["new_alert_detection"])!=(frozen.false_episodes,frozen.new_alert_detection):
                        raise ValueError("frozen reference count differs")
                    if (delay is None and pd.notna(frozen.alarm_delay_s)) or (delay is not None and delay!=frozen.alarm_delay_s):
                        raise ValueError("frozen reference timing differs")
                for i,state,reason,value in changes:
                    transition_rows.append((meta.scenario,mode,name,clock[i],state,reason,value,"VALID_1HZ_ROW"))
                for a,b in episodes:
                    episode_rows.append((meta.scenario,mode,name,a,b,(end if b is None else b)-a,
                                         onset is not None and onset<=a<=last))
            if onset is not None:
                early=(clock>=onset)&(clock<=min(onset+5,last))
                early_norm=norm[early]
                contributors=abs(early_norm)>1
                top=CHANNELS[int(np.argmax(abs(early_norm).max(axis=0)))] if early.any() else None
                j=np.searchsorted(clock,onset)
                observed_alarm_open=bool(j>0 and j<len(reference) and reference[j-1] and reference[j])
                forensics.append(dict(scenario=meta.scenario,mode=mode,subtype=meta.event,
                    onset_s=onset,last_active_s=last,early_knots=int(early.sum()),peak_driver=top,
                    simultaneous_channels=int(contributors.sum(axis=1).max()) if early.any() else 0,
                    union_channels=int(contributors.any(axis=0).sum()) if early.any() else 0,
                    reference_open_at_onset=observed_alarm_open,
                    reference_early_peak=float(ref[early].max()) if early.any() else None,
                    signed_normalized_peak_by_channel=json.dumps(
                        {name:float(early_norm[np.argmax(abs(early_norm[:,i])),i]) for i,name in enumerate(CHANNELS)}
                    ) if early.any() else None))
    out.mkdir(parents=True)
    result=pd.DataFrame(rows)
    result.to_csv(out/"scenario.csv",index=False)
    pd.DataFrame(forensics).to_csv(out/"failure_matrix.csv",index=False)
    pd.DataFrame(cost).to_csv(out/"compute.csv",index=False)
    pd.DataFrame(transition_rows,columns=["scenario","mode","model","time_s","state","reason","score","quality"]).to_csv(out/"transitions.csv",index=False)
    pd.DataFrame(episode_rows,columns=["scenario","mode","model","start_s","reset_s","duration_s","in_event_start"]).to_csv(out/"episodes.csv",index=False)
    for name,keys in (("comparison",["mode","model"]),("subtype",["mode","model","subtype"])):
        summary=summarize(result,keys)
        other=result.groupby(keys).agg(mean_duty=("duty","mean"),open_tail=("open_tail","sum"),
          suspected=("suspected","sum"),median_suspicion_delay_s=("suspicion_delay_s","median"),
          p90_delay_s=("alarm_delay_s",lambda x:x.quantile(.9)),p95_delay_s=("alarm_delay_s",lambda x:x.quantile(.95)),
          max_delay_s=("alarm_delay_s","max"),**{f"within_{d}s":(f"within_{d}s","sum") for d in DEADLINES}).reset_index()
        summary.merge(other,on=keys).to_csv(out/(name+".csv"),index=False)
    (out/"settings.json").write_text(json.dumps(dict(reference_rows_checked=len(old),cadence_s=1,
        adaptive_noise="31 prior increments; four times median; fixed initial floors",
        accumulator="top three causal per-channel memories; excess clipped 0 to 3",
        cusum="max channel innovation, clipped at 4, drift 1.5, reflected and capped at 20",
        rules={"accumulator":[2.5,.6,1,1],"two_stage":[2.5,.6,2,3],"cusum":[8,2,1,1]},
        scope="exploratory; no parameter selection or deployment threshold"),indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    run(a.base,a.out)
