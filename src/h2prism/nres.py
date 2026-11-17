"""Nuisance-robust evidence separability on accepted controlled captures."""
import argparse
from dataclasses import dataclass
from itertools import combinations
import json
from pathlib import Path
from time import perf_counter_ns
import tracemalloc

import numpy as np
import pandas as pd
from scipy.io import loadmat

from .phase10 import visible_unit
from .phase13 import CAPTURE, sensor_values, sha256


UNITS={"pressure":{"Pa":1e-6,"kPa":1e-3,"MPa":1.},
       "mass_flow":{"kg/s":1.,"g/s":.001}}
BOUNDS=(0.,.2,.5,1.,2.)


@dataclass(frozen=True)
class Sensor:
    name: str
    kind: str
    unit: str


@dataclass(frozen=True)
class Observation:
    clock: np.ndarray
    values: np.ndarray
    schema: tuple

    def canonical(self,deadline):
        t,x=np.asarray(self.clock),np.asarray(self.values,dtype=float)
        if (t.ndim!=1 or len(t)==0 or not np.isfinite(t).all() or not np.all(np.diff(t)>0)
                or x.shape!=(len(t),len(self.schema))
                or len({s.name for s in self.schema})!=len(self.schema)
                or not self.schema or not np.isfinite(deadline)):
            raise ValueError("invalid observation schema or clock")
        try:
            factors=[UNITS[s.kind][s.unit] for s in self.schema]
        except KeyError as err:
            raise ValueError("incompatible sensor unit") from err
        active=t<=deadline
        if not active.any():
            raise ValueError("no observations at deadline")
        return t[active],x[active]*factors


def residual(observation,reference,deadline,*,operational=False,qualified_reference=False):
    if reference is None or (operational and not qualified_reference):
        return "BLOCKED_REFERENCE", None
    t,x=observation.canonical(deadline)
    ref,y=reference.canonical(deadline)
    if ([s.name for s in observation.schema]!=[s.name for s in reference.schema]
            or [s.kind for s in observation.schema]!=[s.kind for s in reference.schema]
            or not np.array_equal(t,ref)):
        raise ValueError("reference schema or timestamps differ")
    return "OK",x-y


def distance(query,template,anchor,step,bound,scales,weights=None):
    """Shared integer-grid translation; common valid mask across every shift."""
    q,r=np.asarray(query,dtype=float),np.asarray(template,dtype=float)
    if (q.ndim!=2 or not q.size or r.ndim!=2 or q.shape[1]!=r.shape[1]
            or not np.isfinite(step) or not np.isfinite(bound) or step<=0 or bound<0
            or not isinstance(anchor,(int,np.integer))):
        raise ValueError("invalid timing or signal shape")
    s=np.asarray(scales,dtype=float)
    if s.shape!=(q.shape[1],) or (s<=0).any() or not np.isfinite(s).all():
        raise ValueError("invalid sensor scales")
    w=np.ones(len(s)) if weights is None else np.asarray(weights,dtype=float)
    if w.shape!=s.shape or (w<=0).any() or not np.isfinite(w).all():
        raise ValueError("invalid weights")
    radius=int(np.floor(bound/step+1e-9))
    shifts=sorted(range(-radius,radius+1),key=lambda k:(abs(k),k))
    if anchor-radius<0 or anchor+radius+len(q)>len(r):
        raise ValueError("template does not cover fixed comparison window")
    shifted=np.stack([r[anchor+k:anchor+k+len(q)] for k in shifts])
    mask=np.isfinite(q)&np.isfinite(shifted).all(axis=0)
    if not mask.any():
        return None
    delta=np.where(mask,((q-shifted)/s)**2,0.)
    denominator=(mask*w).sum()
    score=np.sqrt((delta*w).sum(axis=(1,2))/denominator)
    winner=int(np.argmin(score))
    return dict(rms=float(score[winner]),selected_shift_s=shifts[winner]*step,
                max_rms=float(score.max()),valid_fraction=float(mask.mean()),
                valid_channels=np.flatnonzero(mask.any(axis=0)).tolist(),
                invalid_channels=np.flatnonzero(~mask.any(axis=0)).tolist(),
                per_channel_squared_contribution=(delta[winner].sum(axis=0)*w/denominator).tolist())


