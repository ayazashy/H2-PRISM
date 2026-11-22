"""Aggregate frozen causal decisions into alert episodes without refitting."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data.loader import load_scenario
from .simnet_study import annotation, archive_path, catalog_tables


def episodes(clock, positive):
    """Open at the first positive; the first negative resets immediately."""
    clock, positive = np.asarray(clock), np.asarray(positive)
    if not len(clock) or not np.isfinite(clock).all() or not np.all(np.diff(clock)>0):
        raise ValueError("non-increasing or empty decision clock")
    if len(clock)!=len(positive) or not np.isin(positive,[0,1]).all():
        raise ValueError("invalid predictions")
    starts = np.flatnonzero(np.diff(np.r_[0,positive,0])==1)
    stops = np.flatnonzero(np.diff(np.r_[0,positive,0])==-1)
    return [(clock[a],clock[b] if b<len(clock) else None) for a,b in zip(starts,stops)]


def assess(rows, onset, last, start, stop, stride):
    rows = rows.sort_values("decision_s")
    clock = rows.decision_s.to_numpy()
    if clock[0]!=start+4 or clock[-1]!=start+4+stride*((stop-start-4)//stride) or not np.all(np.diff(clock)==stride):
        raise ValueError("incomplete frozen schedule")
    active = (clock>=onset)&(clock<=last) if onset is not None else np.zeros(len(clock),dtype=bool)
    if not np.array_equal(rows.truth.to_numpy(),active):
        raise ValueError("frozen target disagrees with archive")
    alarms = episodes(clock,rows.prediction.to_numpy())
    alert_times = [a for a,_ in alarms]
    true_start = [a for a in alert_times if onset is not None and onset<=a<=last]
    positive = clock[active & (rows.prediction.to_numpy()==1)]
    active_exposure = max(0,min(clock[-1],last+1)-max(clock[0],onset)) if onset is not None else 0
    inactive_hours = float((clock[-1]-clock[0]-active_exposure)/3600)
    return dict(false_episodes=len(alarms)-len(true_start),episodes=len(alarms),
                inactive_hours=inactive_hours,event=int(onset is not None),
                new_alert_detection=int(bool(true_start)),active_positive_detection=int(bool(len(positive))),
                alarm_delay_s=float(true_start[0]-onset) if true_start else None,
                active_positive_delay_s=float(positive[0]-onset) if len(positive) else None), alarms


def summarize(table,keys):
    t = table.groupby(keys,dropna=False).agg(
        scenarios=("scenario","size"),events=("event","sum"),false_episodes=("false_episodes","sum"),
        inactive_hours=("inactive_hours","sum"),new_alert_detections=("new_alert_detection","sum"),
        active_positive_detections=("active_positive_detection","sum"),
        median_alarm_delay_s=("alarm_delay_s","median")).reset_index()
    t["missed_events"] = t.events-t.new_alert_detections
    t["false_episodes_per_inactive_hour"] = t.false_episodes/t.inactive_hours.where(t.inactive_hours>0)
    return t


def main(frozen,out):
    registry = pd.read_csv(frozen/"provenance.csv").set_index("scenario")
    predictions = pd.read_csv(frozen/"predictions.csv")
    method = json.loads((frozen/"method.json").read_text(encoding="utf8"))
    manifest,_ = catalog_tables()
    source = {r.Scenario_ID:r for r in manifest.itertuples(index=False)}
    verified = {}
    for sid,row in registry.iterrows():
        rec = source[sid]
        if row.archive_sha256 != rec.sha256_clean:
            raise ValueError("archive hash mismatch")
        frame = load_scenario(archive_path(rec))
        labels,issues = annotation(frame,rec)
        if issues:
            raise ValueError(issues)
        verified[sid] = (labels["onset_s"],labels["last_active_s"],frame.index[0],frame.index[-1])
    if set(predictions.scenario)!=set(verified):
        raise ValueError("scenario inventory differs")
    records, alarm_log = [],[]
    expected = set(verified)
    for (model,mode),variant in predictions.groupby(["model","mode"]):
        if set(variant.scenario)!=expected:
            raise ValueError("model/stress scenario coverage differs")
        for sid,rows in variant.groupby("scenario"):
            row = registry.loc[sid]
            if set(rows.group)!={row.group}:
                raise ValueError("unexpected component")
            outcome,alarms = assess(rows,*verified[sid],method["stride_seconds"])
            records.append(dict(model=model,mode=mode,scenario=sid,component=row.group,
                                subtype=row.event,**outcome))
            onset,last,_,_ = verified[sid]
            for a,b in alarms:
                alarm_log.append(dict(model=model,mode=mode,scenario=sid,alarm_start_s=a,
                                      reset_s=b,false_at_start=onset is None or not onset<=a<=last))
    result = pd.DataFrame(records)
    out.mkdir(parents=True)
    result.to_csv(out/"per_scenario.csv",index=False)
    pd.DataFrame(alarm_log).to_csv(out/"episodes.csv",index=False)
    for name,keys in (("overall",["model","mode"]),("per_component",["model","mode","component"]),
                      ("by_subtype",["model","mode","subtype"])):
        summarize(result,keys).to_csv(out/f"{name}.csv",index=False)
    delays = result[result.alarm_delay_s.notna()].groupby(["model","mode"]).alarm_delay_s.quantile(
        [.0,.25,.5,.75,1]).rename("delay_s")
    delays.to_csv(out/"delay_quantiles.csv")
    totals = summarize(result,["model","mode"])
    stress = totals.merge(totals[totals["mode"]=="clean"].drop(columns="mode"),on="model",suffixes=("","_clean"))
    stress["extra_false_episodes"] = stress.false_episodes-stress.false_episodes_clean
    stress["extra_missed_events"] = stress.missed_events-stress.missed_events_clean
    stress.to_csv(out/"stress_deltas.csv",index=False)
    (out/"audit.json").write_text(json.dumps(dict(
        hashes={n:hashlib.sha256((frozen/n).read_bytes()).hexdigest()
                for n in ("provenance.csv","method.json","predictions.csv")},
        scenarios=len(verified),decision_rows=len(predictions),components=int(result.component.nunique()),
        policy="Open on positive; reset on first negative. An episode starting inactive is false even if it persists into the event.",
        strict_event_credit="Starts during the annotated interval; separately report active positives.",
        exposure="Verified inactive duration between first and last frozen decision, excludes warm-up and unobserved tail.",
        independently_verified_families={k:0 for k in ("NORMAL","LEAK","FAULT","DELAY")},
        diagnostic_splits={"historical_four_class":"rejected: held-out FAULT/DELAY or NORMAL components remove classes from training",
                            "controlled_localization":"rejected: all 10 captures share one Center family",
                            "causal_binary":"exploratory: archived grouped playback, ancestry unresolved",
                            "external":"blocked: no untouched qualified external partition"}),indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("frozen",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    main(a.frozen,a.output)
