"""Descriptive alarm-policy contrasts on frozen binary predictions."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .phase13_alarms import episodes


def debounce(values, open_count, reset_count):
    state, consecutive = 0,0
    result = []
    for value in values:
        consecutive = 0 if value == state else consecutive+1
        if consecutive >= (reset_count if state else open_count):
            state,consecutive = int(value),0
        result.append(state)
    return result


def analyze(replay, alarm_reference, output):
    scenarios = pd.read_csv(replay/"provenance.csv").set_index("scenario")
    frozen = pd.read_csv(replay/"predictions.csv")
    baseline = pd.read_csv(alarm_reference/"overall.csv").set_index(["model","mode"])
    rows = []
    for (model,mode,sid), table in frozen.groupby(["model","mode","scenario"]):
        table = table.sort_values("decision_s")
        clock = table.decision_s.to_numpy()
        if not np.all(np.diff(clock)==120):
            raise ValueError("invalid clock")
        start,end = scenarios.loc[sid,["onset_s","last_active_s"]]
        for open_count,reset_count in ((1,1),(2,1),(1,2),(2,2)):
            alarms = episodes(clock,debounce(table.prediction,open_count,reset_count))
            true = [a for a,_ in alarms if start<=a<=end]
            false = [(a,b) for a,b in alarms if not start<=a<=end]
            delay = min(true)-start if true else np.nan
            false_duration = sum((clock[-1] if b is None else b)-a for a,b in false)
            duration = sum((clock[-1] if b is None else b)-a for a,b in alarms)
            rows.append(dict(model=model,mode=mode,scenario=sid,open_count=open_count,reset_count=reset_count,
                             events=int(pd.notna(start)),detected=int(bool(true)),delay_s=delay,
                             false_episodes=len(false),false_episode_duration_s=false_duration,
                             alarm_duration_s=duration,observed_s=clock[-1]-clock[0],
                             **{f"within_{s}s":int(delay<=s) for s in (120,300,600,1800)}))
    data = pd.DataFrame(rows)
    summary = data.groupby(["model","mode","open_count","reset_count"]).sum(numeric_only=True).drop(columns="delay_s")
    for idx,r in baseline.iterrows():
        nominal = summary.loc[(*idx,1,1)]
        if (r.false_episodes,r.new_alert_detections)!=(nominal.false_episodes,nominal.detected):
            raise ValueError("baseline alarm replay differs")
    summary["duty_cycle"] = summary.alarm_duration_s/summary.observed_s
    output.mkdir(parents=True)
    data.to_csv(output/"alarm_policy_cases.csv",index=False)
    summary.to_csv(output/"alarm_policy_summary.csv")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ("replay","alarm_reference","output"):
        p.add_argument(arg,type=Path)
    analyze(**vars(p.parse_args()))
