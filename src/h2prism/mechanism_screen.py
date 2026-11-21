"""Controlled B3 mechanism screening with exploratory conditional location."""
import argparse
import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np
import pandas as pd

from .nres import load_pairs, rank, residual

WITHDRAWAL="CONTROLLED_WITHDRAWAL"
NORMAL="NORMAL_OPERATION"
MECHANISMS={"NORMAL_ZERO":NORMAL,"NORMAL_TRANSIENT":NORMAL,
            "SID213":WITHDRAWAL,"SID312":WITHDRAWAL,"SID215":WITHDRAWAL,
            "PRESSURE":"PRESSURE_COMMAND_CHANGE","TIMING":"COMMAND_ISSUANCE_SHIFT"}
LOCATIONS=("SID213","SID312","SID215")
UNKNOWN="UNKNOWN_OR_UNSUPPORTED"


def reference(observation,nominal,deadline,*,mode="controlled",source="matched_control",qualified=False):
    if mode not in ("controlled","operational"):
        raise ValueError("unknown reference mode")
    if mode=="operational" and (source not in ("verified_nominal","past_only") or not qualified):
        return "BLOCKED_REFERENCE",None
    return residual(observation,nominal,deadline,operational=mode=="operational",
                    qualified_reference=qualified)


def collapse(rows,registry):
    seen=set()
    best=[]
    for r in rows:
        group=registry[r["candidate"]]
        if group not in seen:
            best.append(dict(mechanism=group,**r))
            seen.add(group)
    return best


def screen(query,templates,registry,locations,step,offset,scale,quality=None):
    """Route only when withdrawal is the unique leader with and without time shift."""
    if "NORMAL_OPERATION" not in registry.values() or not set(templates)<=set(registry):
        raise ValueError("invalid mechanism registry")
    if not locations or not set(locations)<=set(templates):
        raise ValueError("location inventory unavailable")
    if quality is not None:
        quality=np.asarray(quality,dtype=bool)
        if quality.shape!=np.shape(query):
            raise ValueError("quality mask shape differs")
        query=np.where(quality,query,np.nan)
    aligned=rank(query,templates,step,offset,scale)
    exact=rank(query,templates,step,0,scale)
    a=collapse(aligned["ranks"],registry)
    b=collapse(exact["ranks"],registry)
    # B0 derives from the same distance rows and evidence mask as the full library.
    loc=[row for row in aligned["ranks"] if row["candidate"] in locations]
    def unique_leader(rows):
        return rows[0]["mechanism"] if len(rows)>1 and rows[0]["rms"]<rows[1]["rms"] else UNKNOWN
    lead, exact_lead=unique_leader(a),unique_leader(b)
    complete=bool(a) and np.isclose(a[0]["valid_fraction"],1.)
    eligible=bool(complete and lead==exact_lead==WITHDRAWAL)
    reason=("withdrawal_leads_both" if eligible else "invalid_or_missing_evidence" if not complete else
            "timing_sensitive_or_tied" if lead!=exact_lead or lead==UNKNOWN else "operational_leader")
    return dict(forced_location=loc[0]["candidate"] if loc else None,
        mechanism=lead,exact_mechanism=exact_lead,eligible=eligible,reason=reason,
        location_ranked=loc[0]["candidate"] if eligible and loc else None,
        retained_locations=list(locations) if eligible else [],
        mechanism_set=sorted(set(registry[k] for k in templates)|{UNKNOWN}),
        mechanism_margin=a[1]["rms"]-a[0]["rms"] if len(a)>1 else None,
        location_margin=loc[1]["rms"]-loc[0]["rms"] if eligible and len(loc)>1 else None,
        valid_fraction=a[0]["valid_fraction"] if a else 0.,
        valid_channels=a[0]["valid_channels"] if a else [],
        hypotheses=[(r["mechanism"],r["candidate"],r["rms"],r["selected_shift_s"]) for r in a],
        locations=[(r["candidate"],r["rms"]) for r in loc] if eligible else [],
        formal="UNRESOLVED",localization="L0")


