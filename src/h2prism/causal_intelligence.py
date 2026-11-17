"""Forensic replay and a robust-scale causal alarm comparator."""
import argparse
from collections import deque
import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import pandas as pd
from scipy.signal import lfilter

from .data.loader import load_scenario
from .phase13_alarms import assess, summarize
from .sequential_replay import CHANNELS,FLOORS,decision_stream,perturb
from .simnet_study import annotation,archive_path,catalog_tables

DEADLINES=(1,2,5,10,30,60,120)


def scoring(x):
    """Prefix-equivalent batch calculation, using a strictly trailing noise scale."""
    if x.ndim!=2 or x.shape[1]!=len(CHANNELS) or len(x)<5 or not np.isfinite(x).all():
        raise ValueError("invalid sensor sample matrix")
    fixed=np.maximum(FLOORS,.005*abs(x[0]))
    delta=abs(x[4:]-x[:-4])
    plain=np.max(delta/fixed,axis=1)
    inc=np.vstack((np.zeros((1,x.shape[1])),abs(np.diff(x,axis=0))))
    prior=pd.DataFrame(inc).rolling(31,min_periods=1).median().shift(1).fillna(0).to_numpy()
    robust=delta/np.maximum(fixed,4*prior[4:])
    # Fourth-largest channel requires corroboration from at least four channels.
    corroborated=np.partition(robust,-4,axis=1)[:,-4]
    return lfilter([.25],[1,-.75],plain),lfilter([.25],[1,-.75],corroborated)


def transition(active,run,score,confirmation,recovery):
    condition=score<=2 if active else score>5
    run=run+1 if condition else 0
    if run >= (recovery if active else confirmation):
        active,run=not active,0
    name=("RECOVERY" if run else "ACTIVE_ALARM") if active else (
          "SUSPECTED_CHANGE" if run else "NORMAL_MONITORING")
    return active,run,name


def states(score,confirmation=2,recovery=3):
    active,run=False,0
    for val in score:
        active,run,name=transition(active,run,val,confirmation,recovery)
        yield name


class RobustStream:
    """One-sample interface for the versioned robust stateful policy."""
    policy_id = "robust-scale-e25-q4-5-2-p2-r3-v1"

    def __init__(self):
        self.samples=deque(maxlen=5)
        self.increments=deque(maxlen=31)
        self.last_t=None
        self.scale=None
        self.smoothed=0.
        self.active=False
        self.run=0

    def update(self,t,values,channels=CHANNELS):
        values=np.asarray(values,dtype=float)
        if (tuple(channels)!=CHANNELS or values.shape!=(len(CHANNELS),)
                or not np.isfinite(t) or not np.isfinite(values).all()
                or (self.last_t is not None and t-self.last_t!=1)):
            # A caller must explicitly restart from fresh warm-up after an interruption.
            return {"state":"SENSOR_INVALID","diagnosis":"UNRESOLVED","alert":None,
                    "score":None,"policy_id":self.policy_id}
        increment=abs(values-self.samples[-1]) if self.samples else np.zeros(len(CHANNELS))
        self.last_t=t
        self.samples.append(values.copy())
        if self.scale is None:
            self.scale=np.maximum(FLOORS,.005*abs(values))
        score=None
        state="WARMUP"
        if len(self.samples)==5:
            noise=np.median(np.asarray(self.increments),axis=0)
            innovation=abs(values-self.samples[0])/np.maximum(self.scale,4*noise)
            self.smoothed=.25*np.partition(innovation,-4)[-4]+.75*self.smoothed
            score=float(self.smoothed)
            self.active,self.run,state=transition(self.active,self.run,score,2,3)
        self.increments.append(increment)
        return {"state":state,"diagnosis":"UNRESOLVED","alert":self.active,
                "score":score,"policy_id":self.policy_id}


