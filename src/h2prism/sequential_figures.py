"""Figures and machine-readable claim coverage for sequential replay."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def render(root):
    metrics=pd.read_csv(root/"summary.csv")
    clean=metrics[metrics["mode"]=="clean"]
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout="constrained")
    for (name,table),color in zip(clean.groupby("detector"),("#143253","#078781")):
        axes[0].plot(table.interval_s,table.within_10s,"o-",label=name,color=color)
        axes[1].scatter(table.false_episodes_per_inactive_hour,table.within_10s,label=name,color=color)
        for row in table.itertuples():
            axes[1].annotate(f"{row.interval_s}s",(row.false_episodes_per_inactive_hour,row.within_10s),
                             xytext=(3,4),textcoords="offset points",fontsize=7)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Decision cadence (s)")
    axes[1].set_xlabel("False starts per inactive archive hour")
    for ax in axes:
        ax.set_ylabel("New detections within 10 s (of 48)")
        ax.legend()
    fig.savefig(root/"cadence_tradeoff.png",dpi=220)
    plt.close(fig)
    geometry=pd.read_csv(root/"timing_geometry.csv")
    locations={"A","sid312","sid215"}
    g=geometry[(geometry.seconds==30)&geometry.a.isin(locations)&geometry.b.isin(locations)]
    fig,axes=plt.subplots(1,3,figsize=(11,3.5),layout="constrained")
    for ax,subset in zip(axes,("all","pressure","flow")):
        for (a,b),table in g[g.subset==subset].groupby(["a","b"]):
            ax.plot(table.hypothetical_offset_s,table.min_rms,"o-",label=f"{a} / {b}")
        ax.set_title(subset)
        ax.set_xlabel("Relative offset bound (s)")
    axes[0].set_ylabel("Minimum normalized RMS")
    axes[-1].legend(fontsize=8)
    fig.savefig(root/"location_geometry.png",dpi=220)
    plt.close(fig)
    fields=[
        ("Fast detection","New episode starts within fixed deadlines","EXPLORATORY","summary.csv"),
        ("Detection delay","First in-event new start minus archived onset","EXPLORATORY","delay_quantiles.csv"),
        ("False-alarm burden","New inactive starts per verified common exposure hour","EXPLORATORY","summary.csv"),
        ("Binary classification","Frozen RF and SVM operational comparator","EXPLORATORY","../phase13_alarm_validation/report.md"),
        ("Accuracy","Multiclass fraction correct on untouched independent roots","NOT_ESTABLISHED",None),
        ("Balanced accuracy","Class-average recall of frozen binary replay","EXPLORATORY","../phase13_causal_validation/metrics.csv"),
        ("Macro F1","Class-average F1 of frozen binary replay","EXPLORATORY","../phase13_causal_validation/metrics.csv"),
        ("Multiclass diagnosis","Qualified mechanism recognition on independent roots","BLOCKED",None),
        ("Calibration","Observed outcomes versus predicted probabilities","NOT_ESTABLISHED",None),
        ("Selective risk","Specific-decision error at matched coverage","NOT_ESTABLISHED",None),
        ("Decision coverage","Qualified specific decisions per accepted capture","ESTABLISHED","../phase13_integrated_timing/evidence.json"),
        ("Distinguishability","Range of residual RMS over allowed offsets","EXPLORATORY","timing_geometry.csv"),
        ("Formal hypothesis exclusion","Qualified disjoint hypothesis sets","ESTABLISHED","../phase13_integrated_timing/evidence.json"),
        ("Timing uncertainty","Hypothetical nuisance-offset set","EXPLORATORY","timing_geometry.csv"),
        ("Localization","Conditional template ranks with all candidates retained","EXPLORATORY","location_candidates.csv"),
        ("Sensor ablation","Residual geometry after sensor omission","EXPLORATORY","timing_geometry.csv"),
        ("Noise robustness","Assumed stress effects on repeated alarm starts","EXPLORATORY","summary.csv"),
        ("Numerical integrity","Audit of accepted controlled run clocks and physics","ESTABLISHED","../phase13_integrated_timing/evidence.json"),
        ("Independence","Verified independent source roots","NOT_ESTABLISHED",None),
        ("Cross-topology transfer","Untouched independent topology assessment","BLOCKED",None),
        ("Industrial readiness","Field-qualified detection and diagnosis","BLOCKED",None),
    ]
    scored = clean[["detector","interval_s","within_10s","new_alert_detections",
                    "false_episodes_per_inactive_hour","median_alarm_delay_s"]].to_dict("records")
    actual = {
        "Fast detection": scored, "Detection delay": scored, "False-alarm burden": scored,
        "Binary classification": {"forest_events":48,"linear_svm_events":37},
        "Decision coverage": "0/12 specific", "Formal hypothesis exclusion":"0 qualified exclusions",
        "Localization": "L0; all three remain candidates", "Numerical integrity":"12 accepted Center captures",
        "Independence":"zero verified families",
    }
    rows=[dict(metric=n,definition=d,validity=s,artifact=a,
               independent_units=0,population="archive replay or one Center source family",
               result=actual.get(n, "see linked numerical table" if a else None),
               data_source=a,
               blocker="No verified independent roots or field-qualified uncertainty") for n,d,s,a in fields]
    (root/"completeness.json").write_text(json.dumps(rows,indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    render(p.parse_args().root)