def rank(query,templates,step,bound,scale,weights=None):
    values=[]
    # Comparison support is common across candidate hypotheses as well as shifts.
    common=np.isfinite(query)
    radius=int(np.floor(bound/step+1e-9))
    for template,anchor in templates.values():
        if anchor-radius<0 or anchor+radius+len(query)>len(template):
            raise ValueError("candidate window unavailable")
        for k in range(-radius,radius+1):
            common &= np.isfinite(template[anchor+k:anchor+k+len(query)])
    q=np.where(common,query,np.nan)
    for name,(template,anchor) in templates.items():
        result=distance(q,template,anchor,step,bound,scale,weights)
        if result is not None:
            values.append(dict(candidate=name,**result))
    values.sort(key=lambda row:(row["rms"],row["candidate"]))
    for i,row in enumerate(values):
        row["rank"]=i+1
    return dict(ranks=values,candidate_set=sorted(templates),
                policy="EXPLORATORY_SET" if values else "RANKED_ONLY",
                set_narrowing_calibrated=False,
                margin=values[1]["rms"]-values[0]["rms"] if len(values)>1 else None)


def evaluate(observation,reference,deadline,templates,config,*,operational=False,qualified_reference=False):
    """Build a time-clipped residual and score pre-existing, canonical templates."""
    status,values=residual(observation,reference,deadline,operational=operational,
                           qualified_reference=qualified_reference)
    if status!="OK":
        return dict(status=status,ranks=[],candidate_set=sorted(templates),
                    policy="RANKED_ONLY",set_narrowing_calibrated=False)
    clock,_=observation.canonical(deadline)
    if len(clock)>1 and not np.allclose(np.diff(clock),config["step_s"],rtol=0,atol=1e-10):
        raise ValueError("unsupported grid in observed prefix")
    result=rank(values,templates,config["step_s"],config["bound_s"],config["scales"],
                config.get("weights"))
    return dict(status="OK",reference_source=config.get("reference_source","declared reference"),
                evidence="EXPLORATORY",**result)


def load_pairs(base):
    w=base/"work"
    def read(path):
        return json.loads(path.read_text(encoding="utf8"))
    old=read(base/"outputs/phase13_recovered_final/evidence.json")
    recent=read(base/"outputs/phase13_integrated_timing/evidence.json")
    history={r["id"]:r for r in old["historical"]}
    folders={"SID213":("phase12_sdi_retry_01","A"),"SID312":("final_research_matrix/sid312","sid312"),
             "SID215":("final_research_matrix/sid215","sid215"),"PRESSURE":("phase13_02/pressure_rival","pressure_rival"),
             "ALT":("phase13_02/alternate_profile","alternate_profile"),"TIMING":("phase13_command_delay_01","timing")}
    pairs,hashes={},{}
    clock=None
    schema=tuple(Sensor(n,"pressure","MPa") if n.startswith("PS") else Sensor(n,"mass_flow","kg/s") for n in CAPTURE)
    for label,(folder,key) in folders.items():
        pair=[]
        for case in ("normal","outlet_opening"):
            root=w/folder
            if label=="ALT" and case=="outlet_opening":
                root=w/"phase13_alternate_retry_02"
            index=key+":"+case
            record=recent["accepted"][case] if label=="TIMING" else old["accepted"].get(index) or history[index]
            expected=record.get("capture_hashes") or record["receipt"]["capture_hashes"]
            path=root/case/"center_raw.mat"
            if sha256(path)!=expected["center_raw.mat"]:
                raise ValueError(f"accepted capture changed: {index}")
            hashes[index]=expected["center_raw.mat"]
            data=loadmat(path,simplify_cells=True,variable_names=["sensors"])
            t=data["sensors"]["pressure_sensor1"]["time"]
            if clock is None:
                clock=t
            if not np.array_equal(t,clock) or not np.allclose(np.diff(t),.2,atol=1e-10,rtol=0):
                raise ValueError(f"unsupported common clock: {index}")
            for sensor in schema:
                if visible_unit(data["sensors"][CAPTURE[sensor.name]]["unit"])!=sensor.unit:
                    raise ValueError(f"canonical sensor unit mismatch: {sensor.name}")
            x=np.column_stack(list(sensor_values(data,clock).values()))
            if not np.isfinite(x).all():
                raise ValueError("nonfinite source capture")
            pair.append(Observation(clock,x,schema))
        pairs[label]=pair
    return clock,schema,pairs,hashes