def replay(base,out):
    frozen=base/"outputs/phase13_causal_validation"
    reference=pd.read_csv(base/"outputs/phase13_sequential/scenario_metrics.csv")
    reference=reference[(reference.detector=="ewma")&(reference.interval_s==1)].set_index(["scenario","mode"])
    provenance=pd.read_csv(frozen/"provenance.csv").set_index("scenario")
    manifest,_=catalog_tables()
    source={r.Scenario_ID:r for r in manifest.itertuples(index=False)}
    rows,episodes_table,forensics,stats_table=[],[],[],[]
    for seed,(sid,item) in enumerate(provenance.iterrows(),42):
        rec=source[sid]
        if rec.sha256_clean!=item.archive_sha256:
            raise ValueError("lineage mismatch")
        frame=load_scenario(archive_path(rec))
        clock=frame.index.to_numpy(dtype=float)
        if not np.all(np.diff(clock)==1):
            raise ValueError("clock mismatch")
        x=frame.loc[:,list(CHANNELS)].to_numpy()
        stop=clock[0]+4+120*((clock[-1]-clock[0]-4)//120)
        limit=np.searchsorted(clock,stop,side="right")
        t=clock[4:limit]
        for mode,samples in perturb(x,seed):
            started=perf_counter_ns()
            baseline,robust=scoring(samples[:limit])
            elapsed=(perf_counter_ns()-started)/limit/1000
            state=np.array(list(states(robust)))
            choices={"reference":(baseline,np.array(list(decision_stream(baseline,5,2)))),
                     "robust_scale":(robust,np.array(list(decision_stream(robust,5,2)))),
                     "robust_stateful":(robust,np.isin(state,["ACTIVE_ALARM","RECOVERY"]).astype(int))}
            if mode=="clean":
                labels,issues=annotation(frame,rec)
                if issues:
                    raise ValueError(issues)
                onset,last=labels["onset_s"],labels["last_active_s"]
            truth=frame.label_anomaly.iloc[4:limit].to_numpy()
            for model,(score,flags) in choices.items():
                decision=pd.DataFrame(dict(decision_s=t,prediction=flags,truth=truth))
                m,alarms=assess(decision,onset,last,clock[0],stop,1)
                duration=sum((stop if b is None else b)-a for a,b in alarms)
                delay=m["alarm_delay_s"]
                rows.append(dict(scenario=sid,component=item.group,subtype=item.event,mode=mode,model=model,
                    duty_cycle=duration/(stop-t[0]),false_positive_knots=int(((truth==0)&(flags==1)).sum()),
                    inactive_knots=int((truth==0).sum()),alarm_duration_s=duration,
                    **m,**{f"within_{k}s":int(delay is not None and delay<=k) for k in DEADLINES}))
                starts=np.array([a for a,_ in alarms])
                for a,b in alarms:
                    episodes_table.append(dict(scenario=sid,mode=mode,model=model,start_s=a,reset_s=b,
                        active_at_start=onset is not None and onset<=a<=last,
                        observed_duration_s=(stop if b is None else b)-a))
                if model=="reference":
                    old=reference.loc[(sid,mode)]
                    if (m["false_episodes"],m["new_alert_detection"])!=(old.false_episodes,old.new_alert_detection):
                        raise ValueError(f"Frozen replay mismatch: {sid}/{mode}")
                    if delay is None and pd.notna(old.alarm_delay_s) or delay is not None and delay!=old.alarm_delay_s:
                        raise ValueError(f"Frozen delay mismatch: {sid}/{mode}")
                    if onset is not None:
                        active=(t>=onset)&(t<=last)
                        early=active&(t<=onset+5)
                        start_idx=np.searchsorted(t,onset)
                        already_open=bool(start_idx>0 and flags[start_idx-1] and flags[start_idx])
                        taxonomy=("within_5s" if delay is not None and delay<=5 else
                                  "late_threshold_start" if delay is not None else
                                  "open_at_onset_without_new_start" if already_open else
                                  "no_active_interval_threshold_start")
                        peak = np.argmax(score[early]) if early.any() else None
                        early_clock = t[early][peak] if peak is not None else None
                        dominant = None
                        if early_clock is not None:
                            idx=np.searchsorted(clock,early_clock)
                            dominant=CHANNELS[int(np.argmax(abs(samples[idx]-samples[idx-4])/
                                                            np.maximum(FLOORS,.005*abs(samples[0]))))]
                        forensics.append(dict(scenario=sid,subtype=item.event,mode=mode,onset_s=onset,
                            taxonomy=taxonomy,delay_s=delay,preexisting_alarm=already_open,
                            prior_false_starts=int((starts<onset).sum()), max_first_5s=float(max(score[early])) if early.any() else None,
                            max_while_active=float(max(score[active])) if active.any() else None,
                            peak_instantaneous_driver_at_early_ewma_peak=dominant))
            stats_table.append(dict(scenario=sid,mode=mode,combined_batch_us_per_row=elapsed,
                                    score_buffer_bytes_per_row=(2*8)))
    result=pd.DataFrame(rows)
    out.mkdir(parents=True)
    for name,table in (("scenario",result),("episodes",pd.DataFrame(episodes_table)),
                       ("forensics",pd.DataFrame(forensics)),("compute",pd.DataFrame(stats_table))):
        table.to_csv(out/(name+".csv"),index=False)
    for name,keys in (("comparison",["model","mode"]),("component",["model","mode","component"]),
                      ("subtype",["model","mode","subtype"])):
        summary=summarize(result,keys)
        extras=result.groupby(keys).agg(mean_duty=("duty_cycle","mean"),
             p90_delay_s=("alarm_delay_s",lambda a:a.quantile(.9)),max_delay_s=("alarm_delay_s","max"),
             false_positive_knots=("false_positive_knots","sum"),inactive_knots=("inactive_knots","sum"),
             **{f"within_{k}s":(f"within_{k}s","sum") for k in DEADLINES}).reset_index()
        summary.merge(extras,on=keys).to_csv(out/(name+".csv"),index=False)
    (out/"run.json").write_text(json.dumps(dict(scenarios=len(provenance),matched_reference_rows=len(provenance)*7,
        cadence_s=1,feature_span_s=4,stated_thresholds=[5,2],robust_trailing_samples=31,
        confirmation=2,recovery=3,hypothetical_stress=True,
        scope="Exploratory archive replay; no held-out tuning or field bounds."),indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    replay(a.base,a.out)
