"""Render forensic and robustness figures from the completed replay."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def render(root):
    r=pd.read_csv(root/"comparison.csv")
    clean=r[r["mode"]=="clean"]
    fig,ax=plt.subplots(figsize=(7,4),layout="constrained")
    deadlines=[1,2,5,10,30,60,120]
    for row,color in zip(clean.itertuples(),("#143253","#078781","#3678af")):
        ax.step(deadlines,[getattr(row,f"within_{d}s") for d in deadlines],where="post",
                label=row.model,color=color)
    ax.set(xscale="log",xlabel="Deadline after archived onset (s)",ylabel="New event detections (of 48)")
    ax.set_xticks(deadlines,deadlines)
    ax.legend()
    fig.savefig(root/"deadline_recall.png",dpi=220)
    plt.close(fig)
    r=r[r["mode"].isin(["clean","white","correlated"])]
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout="constrained")
    for ax,value,label in zip(axes,("mean_duty","false_episodes_per_inactive_hour"),
                             ("Mean alarm duty fraction","False episodes per inactive archive hour")):
        data=r.pivot(index="mode",columns="model",values=value).loc[["clean","white","correlated"]]
        data.plot.bar(ax=ax,color=["#143253","#078781","#3678af"])
        ax.set_ylabel(label)
        ax.tick_params(axis="x",rotation=0)
        ax.set_xlabel("")
    fig.savefig(root/"noise_failure.png",dpi=220)
    plt.close(fig)
    p=pd.read_csv(root/"prefix_ranks.csv")
    p=p[(p["query"]=="alternate_profile")&(p.scope=="after_startup")&
        (p.hypothetical_offset_s==1)&p.subset.isin(["all","pressure","flow"])]
    fig,ax=plt.subplots(figsize=(7,4),layout="constrained")
    for subset,table in p.groupby("subset"):
        ax.plot(table.window_s,table.margin,"o-",label=subset)
    ax.set(yscale="log",xlabel="Evidence acquired after causal alert (s)",
           ylabel="Normalized RMS margin to runner-up")
    ax.legend()
    fig.savefig(root/"prefix_margin.png",dpi=220)
    plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    render(p.parse_args().root)