def run(base,out):
    t,schema,pairs,hashes=load_pairs(base)
    names=[s.name for s in schema]
    scale=np.sqrt(np.mean(pairs["SID213"][0].values[t<1000]**2,axis=0))
    a25=np.searchsorted(t,25)
    late=np.searchsorted(t,1000)
    # A separate normal control supplies the nominal transient template.
    normal=pairs["SID312"][0].values
    contrasts={k:b.values-a.values for k,(a,b) in pairs.items()}
    templates={k:(contrasts[k],a25 if k=="TIMING" else late)
               for k in (*LOCATIONS,"PRESSURE","TIMING")}
    templates["NORMAL_ZERO"]=(np.zeros_like(normal),late)
    templates["NORMAL_TRANSIENT"]=(normal-normal[a25-1],a25)
    alert_rows=pd.read_csv(base/"outputs/phase13_causal_intelligence/rank_alerts.csv")
    pairs_to_alert={"SID213":"A","SID312":"sid312","SID215":"sid215",
                    "PRESSURE":"pressure_rival","ALT":"alternate_profile","TIMING":"timing"}
    # A controlled anchor may be used for scientific mode; latency rows require an actual alert.
    cases=[]
    for k in pairs_to_alert:
        scope="startup" if k=="TIMING" else "after_startup"
        rows=alert_rows[(alert_rows["query"]==pairs_to_alert[k])&(alert_rows.scope==scope)]
        if len(rows)!=1:
            raise ValueError("unexpected alert inventory")
        observed=rows.iloc[0].first_alert_s
        anchor=26 if k=="TIMING" else 1000
        cases.append((k,contrasts[k],anchor,observed,WITHDRAWAL if k=="ALT" or k in LOCATIONS else MECHANISMS[k]))
    nominal=pairs["SID213"][0].values
    cases.append(("NOMINAL",nominal-nominal[a25-1],25,25,NORMAL))
    cases.append(("QUIET",np.zeros_like(nominal),1000,np.nan,NORMAL))
    subsets={"all":np.arange(len(names)),"pressure":[i for i,s in enumerate(schema) if s.kind=="pressure"],
             "flow":[i for i,s in enumerate(schema) if s.kind=="mass_flow"]}
    subsets.update({"omit_"+n:[j for j in range(len(names)) if j!=i] for i,n in enumerate(names)})
    results=[]
    for query,data,anchor,alert,truth in cases:
        anchors=[("controlled",anchor)]
        if pd.notna(alert):
            anchors.append(("causal_alert",float(alert)))
        for scope,origin in anchors:
            j=np.searchsorted(t,origin)
            for seconds in (1,2,5,10,30,60,120):
                n=round(seconds/.2)+1
                for subset,idx in subsets.items():
                    view=data[j:j+n,idx]
                    scales=scale[idx]
                    # Apply the same configured subset to the full template library.
                    library={k:(v[i-10:i+n+10,idx],10) for k,(v,i) in templates.items()}
                    for offset in (0.,.5,1.,2.):
                        start=perf_counter_ns()
                        result=screen(view,library,MECHANISMS,LOCATIONS,.2,offset,scales)
                        elapsed=(perf_counter_ns()-start)/1e6
                        results.append(dict(query=query,scope=scope,seconds=seconds,subset=subset,offset_s=offset,
                            origin_s=origin,deadline_s=t[j+n-1],truth=truth,self_template=query in templates,
                            shares_nominal_schedule=query in ("NOMINAL","QUIET"),
                            forced_nonwithdrawal=truth!=WITHDRAWAL and result["forced_location"] is not None,
                            incorrect_route=truth!=WITHDRAWAL and result["eligible"],
                            suppressed_withdrawal=truth==WITHDRAWAL and not result["eligible"],
                            latency_ms=elapsed,**result))
    # Open-set omission explicitly tests the risk of an unrepresented operational rival.
    stress=[]
    for key,data,anchor,_,truth in cases:
        if key not in ("PRESSURE","TIMING","ALT"):
            continue
        j=np.searchsorted(t,anchor)
        for test in ("all_templates","without_queried_rival","missing_MFS3"):
            library={k:v for k,v in templates.items() if not (test=="without_queried_rival" and k==key)}
            q=data[j:j+151].copy()
            if test=="missing_MFS3":
                q[:,names.index("MFS3")]=np.nan
            stress.append(dict(query=key,test=test,truth=truth,**screen(q,library,MECHANISMS,LOCATIONS,.2,1.,scale)))
    # Offline proxies measure mismatch; neither is an approved operational reference.
    refs=[]
    for key,anchor in (("ALT",1000),("PRESSURE",1000),("TIMING",26),("NOMINAL",25)):
        query=pairs[key][1].values if key!="NOMINAL" else pairs["SID213"][0].values
        j=np.searchsorted(t,anchor)
        nominal=pairs[key][0].values if key!="NOMINAL" else pairs["SID312"][0].values
        truth=contrasts[key][j:j+151] if key!="NOMINAL" else np.zeros((151,len(names)))
        observed=query[j:j+151]
        for label,ref in (("pre_established_nominal",nominal[j:j+151]),
                          ("clock_mismatch_1s",nominal[j-5:j+146]),
                          ("past_only_5s_median",np.median(query[j-25:j],axis=0))):
            r=(observed-ref-truth)/scale
            refs.append(dict(query=key,reference=label,all_rms=np.sqrt(np.mean(r*r)),
                            without_MFS3_rms=np.sqrt(np.mean(np.delete(r,names.index("MFS3"),axis=1)**2)),
                            operational_status="BLOCKED_REFERENCE"))
    out.mkdir(parents=True)
    for name,rows in (("rankings",results),("reference_feasibility",refs),("stress",stress)):
        pd.DataFrame(rows).to_csv(out/(name+".csv"),index=False)
    (out/"registry.json").write_text(json.dumps(dict(mechanisms=MECHANISMS,locations=LOCATIONS,
        abstention=UNKNOWN,operational_reference="BLOCKED_REFERENCE",capture_raw_sha256=hashes,
        policy="unique withdrawal leader with both zero and bounded shift, complete selected evidence",
        positive_mechanism_coverage_is_exploratory=True,independent_families=0,
        reference_constraints="Matched controls are scientific only; command-context model unavailable.",
        nominal_query_control="SID213 control; nominal template uses SID312 control from same source."),indent=2),encoding="utf8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("out",type=Path)
    a=p.parse_args()
    run(a.base,a.out)
