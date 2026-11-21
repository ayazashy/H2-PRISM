"""Render NRES comparisons from saved numeric results."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import loadmat


def render(base,out):
    timing=pd.read_csv(out/"timing.csv")
    transfer=pd.read_csv(out/"transfer.csv")
    geo=pd.read_csv(out/"location_geometry.csv")
    neg=pd.read_csv(out/"negative_controls.csv")
    fig,axes=plt.subplots(1,2,figsize=(9,4),layout="constrained")
    for method,r in timing[timing.subset=="all"].groupby("method"):
        axes[0].plot(r.hypothetical_bound_s,r.rms,"o-",label=method)
    axes[0].set(xlabel="Assumed shared offset bound (s)",ylabel="Normalized RMS",yscale="log")
    axes[0].legend(ncol=2,fontsize=8)
    selected=transfer[(transfer.subset=="all")&(transfer.bound_s==1)&(transfer["rank"]==1)]
    for method,r in selected.groupby("method"):
        axes[1].plot(r.seconds,r.margin,"o-",label=method)
    axes[1].set(xlabel="Observed prefix (s)",ylabel="Top-to-runner-up margin")
    axes[1].legend(ncol=2,fontsize=8)
    fig.savefig(out/"timing_and_baselines.png",dpi=220)
    plt.close(fig)
    rows=geo[(geo.seconds==30)&(geo.bound_s==1)&(geo.method=="B4")
             &geo.a.str.startswith("SID")&geo.b.str.startswith("SID")]
    labels=["SID213","SID312","SID215"]
    fig,axes=plt.subplots(1,3,figsize=(10,3.5),layout="constrained")
    for ax,sub in zip(axes,("all","pressure","flow")):
        m=np.zeros((3,3))
        for r in rows[rows.subset==sub].itertuples():
            i,j=labels.index(r.a),labels.index(r.b)
            m[i,j]=m[j,i]=r.rms
        im=ax.imshow(m,cmap="Blues")
        for i,j in np.ndindex(m.shape):
            ax.text(j,i,f"{m[i,j]:.3g}",ha="center",va="center",
                    color="white" if m[i,j]>.55*m.max() else "black",fontsize=8)
        ax.set_xticks(range(3),labels,rotation=30)
        ax.set_yticks(range(3),labels)
        ax.set_title(sub)
        fig.colorbar(im,ax=ax,shrink=.6)
    fig.savefig(out/"location_separation.png",dpi=220)
    plt.close(fig)
    s=transfer[(transfer.seconds==30)&(transfer.bound_s==1)&(transfer["rank"]==1)&
               (transfer.subset.str.startswith("omit_")|transfer.subset.isin(["all","pressure","flow"]))]
    fig,ax=plt.subplots(figsize=(10,4),layout="constrained")
    s[s.method.isin(["B3","B4"])].pivot(index="subset",columns="method",values="margin").plot.bar(
        ax=ax,color=["#234b6e","#138077"])
    ax.set(ylabel="Top-to-runner-up margin",xlabel="Sensor subset")
    fig.savefig(out/"sensor_ablation.png",dpi=220)
    plt.close(fig)
    s=neg[(neg.bound_s==1)&(neg["query"]=="ALT")].copy()
    fig,ax=plt.subplots(figsize=(9,4),layout="constrained")
    s.pivot(index="mode",columns="method",values="margin").plot.bar(ax=ax,color=["#234b6e","#138077"])
    ax.set(ylabel="Normalized top-to-runner-up margin",xlabel="Hypothetical perturbation")
    fig.savefig(out/"stress_comparison.png",dpi=220)
    plt.close(fig)
    root=base/"work/phase13_alternate_retry_02/outlet_opening"
    control=base/"work/phase13_02/alternate_profile/normal"
    raw=[loadmat(f/"center_raw.mat",simplify_cells=True,variable_names=["sensors"])["sensors"]
         for f in (control,root)]
    fig,axes=plt.subplots(2,2,figsize=(9,5),layout="constrained",sharex=True)
    for row,key,unit in zip(axes,("pressure_sensor1","flow_sensor3"),("MPa","kg/s")):
        x=raw[0][key]["time"]
        view=(x>=995)&(x<=1030)
        a,b=[v[key]["values"] for v in raw]
        row[0].plot(x[view],a[view],label="Matched control")
        row[0].plot(x[view],b[view],label="Observed")
        row[0].set_ylabel(f"Raw ({unit})")
        row[1].plot(x[view],(b-a)[view],color="#138077")
        row[1].set_ylabel(f"Residual ({unit})")
    axes[0,0].legend(fontsize=8)
    for ax in axes[-1]:
        ax.set_xlabel("Saved clock (s)")
    fig.savefig(out/"raw_and_residual.png",dpi=220)
    plt.close(fig)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    render(a.base,a.out)