def reproduce_mfs3(t,schema,pairs):
    names=[s.name for s in schema]
    anchors={k:np.searchsorted(t,25 if k=="TIMING" else 1000) for k in pairs}
    scale=np.sqrt(np.mean(pairs["SID213"][0].values[t<1000]**2,axis=0))
    residuals={k:b.values-a.values for k,(a,b) in pairs.items()}
    residuals["NORMAL"]=np.zeros_like(residuals["SID213"])
    anchors["NORMAL"]=anchors["SID213"]
    j=anchors["ALT"]
    rows=[]
    for subset,idx in (("all",np.arange(len(names))),
                       ("omit_MFS3",np.array([i for i,n in enumerate(names) if n!="MFS3"]))):
        templates={k:(x[:,idx],anchors[k]) for k,x in residuals.items() if k!="ALT"}
        result=rank(residuals["ALT"][j:j+151,idx],templates,.2,1.,scale[idx])
        rows.append(dict(subset=subset,top=result["ranks"][0]["candidate"],
                         runner_up=result["ranks"][1]["candidate"],**result))
    return rows


def run(base,out):
    t,schema,pairs,hashes=load_pairs(base)
    names=[s.name for s in schema]
    group=np.array([s.kind for s in schema])
    raw={name:b.values for name,(a,b) in pairs.items()}
    res={name:residual(b,a,t[-1])[1] for name,(a,b) in pairs.items()}
    scales=np.sqrt(np.mean(pairs["SID213"][0].values[t<1000]**2,axis=0))
    anchor=np.searchsorted(t,1000)
    subsets={"all":np.arange(len(names)),"pressure":np.flatnonzero(group=="pressure"),
             "flow":np.flatnonzero(group=="mass_flow")}
    subsets.update({"omit_"+n:np.array([j for j in range(len(names)) if j!=i]) for i,n in enumerate(names)})
    def balanced(idx):
        types=group[idx]
        return np.array([1/sum(types==g) for g in types])
    methods=(("B0",False,False,False),("B1",True,False,False),("B2",False,True,False),
             ("B3",True,True,False),("B4",True,True,True))
    timing=[]
    j=np.searchsorted(t,25)
    a,b=(o.values for o in pairs["TIMING"])
    # Equal constant nominal reference preserves the timing intervention and cancels in difference.
    fixed=a[j-1]
    for sub,idx in subsets.items():
        for bound in BOUNDS:
            for method,use_res,shifted,weighted in methods:
                bb,aa=(b-fixed,a-fixed) if use_res else (b,a)
                d=distance(bb[j:j+151,idx],aa[:,idx],j,.2,bound if shifted else 0.,scales[idx],
                           balanced(idx) if weighted else None)
                timing.append(dict(subset=sub,hypothetical_bound_s=bound,method=method,**d))
    reproduced=float(np.sqrt(np.mean(((b[j+5:j+156]-a[j:j+151])/scales)**2)))
    clock_rms=float(np.sqrt(np.mean(((b[j:j+151]-a[j:j+151])/scales)**2)))
    if not np.isclose(clock_rms,.027781127452742544,rtol=1e-8) or not np.isclose(reproduced,.00012192436273017852,rtol=1e-8):
        raise ValueError("published timing invariance fixture differs")
    loc=("SID213","SID312","SID215")
    geometry=[]
    for x,y in combinations((*loc,"PRESSURE","TIMING"),2):
        for sec in (5,15,30,60):
            n=round(sec/.2)+1
            for sub,idx in subsets.items():
                for bound in BOUNDS:
                    left=j if x=="TIMING" else anchor
                    right=j if y=="TIMING" else anchor
                    for name,scale,weight in (("raw_physical",np.ones(len(idx)),None),
                        ("B3",scales[idx],None),("B4",scales[idx],balanced(idx)),
                        ("residual_physical",np.ones(len(idx)),None)):
                        source=raw if name=="raw_physical" else res
                        d=distance(source[x][left:left+n,idx],source[y][:,idx],right,.2,bound,scale,weight)
                        geometry.append(dict(a=x,b=y,seconds=sec,subset=sub,bound_s=bound,method=name,**d))
    alerts=pd.read_csv(base/"outputs/phase13_causal_intelligence/rank_alerts.csv")
    alert=alerts[alerts["query"]=="alternate_profile"]
    query_anchor=np.searchsorted(t,float(alert.loc[alert.scope=="after_startup","first_alert_s"].iloc[0]))
    rows=[]
    for sec in (1,2,5,10,15,30,60):
        n=round(sec/.2)+1
        for sub,idx in subsets.items():
            for bound in BOUNDS:
                for method,use_res,shifted,weighted in methods:
                    source=res if use_res else raw
                    references={k:(source[k][:,idx],anchor) for k in loc}
                    query=source["ALT"][query_anchor:query_anchor+n,idx]
                    result=rank(query,references,.2,bound if shifted else 0.,scales[idx],
                                balanced(idx) if weighted else None)
                    for item in result["ranks"]:
                        rows.append(dict(seconds=sec,subset=sub,bound_s=bound,method=method,
                            query_deadline_s=float(t[query_anchor+n-1]),margin=result["margin"],
                            retained=" ".join(result["candidate_set"]),**item))
    stress=[]
    clean=res["ALT"][query_anchor:query_anchor+151]
    rng=np.random.default_rng(42)
    white=rng.normal(size=clean.shape)*scales*.01
    corr=white.copy()
    for i in range(1,len(corr)):
        corr[i]+=.8*corr[i-1]
    corrupt={"clean":clean.copy(),"white":clean+white,"correlated":clean+corr,
             "pressure_bias":clean.copy(),"stuck_MFS3":clean.copy(),"missing_MFS3":clean.copy(),
             "wrong_nominal_reference":raw["ALT"][query_anchor:query_anchor+151]-pairs["SID213"][0].values[query_anchor:query_anchor+151]}
    m=names.index("MFS3")
    corrupt["pressure_bias"][:,0]+=.01*scales[0]
    corrupt["stuck_MFS3"][:,m]=clean[0,m]
    corrupt["missing_MFS3"][:,m]=np.nan
    templates={k:(res[k],anchor) for k in loc}
    for mode,q in corrupt.items():
        for bound in BOUNDS:
            for method,w in (("B3",None),("B4",balanced(subsets["all"]))):
                result=rank(q,templates,.2,bound,scales,w)
                stress.append(dict(query="ALT",mode=mode,method=method,bound_s=bound,**result))
    # Open-set controls: no same-run template is included, and all locations remain plausible.
    for name,start in (("PRESSURE",anchor),("TIMING",j),("NORMAL_TRANSIENT",j)):
        q=res[name][start:start+151] if name in res else a[j:j+151]-a[j-1]
        for method,w in (("B3",None),("B4",balanced(subsets["all"]))):
            for bound in BOUNDS:
                stress.append(dict(query=name,mode="location_library_only",method=method,bound_s=bound,
                                   **rank(q,templates,.2,bound,scales,w)))
    perf=[]
    for nc in (3,13):
        for nt in (1,3):
            for bound in (0.,2.):
                idx=np.arange(nc)
                q=clean[:,idx]
                subset={k:(res[k][:,idx],anchor) for k in loc[:nt]}
                elapsed=[]
                for _ in range(30):
                    start=perf_counter_ns()
                    rank(q,subset,.2,bound,scales[idx],balanced(idx))
                    elapsed.append((perf_counter_ns()-start)/1e6)
                tracemalloc.start()
                rank(q,subset,.2,bound,scales[idx],balanced(idx))
                _,peak=tracemalloc.get_traced_memory()
                tracemalloc.stop()
                perf.append(dict(channels=nc,templates=nt,bound_s=bound,median_ms=np.median(elapsed),
                    p95_ms=np.quantile(elapsed,.95),p99_ms=np.quantile(elapsed,.99),traced_peak_bytes=peak))
    out.mkdir(parents=True)
    pd.DataFrame(reproduce_mfs3(t,schema,pairs)).to_csv(out/"mfs3_reproduction.csv",index=False)
    for fn,data in (("timing",timing),("location_geometry",geometry),("transfer",rows),
                    ("negative_controls",stress),("complexity",perf)):
        pd.DataFrame(data).to_csv(out/(fn+".csv"),index=False)
    (out/"provenance.json").write_text(json.dumps(dict(capture_raw_sha256=hashes,sensors=[s.__dict__ for s in schema],
        rms_scales=dict(zip(names,scales)),bounds_s=BOUNDS,recording_step_s=.2,clock_rms=clock_rms,
        event_aligned_rms=reproduced,query_anchor_s=float(t[query_anchor]),operational="BLOCKED_REFERENCE",
        formal="12 UNRESOLVED; 0 qualified exclusions; L0",controlled_source_families=1,
        independent_verified_families=0),indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    run(a.base,a.out)
    from .nres_figures import render
    render(a.base,a.out)
