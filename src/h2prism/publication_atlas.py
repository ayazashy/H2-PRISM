"""Render the publication atlas from checksum-frozen research evidence."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import loadmat


NAVY,TEAL,BLUE,SLATE,ORANGE,RED="#10263E","#007F86","#356CB1","#64748B","#B56A35","#A33F43"
STM=("reference","accumulator","two_stage","cusum")
TITLES={"reference":"EWMA","accumulator":"Accumulator","two_stage":"Two-stage","cusum":"Capped CUSUM"}
LOC=("SID213","SID312","SID215")


SUPPLEMENTAL_INPUTS = {
    "outputs/phase11-final/mass_balance.csv": "f6b742895d1aab706b5e575dc9a3b1103dff7e58b651820d960da7b88b5f7581",
    "outputs/phase12-paired-results/observation_windows.csv": "385591b7de24b72a756efdaaed1f5fd2a4b38691ec55d742ac91fd7c47b285ff",
}

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def verify(repo,workspace,manifest):
    for scope,root in (("repository",repo),("workspace",workspace)):
        for name,expected in manifest["sha256"][scope].items():
            if digest(root/name)!=expected:
                raise ValueError(f"frozen checksum differs: {scope}/{name}")
    return sum(len(v) for v in manifest["sha256"].values())


def deadline_curve(delays,denominator):
    x=np.sort(np.asarray(delays,dtype=float))
    if not denominator or len(x)>denominator or not np.isfinite(x).all() or (x<0).any():
        raise ValueError("invalid event latency population")
    return np.r_[0,x],np.arange(len(x)+1)/denominator


class Atlas:
    def __init__(self,root,frozen,out):
        self.root,self.out=root,out
        self.frozen={**frozen["sha256"]["workspace"], **SUPPLEMENTAL_INPUTS}
        self.items=[]
        self.sources=set()
        self.figures=[]
        plt.rcParams.update({"font.family":"DejaVu Sans","font.size":9,
            "axes.labelcolor":NAVY,"text.color":NAVY,"axes.edgecolor":SLATE,
            "axes.spines.top":False,"axes.spines.right":False,
            "axes.grid":True,"grid.alpha":.20,"axes.axisbelow":True,
            "svg.hashsalt":"h2prism-publication-v1","pdf.fonttype":42})

    def source(self,name):
        if name not in self.frozen:
            raise ValueError(f"plot input not frozen: {name}")
        if name in SUPPLEMENTAL_INPUTS and digest(self.root/name) != SUPPLEMENTAL_INPUTS[name]:
            raise ValueError(f"supplemental checksum differs: {name}")
        self.sources.add(name)
        return self.root/name

    def frame(self,name):
        return pd.read_csv(self.source("outputs/"+name))

    def obj(self,name):
        return read(self.source("outputs/"+name))

    def capture(self,frozen,key,fields):
        case=frozen["captures"][key]["case_path"]
        return loadmat(self.source(case+"/center_raw.mat"),simplify_cells=True,variable_names=fields)

    def register(self,identifier,title,files,caption):
        if any(item["id"]==identifier for item in self.items):
            raise ValueError("duplicate research identifier")
        self.items.append(dict(id=identifier,title=title,files=files,caption=caption,
           sources={p:self.frozen[p] for p in sorted(self.sources)},
           exports={p:digest(self.out/p) for p in files}))
        self.sources.clear()

    def table(self,identifier,title,frame,caption):
        csv_path=f"tables/{identifier}.csv"
        md_path=f"tables/{identifier}.md"
        frame.to_csv(self.out/csv_path,index=False)
        # Keep the CSV values at full precision; Markdown is for presentation.
        columns=list(map(str,frame.columns))
        body=["| "+" | ".join(columns)+" |","| "+" | ".join(["---"]*len(columns))+" |"]
        def cell(x):
            if pd.isna(x):
                return "—"
            return f"{x:.6g}" if isinstance(x,float) else str(x).replace("|","\\|")
        for row in frame.itertuples(index=False,name=None):
            body.append("| "+" | ".join(map(cell,row))+" |")
        (self.out/md_path).write_text(f"# {identifier} — {title}\n\n{caption}\n\n"+"\n".join(body)+"\n",encoding="utf-8")
        self.register(identifier,title,[csv_path,md_path],caption)

    def figure(self,identifier,title,fig,caption,poster=False):
        for panel,ax in zip("ABCDEFGHIJKLM",fig.axes):
            if not ax.get_label()=="<colorbar>":
                ax.text(.0,1.035,panel,transform=ax.transAxes,fontweight="bold",fontsize=10,va="bottom")
        fig.suptitle(title,x=.03,ha="left",fontweight="bold",fontsize=13)
        fig.canvas.draw()
        bounds=fig.get_tightbbox(fig.canvas.get_renderer()).extents
        w,h=fig.get_size_inches()
        if not np.isfinite(bounds).all() or bounds[0]<-.03 or bounds[1]<-.03 or bounds[2]>w+.03 or bounds[3]>h+.03:
            raise ValueError(f"uncontained figure layout: {identifier} {bounds}")
        for ax in fig.axes:
            for line in ax.lines:
                if not np.isfinite(line.get_xydata()).all():
                    raise ValueError(f"nonfinite plotted point: {identifier}")
            if ax.collections:
                for collection in ax.collections:
                    array=collection.get_array()
                    if array is not None and not np.isfinite(array).all():
                        raise ValueError(f"nonfinite image: {identifier}")
        paths=[]
        for ext in ("svg","pdf","png"):
            path=f"figures/{identifier}.{ext}"
            fig.savefig(self.out/path,dpi=320,facecolor="white")
            paths.append(path)
        if poster:
            path=f"poster/{identifier}.png"
            fig.savefig(self.out/path,dpi=320,facecolor="#F6F5F0")
            paths.append(path)
        self.register(identifier,title,paths,caption)
        plt.close(fig)


def plots(a,frozen):
    # FIG 01 — actual alternate-profile pressure and flow, plus command and signed residual.
    raw=[a.capture(frozen,"alternate_profile:"+case,["sensors"])["sensors"]
         for case in ("normal","outlet_opening")]
    outlet=[]
    for case in ("normal","outlet_opening"):
        where=frozen["captures"]["alternate_profile:"+case]["case_path"]
        outlet.append(loadmat(a.source(where+"/outlet_evidence.mat"),simplify_cells=True)["response"])
    t=raw[0]["pressure_sensor1"]["time"]; view=(t>=995)&(t<=1030)
    fig,axs=plt.subplots(2,2,figsize=(9,5.2),layout="constrained",sharex=True)
    for k,label,color,style in ((0,"Control",BLUE,"--"),(1,"Opening",TEAL,"-")):
        axs[0,0].plot(t[view],raw[k]["pressure_sensor1"]["values"][view],style,color=color,label=label)
        axs[0,1].plot(t[view],raw[k]["flow_sensor3"]["values"][view],style,color=color)
        axs[1,0].step(t[view],outlet[k]["restriction_area_input"]["values"][view]*1e6,where="post",linestyle=style,color=color)
    axs[1,1].plot(t[view],(outlet[1]["signed_outlet_flow"]["values"]-outlet[0]["signed_outlet_flow"]["values"])[view],color=TEAL)
    labels=("PS1 (MPa)","MFS3 (kg/s)","Received area (mm²)","Outlet-flow difference (kg/s)")
    for ax,label in zip(axs.flat,labels):
        ax.set_ylabel(label); ax.axvline(1000,color=SLATE,ls=":",lw=.8)
    for ax in axs[-1]: ax.set_xlabel("Saved time (s)")
    axs[0,0].legend(frameon=False)
    a.figure("FIG_01_controlled_response","Controlled withdrawal under the alternate profile",fig,
       "Both twins share the +5 kPa reservoir profile. The atmospheric outlet area steps at 1,000 s only in the intervention.",True)

    data=[a.capture(frozen,"timing:"+case,["sensors","logSeries"]) for case in ("normal","outlet_opening")]
    records=[{r["path"]:r["values"] for r in case["logSeries"]} for case in data]
    t=data[0]["sensors"]["pressure_sensor1"]["time"]; visible=(t>=24)&(t<=32)
    fig,axs=plt.subplots(3,3,figsize=(11,8),layout="constrained")
    specs=(("PS_Step/O","Issued pressure command (MPa)"),("Pressure_Source_G3/P","Received pressure command (MPa)"),
           ("pressure_sensor7","PS7 (MPa)"),("pressure_sensor1","PS1 (MPa)"),("flow_sensor3","MFS3 (kg/s)"))
    arrays=[]
    for ax,(key,label) in zip(axs.flat,specs):
        values=[r[key]/1e6 for r in records] if key in records[0] else [r["sensors"][key]["values"] for r in data]
        arrays.append(values)
        for idx,style,color in ((0,"--",BLUE),(1,"-",TEAL)):
            ax.plot(t[visible],values[idx][visible],style,color=color,label=("Control","Timing shift")[idx],
                    drawstyle="steps-post" if key in records[0] else "default")
        ax.set(xlabel="Saved time (s)",ylabel=label)
    axs[0,0].legend(frameon=False)
    for ax,key,relative in ((axs[1,2],3,False),(axs[2,0],3,True),(axs[2,1],4,True)):
        left,right=arrays[key]
        index=np.flatnonzero((t>=25)&(t<=32))
        difference=right[index+(5 if relative else 0)]-left[index]
        scale=(1e6 if key==3 else 1e3) if relative else 1
        unit=("Pa" if key==3 else "g/s") if relative else "MPa"
        sensor="PS1" if key==3 else "MFS3"
        ax.plot(t[index]-(25 if relative else 0),difference*scale,color=TEAL)
        ax.set(xlabel="Relative to command (s)" if relative else "Saved time (s)",
               ylabel=f"{sensor} difference ({unit})",
               title="Event-aligned" if relative else "Clock-aligned")
    prov=a.obj("nres_v1/provenance.json")
    last=axs[2,2]
    vals=[prov["clock_rms"],prov["event_aligned_rms"]]
    last.bar(["Clock","Event"],vals,color=[BLUE,TEAL],hatch=["//",""])
    last.set_ylabel("30 s normalized RMS")
    last.set_title(f"{vals[0]/vals[1]:.0f}× reduction")
    a.figure("FIG_02_timing_alignment","One-second command shift and retrospective alignment",fig,
       "Both commands move from 3.0 to 6.4 MPa on their recorded knots. Event alignment is retrospective and does not diagnose actuator lag.",True)

    ml=a.frame("phase13_extended_benchmark/comparison.csv")
    ml=ml[ml.variant=="full"].sort_values("hits")
    assert ml.cases.eq(39).all() and len(ml)==5
    fig,axs=plt.subplots(1,2,figsize=(9,3.8),layout="constrained")
    axs[0].barh(ml.model.str.replace("_"," "),ml.hits,color=BLUE)
    axs[0].axvline(39,color=ORANGE,ls="--",label="Constant LEAK = 39")
    axs[0].set(xlim=(0,42),xlabel="Archived LEAK labels matched (of 39)")
    axs[0].legend(frameon=False)
    release=a.obj("phase13_recovered_final/ml/ml_results.json")
    population=pd.Series(release["class_counts"]).sort_values()
    axs[1].barh(population.index.str.replace("COMPRESSOR_",""),population.values,color=SLATE)
    axs[1].set(xlabel="Release scenarios available for model fitting")
    a.figure("FIG_03_archive_ml","Oracle-onset benchmark and class support",fig,
             "All 39 scored holdouts carry LEAK. The constant rule ties XGBoost. No multiclass accuracy is reported.")

    dec=a.frame("phase13_decisive/scenario.csv")
    comp=a.frame("phase13_decisive/comparison.csv")
    frozen_alarm=a.frame("phase13_alarm_validation/overall.csv")
    fig,axs=plt.subplots(1,3,figsize=(11,4),layout="constrained")
    colors=(BLUE,TEAL,SLATE,ORANGE)
    for name,color,style in zip(STM,colors,("-","--","-.",":")):
        d=dec[(dec.model==name)&(dec["mode"]=="clean")&(dec.event==1)]
        time,y=deadline_curve(d.alarm_delay_s.dropna(),len(d))
        assert len(d)==48
        axs[0].step(time+1,y,where="post",label=TITLES[name],color=color,ls=style)
    axs[0].set(xscale="log",xlabel="Delay + 1 s (log scale)",ylabel="Fraction of all 48 events")
    axs[0].legend(frameon=False,fontsize=7)
    d=comp[(comp["mode"]=="clean")].set_index("model").loc[list(STM)]
    axs[1].barh([TITLES[k] for k in STM],d.false_episodes_per_inactive_hour,color=colors)
    axs[1].set(xlabel="False starts per inactive archive hour",title="1 s decisions")
    old=frozen_alarm[(frozen_alarm["mode"]=="clean")&frozen_alarm.model.isin(["random_forest","linear_svm"])]
    axs[2].bar(["Linear SVM","Random forest"],old.set_index("model").loc[["linear_svm","random_forest"]].new_alert_detections,color=[BLUE,TEAL])
    axs[2].set(ylim=(0,51),ylabel="New alarms (of 48)",title="120 s decisions")
    a.figure("FIG_04_detection","Detection delay and false-alarm burden",fig,
             "Cumulative clean replay uses all events in the denominator. Different decision cadences are shown in separate panels.",True)

    c=a.frame("phase13_decisive/comparison.csv")
    fig,axs=plt.subplots(1,3,figsize=(12,4),layout="constrained")
    conditions=("clean","white","correlated","bias","drift","stuck","delay")
    for ax,metric,title,fmt in zip(axs,("new_alert_detections","false_episodes","mean_duty"),
                  ("New alarms (of 48)","False episodes","Alarm duty (%)"),(".0f",".0f",".2f")):
        grid=c.pivot(index="model",columns="mode",values=metric).loc[list(STM),list(conditions)].to_numpy()
        if metric=="mean_duty": grid=grid*100
        ax.imshow(grid,cmap="Blues",aspect="auto",vmin=0)
        for i,j in np.ndindex(grid.shape):
            ax.text(j,i,format(grid[i,j],fmt),ha="center",va="center",fontsize=7,
                    color="white" if grid[i,j]>.55*grid.max() else NAVY)
        ax.set_xticks(range(7),conditions,rotation=55,ha="right")
        ax.set_yticks(range(4),[TITLES[k] for k in STM] if ax is axs[0] else [""]*4)
        ax.set_title(title); ax.grid(False)
    a.figure("FIG_05_robustness","Hypothetical sensor stresses and persistent alarms",fig,
             "Each metric uses its own scale. Noise, bias, drift, stuck and delayed sensors are simulated perturbations without industrial calibration.",True)

    g=a.frame("nres_v1/location_geometry.csv")
    fig,axs=plt.subplots(1,3,figsize=(10,4.4),layout="constrained")
    for ax,subset in zip(axs,("all","pressure","flow")):
        z=g[(g.seconds==30)&(g.bound_s==1)&(g.method=="B3")&(g.subset==subset)]
        grid=np.zeros((3,3))
        for i,j in ((0,1),(0,2),(1,2)):
            v=z[(z.a==LOC[i])&(z.b==LOC[j])].rms.item()
            grid[i,j]=grid[j,i]=v
        ax.imshow(grid,cmap="Blues",vmin=0)
        for i,j in np.ndindex(grid.shape):
            ax.text(j,i,f"{grid[i,j]:.3g}",ha="center",va="center",
                    color="white" if grid[i,j]>.55*grid.max() else NAVY)
        ax.set_xticks(range(3),[k[3:] for k in LOC]); ax.set_yticks(range(3),[k[3:] for k in LOC])
        ax.set_title(subset); ax.grid(False)
    a.figure("FIG_06_location_geometry","Location contrasts depend on sensor group",fig,
             "B3 normalized RMS, 30 s prefix, assumed ±1 s. Panel color scales are independent. Values do not constitute formal exclusion.",True)

    transfer=a.frame("nres_v1/transfer.csv")
    mfs=a.frame("nres_v1/mfs3_reproduction.csv")
    g=a.frame("nres_v1/location_geometry.csv")
    fig,axs=plt.subplots(1,3,figsize=(11,4),layout="constrained")
    tr=transfer[(transfer["rank"]==1)&(transfer.bound_s==1)&(transfer.subset=="all")]
    for model,style in (("B0",":"),("B1","-."),("B2","--"),("B3","-"),("B4","--")):
        s=tr[tr.method==model]
        axs[0].plot(s.seconds,s.margin,style,label=model)
    axs[0].set(xlabel="Observed prefix (s)",ylabel="Top-to-runner-up RMS margin")
    axs[0].legend(frameon=False,fontsize=7)
    axs[1].bar(["All","Without MFS3"],mfs.set_index("subset").loc[["all","omit_MFS3"]].margin,color=[TEAL,SLATE])
    axs[1].set_ylabel("Margin, full mechanism library")
    for x,y in (("SID215","TIMING"),("SID213","PRESSURE"),("SID213","SID312")):
        z=g[(g.a==x)&(g.b==y)&(g.seconds==30)&(g.subset=="all")&(g.method=="B3")]
        axs[2].plot(z.bound_s,z.rms,marker="o",label=f"{x} / {y}")
    axs[2].set(xlabel="Allowed offset (s)",ylabel="Minimum normalized RMS")
    axs[2].legend(frameon=False,fontsize=7)
    a.figure("FIG_07_mechanism_evidence","Reference, timing and sensor ablations",fig,
             "The alternate case is one held-template query, not a set of independent trials. NRES (B4) weighting changes units of the numerical margin, not observed decision accuracy.")

    old=a.obj("phase13_recovered_final/evidence.json")
    new=a.obj("phase13_integrated_timing/evidence.json")
    decisions=[v["policy_b"]["diagnostic"]["status"] for v in old["decisions"].values()]
    decisions.extend(v["diagnostic"]["status"] for v in new["formal"].values())
    counts=[decisions.count(k) for k in ("SPECIFIC","AMBIGUOUS","UNRESOLVED")]
    if counts!=[0,0,12]:
        raise ValueError("formal output differs from publication claim")
    fig,axs=plt.subplots(1,2,figsize=(10,3.8),layout="constrained")
    ax=axs[0]; ax.axis("off")
    blocks=("Causal signal representation\nPressure and signed flow",
            "Diagnostic evidence assessment\nMatched residuals; exploratory candidate ranks",
            "Qualified diagnostic decision\nRequires observation and prediction bounds")
    for i,block in enumerate(blocks):
        y=.8-.31*i
        ax.text(.5,y,block,ha="center",va="center",linespacing=1.4,
                bbox=dict(boxstyle="square,pad=.45",fc="white",ec=SLATE),transform=ax.transAxes)
        if i<2:
            ax.annotate("",(.5,y-.22),(.5,y-.10),xycoords=ax.transAxes,arrowprops={"arrowstyle":"->","color":SLATE})
    axs[1].bar(["Specific","Ambiguous","Unresolved"],counts,color=[BLUE,ORANGE,SLATE])
    axs[1].set(ylim=(0,13.5),ylabel="Accepted observations")
    axs[1].text(2,12.2,"12 / 12",ha="center")
    axs[1].text(.02,.89,"Localization L0\nSelective risk undefined",transform=axs[1].transAxes)
    a.figure("FIG_08_formal_decisions","Empirical evidence and qualified decisions",fig,
             "The schematic shows an evidence gate, not an automatic promotion of template ranks. No qualified exclusions were recorded.",True)
    return counts


def tables(a, frozen):
    def tab(n, title, frame, caption):
        a.table(f"TAB_{n:02d}", title, frame, caption)

    rows = [{"Capture": name, "Path": r["case_path"], "Raw SHA-256":r["raw_sha256"], "Files matched":r["files_verified_against_receipt"]} for name,r in frozen["captures"].items()]
    tab(1,"Accepted capture registry",pd.DataFrame(rows),"All twelve captures belong to one Center source family.")
    tab(2,"Mass accounting across fixed integration steps",a.frame("phase11-final/mass_balance.csv"),
        "Mass in kg; residual is storage change minus signed integrated boundary flow.")
    tab(3,"Historical event-window model comparison",a.frame("phase13_extended_benchmark/comparison.csv"),
        "All 39 scored scenarios carry LEAK annotations; recall denominator is fixed.")
    tab(4,"Frozen 120 s decision replay",a.frame("phase13_alarm_validation/overall.csv"),
        "Episode counts and rates use the archived observation duration.")
    tab(5,"One-second causal replay and stress tests",a.frame("phase13_decisive/comparison.csv"),
        "Perturbations are hypothetical; duty is a fraction, rates are per inactive archive hour.")
    tab(6,"Command timing sensor residuals",a.frame("phase13_integrated_timing/sensor_timing.csv"),
        "Pressure MPa, signed mass flow kg/s. Clock and event alignment are separate.")
    geo=a.frame("nres_v1/location_geometry.csv")
    tab(7,"Location and mechanism geometry",geo[(geo.seconds==30)&(geo.bound_s==1)],
        "Normalized RMS on a 30 s prefix with hypothetical ±1 s alignment.")
    tr=a.frame("nres_v1/transfer.csv")
    tab(8,"Matched-reference baselines on the alternate profile",tr[(tr['rank']==1)&(tr.bound_s==1)]
        .drop(columns=["per_channel_squared_contribution","valid_channels","invalid_channels"]),
        "One alternate profile; settings are repeated views of the same observation.")
    mfs=a.frame("nres_v1/mfs3_reproduction.csv")
    tab(9,"Sensor-withholding sensitivity",mfs.drop(columns=["ranks"]),
        "The margin is normalized RMS. Ranking establishes no exclusions.")
    tab(10,"Focal competing-mechanism routing",a.frame("mechanism_screen_v1/thirty_second_summary.csv"),
        "The focal controlled queries include self-templates; only one withdrawal used a held template.")
    reg=a.obj("mechanism_screen_v1/results_register.json")
    tab(11,"Full routing sweep and retained withdrawal queries",
        pd.DataFrame([{"Statistic":k,"Count":v} for k,v in reg["all_controlled"].items()]),
        "Counts repeat settings across a shared family. Eligibility gate disposition is REVISE_OR_REJECT.")
    tab(12,"Intervention observation windows",a.frame("phase12-paired-results/observation_windows.csv"),
        "Matched controlled simulations. The CSV retains original units and precision.")
    a.obj("phase13_recovered_final/evidence.json")
    a.obj("phase13_integrated_timing/evidence.json")
    tab(13,"Formal decisions and localization",pd.DataFrame([
        {"Decision":"SPECIFIC","Observations":0,"Qualified exclusions":0},
        {"Decision":"AMBIGUOUS","Observations":0,"Qualified exclusions":0},
        {"Decision":"UNRESOLVED","Observations":12,"Qualified exclusions":0}]),
        "Localization L0 for all observations. Selective risk undefined at zero specific coverage.")
    a.obj("phase13_integrated_timing/evidence.json")
    tab(14,"Signed timing-pair boundary flows",a.frame("phase13_integrated_timing/boundary_flows.csv"),
        "Boundary accounting from the accepted timing pair; command timing is distinct from actuator response.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("repository","workspace","output"):
        parser.add_argument("--"+key,type=Path,required=True)
    args=parser.parse_args()
    evidence=args.repository/"03_results/validation"
    docs=evidence/"publication_final_v1"
    manifest=evidence/"baseline_freeze_v1/baseline_manifest.json"
    frozen=read(manifest)
    count=verify(args.repository,args.workspace,frozen)
    if len(frozen["captures"])!=12:
        raise ValueError("publication requires twelve accepted captures")
    args.output.mkdir(parents=True,exist_ok=False)
    for name in ("figures","tables","poster"):
        (args.output/name).mkdir()
    a=Atlas(args.workspace,frozen,args.output)
    plots(a,frozen)
    tables(a,frozen)
    inventory=[]
    for scope,base in (("repository",evidence),("workspace",args.workspace/"outputs")):
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in (".png",".svg",".pdf"):
                continue
            if args.output.resolve() in path.resolve().parents or "publication_final_v1" in path.parts:
                continue
            inventory.append({"scope":scope,"path":path.relative_to(base).as_posix(),"sha256":digest(path)})
    (args.output/"historical_figures.json").write_text(json.dumps(inventory,indent=2),encoding="utf-8")
    figures=[i for i in a.items if i["id"].startswith("FIG_")]
    table_items=[i for i in a.items if i["id"].startswith("TAB_")]
    result={"baseline_manifest_sha256":digest(manifest),"frozen_files_verified":count,
            "accepted_captures":len(frozen["captures"]),"historical_graphic_files":len(inventory),
            "figures":len(figures),"tables":len(table_items),"items":a.items}
    for name in ("REPORT.md","POSTER.md","REPRODUCE.md","BRANCHING.md","claims.json"):
        path=docs/name
        target=args.output/("poster" if name=="POSTER.md" else "")/name
        target.write_bytes(path.read_bytes())
    (args.output/"manifest.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    lines=["# H₂-PRISM scientific results atlas","","[Research report](REPORT.md) · [Poster](poster/POSTER.md) · [Reproduction](REPRODUCE.md) · [Claims](claims.json)",""]
    for item in a.items:
        label=item["id"]
        links=" · ".join(f"[{Path(p).suffix[1:].upper()}]({p})" for p in item["files"])
        lines.extend([f"## {label} — {item['title']}","",item["caption"],"",links,""])
    (args.output/"ATLAS.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="items"},indent=2))


if __name__=="__main__":
    main()
