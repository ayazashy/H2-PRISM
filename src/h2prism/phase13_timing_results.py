"""Audit and analyze the captured SID 59 command timing pair."""
import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
from scipy.io import loadmat

from .phase11 import BOUNDARIES, PHASE10, conservation, read_json
from .phase12_acceptance import audit, mat
from .phase12_pair import framework
from .phase13 import CAPTURE, sensor_values, sha256, prior_registry
from .phase13_command_delay import design


def aligned(control, shifted, samples):
    if not 0 < samples < len(control) or len(control)!=len(shifted):
        raise ValueError("invalid alignment")
    return shifted[samples:]-control[:-samples]


def delta_metrics(t,d):
    j=np.argmax(abs(d))
    return dict(peak_signed=float(d[j]),peak_abs=float(abs(d[j])),peak_s=float(t[j]),
                rmse=float(np.sqrt(np.mean(d*d))),absolute_integral=float(trapezoid(abs(d),x=t)),
                median_tail=float(np.median(d[-5000:])),final=float(d[-1]))


def step_time(t,x):
    return float(t[np.flatnonzero(x>(x[0]+x[-1])/2)[0]])


def analyze(work,out):
    root=work/"phase13_command_delay_01"
    cases=("normal","outlet_opening")
    receipts={}
    for case in cases:
        receipt=audit(root,None,work/"phase11_cases/step_0.2",case,design())
        saved=read_json(root/case/"command_timing_acceptance.json")
        if receipt["capture_hashes"]!=saved["capture_hashes"] or receipt["classification"]!="ACCEPTED":
            raise ValueError(f"Acceptance mismatch: {case}")
        receipts[case]=receipt
    captures=[mat(root/c/"center_raw.mat") for c in cases]
    t=captures[0]["sensors"]["pressure_sensor1"]["time"]
    clocks=[{r["path"]:r["values"] for r in c["logSeries"]} for c in captures]
    sensor=[sensor_values(c,t) for c in captures]
    history=[conservation(c,read_json(PHASE10),.2)[0] for c in captures]
    onset=[step_time(t,r["PS_Step/O"]) for r in clocks]
    step=round((onset[1]-onset[0])/.2)
    cut=np.searchsorted(t,onset[0])
    paths=("PS_Step/O","Pressure_Source_G3/P","Pressure_Source_G3/mdot_A","Pressure_Source_G3/mdot_B",
           "Pressure_Source_G3/A/p","Pressure_Source_G3/B/p")
    physical={}
    for c,logs,on in zip(cases,clocks,onset):
        k=np.searchsorted(t,on)
        physical[c]={"emitted_s":on,"received_s":step_time(t,logs["Pressure_Source_G3/P"]),
                     "before_at_after":{p:logs[p][[k-1,k,k+1]].tolist() for p in paths},
                     "final_storage_kg":float(history[cases.index(c)].storage_kg.iloc[-1])}
    rows=[]
    for name in CAPTURE:
        a,b=(r[name] for r in sensor)
        d=b-a
        ea=aligned(a,b,step)
        onsets=[]
        for data,on in zip((a,b),onset):
            j=np.searchsorted(t,on)
            # Gates only the descriptive response marker, not formal inference.
            threshold=max(float(np.max(abs(np.diff(data[j-5:j]))))*5,1e-9)
            k=np.flatnonzero(abs(data[j:]-data[j-1])>threshold)
            onsets.append(float(t[j+k[0]]-on) if len(k) else None)
        rows.append(dict(sensor=name,unit="MPa" if name.startswith("PS") else "kg/s",
                         pre_max=float(abs(d[:cut]).max()),control_response_delay_s=onsets[0],
                         shifted_response_delay_s=onsets[1],
                         **{f"clock_{k}":v for k,v in delta_metrics(t[cut:],d[cut:]).items()},
                         **{f"event_{k}":v for k,v in delta_metrics(t[cut:-step]-onset[0],ea[cut:]).items()}))
    flows=[]
    for name in BOUNDARIES:
        d=clocks[0][name+"/mdot_A"]-clocks[1][name+"/mdot_A"]
        flows.append(dict(boundary=name,**delta_metrics(t,d),signed_integral_kg=float(trapezoid(d,x=t))))
    storage=history[1].storage_kg.to_numpy()-history[0].storage_kg.to_numpy()
    physical["storage_delta_kg"]=delta_metrics(t,storage)
    del captures,history
    registry=read_json(prior_registry())["registry"]
    earlier=read_json(work.parent/"outputs/phase13_recovered_final/evidence.json")["accepted"]
    folders={"SID213":work/"phase12_sdi_retry_01","SID312":work/"final_research_matrix/sid312",
             "SID215":work/"final_research_matrix/sid215","PRESSURE":work/"phase13_02/pressure_rival",
             "ALT_PROFILE":work/"phase13_02/alternate_profile"}
    prior_keys={"SID213":"A","SID312":"sid312","SID215":"sid215","PRESSURE":"pressure_rival","ALT_PROFILE":"alternate_profile"}
    pairs={}
    for label,folder in folders.items():
        pair=[]
        for c in cases:
            path=folder/c/"center_raw.mat"
            if label=="ALT_PROFILE" and c=="outlet_opening":
                path=work/"phase13_alternate_retry_02"/c/"center_raw.mat"
            key=prior_keys[label]+":"+c
            rec=earlier.get(key) or next(r for r in registry if r["id"]==key)
            expected=rec.get("capture_hashes") or rec["receipt"]["capture_hashes"]
            if sha256(path)!=expected["center_raw.mat"]:
                raise ValueError(f"Frozen capture changed: {key}")
            pair.append(sensor_values(loadmat(path,simplify_cells=True,variable_names=["sensors"]),t))
        pairs[label]=pair
    names=list(CAPTURE)
    scale=np.array([np.sqrt(np.mean(pairs["SID213"][0][n][t<1000]**2)) for n in names])
    later=np.searchsorted(t,1000)
    count=601
    signatures={name:np.column_stack([(b[n]-a[n])[later:later+count] for n in names])/scale
                for name,(a,b) in pairs.items()}
    signatures["NORMAL"]=np.zeros((count,len(names)))
    signatures["NOMINAL_TRANSIENT"]=np.column_stack([
        sensor[0][n][cut:cut+count]-sensor[0][n][cut-1] for n in names])/scale
    signatures["TIMING_CLOCK"]=np.column_stack([
        (sensor[1][n]-sensor[0][n])[cut:cut+count] for n in names])/scale
    signatures["TIMING_EVENT"]=np.column_stack([
        aligned(sensor[0][n],sensor[1][n],step)[cut:cut+count] for n in names])/scale
    subsets={"all":names,"pressure":[n for n in names if n.startswith("PS")],
             "flow":[n for n in names if n.startswith("MFS")],
             **{n:[n] for n in names},**{"omit_"+n:[m for m in names if m!=n] for n in names}}
    distances=[]
    for seconds in (1,5,10,30,60,120):
        stop=round(seconds/.2)+1
        for a,b in combinations(signatures,2):
            for subset,cols in subsets.items():
                d=(signatures[a]-signatures[b])[:stop,[names.index(n) for n in cols]]
                distances.append(dict(a=a,b=b,seconds=seconds,subset=subset,
                    rms=float(np.sqrt(np.mean(d*d))),box_transition=float(abs(d).max())))
    decisions={c:framework(t,x,on,r["capture_hashes"]["center_raw.mat"],
                 ground_truth="Controlled SID 59 timing pilot "+c, extra_hypotheses=("COMMAND_TIMING_SID59",))
               for c,x,on,r in zip(cases,sensor,onset,receipts.values())}
    sensitivity=[dict(hypothetical_clock_halfwidth_s=x,
                      timing_intervals_overlap=2*x>=onset[1]-onset[0])
                 for x in (0,.1,.2,.4,.5,1)]
    out.mkdir(parents=True)
    for name,data in (("sensor_timing",rows),("boundary_flows",flows),("pairwise",distances),
                      ("hypothetical_clock",sensitivity)):
        pd.DataFrame(data).to_csv(out/(name+".csv"),index=False)
    (out/"evidence.json").write_text(json.dumps(dict(accepted=receipts,physical=physical,
        formal=decisions,normalizers=dict(zip(names,scale))),indent=2,default=lambda x:x.tolist()),encoding="utf8")
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(3,1,sharex=True,figsize=(8,7),layout="constrained")
    v=(t>=24)&(t<=40)
    for i,c in enumerate(cases):
        label=("Control","Timing intervention")[i]
        axes[0].step(t[v],clocks[i]["Pressure_Source_G3/P"][v]/1e6,where="post",label=label)
        axes[1].plot(t[v],clocks[i]["Pressure_Source_G3/mdot_A"][v],label=label)
        axes[2].plot(t[v],sensor[i]["PS1"][v],label=label)
    for ax,label in zip(axes,("Received command (MPa)","Flow into SID 55 A (kg/s)","PS1 (MPa)")):
        ax.set_ylabel(label)
    axes[0].legend()
    axes[-1].set_xlabel("Saved time (s)")
    fig.savefig(out/"command_timing.png",dpi=220)
    plt.close(fig)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("work",type=Path)
    parser.add_argument("output",type=Path)
    a=parser.parse_args()
    analyze(a.work,a.output)
