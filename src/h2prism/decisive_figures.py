"""Summarize decisive sprint trade-offs and existing causal ranking ablations."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def render(base,out):
    r=pd.read_csv(out/"comparison.csv")
    refs=pd.read_csv(base/"outputs/phase13_integrated_timing/alarm_policy_summary.csv")
    refs=refs[(refs.open_count==1)&(refs.reset_count==1)&refs.model.isin(
        ["random_forest","linear_svm","majority","always_event"])]
    refs=refs.rename(columns={"detected":"new_alert_detections","duty_cycle":"mean_duty"})
    refs["false_episodes_per_inactive_hour"]=refs.false_episodes/65.62833333333333
    r["cadence_s"]=1
    refs["cadence_s"]=120
    table=pd.concat([r,refs],ignore_index=True,sort=False)
    table["validity"]="EXPLORATORY"
    table["training_provenance"]=table.cadence_s.map(
        {1:"predefined causal scoring; no fit",120:"previously frozen component replay"})
    table.to_csv(out/"comparison_matrix.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout="constrained")
    prompts=(("clean","within_5s","New alarms within 5 s"),("correlated","new_alert_detections","New alarms under correlated noise"))
    for ax,(mode,field,title) in zip(axes,prompts):
        for row in r[r["mode"]==mode].itertuples():
            x=row.false_episodes_per_inactive_hour
            y=getattr(row,field)
            ax.scatter(x,y,label=row.model)
        ax.set(xlabel="False starts per inactive archive hour",ylabel=title)
        ax.legend(fontsize=8)
    fig.savefig(out/"tradeoffs.png",dpi=220)
    plt.close(fig)

    ranks=pd.read_csv(out/"delayed_prefix_ranks.csv")
    q=ranks[(ranks["query"]=="alternate_profile")&(ranks.scope=="after_startup")].copy()
    keys=["alert_delay_s","window_s","hypothetical_offset_s"]
    full=q[q.subset=="all"][keys+["rank","margin"]]
    restored=q.merge(full,on=keys,suffixes=("","_restored"),validate="many_to_one")
    restored["margin_delta_on_restore"]=restored.margin_restored-restored.margin
    restored["top_candidate_changed"]=restored["rank"].str.split().str[0]!=restored.rank_restored.str.split().str[0]
    restored.to_csv(out/"sensor_restore.csv",index=False)
    g=q[(q.alert_delay_s==0)&(q.window_s==30)&(q.hypothetical_offset_s==1)&q.subset.str.startswith("omit_")]
    fig,ax=plt.subplots(figsize=(8,4),layout="constrained")
    ax.bar(g.subset.str.removeprefix("omit_"),g.margin,color="#24756d")
    ax.set(xlabel="Sensor omitted",ylabel="Normalized margin to runner-up",
           title="Alternate SID 213 at 30 s · assumed ±1 s offset")
    fig.savefig(out/"sensor_leverage.png",dpi=220)
    plt.close(fig)
    evidence={
      "query":"alternate-profile SID 213; held out from template library, same Center family",
      "timing":"causal alert at 1000 s; template offset 0, ±1 and ±2 s; native 0.2 s resolution",
      "available":"paired canonical sensor prefixes; one differing operating profile",
      "missing":"qualified simultaneous enclosures and independent producing histories",
      "location_candidates":["SID213","SID312","SID215"],
      "pressure_and_timing_rivals_retained":True,
      "qualified_decision":"UNRESOLVED / L0",
      "added_value":"NO DEMONSTRATED FORMAL DECISION IMPROVEMENT",
      "restoration_rows":len(restored),
      "top_rank_changes":int(restored.top_candidate_changed.sum()),
    }
    (out/"evidence_sufficiency.json").write_text(json.dumps(evidence,indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    render(a.base,a.out)
