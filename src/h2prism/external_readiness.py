"""Hash-bound intake for a separately supplied pressure and signed-flow dataset."""
import argparse
import csv
import hashlib
from io import BytesIO
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .nres import Observation, Sensor, UNITS
from .phase13_independent_design import PARTITIONS, LABELS

QUALIFICATIONS = {
    "multiclass": {"independence","labels","locked_protocol","precision_design"},
    "localization": {"independence","labels","locked_protocol","precision_design","location_truth"},
    "calibration": {"independence","labels","locked_protocol","precision_design","calibration_plan"},
    "formal": {"independence","labels","locked_protocol","measurement_bounds","clock_bounds",
               "initial_boundary_bounds","parameter_bounds","numerical_enclosure",
               "model_discrepancy","joint_prediction_enclosures"},
    "incremental_value": {"independence","labels","locked_protocol","precision_design","calibration_plan",
                          "matched_coverage_plan","measurement_bounds","clock_bounds",
                          "initial_boundary_bounds","parameter_bounds","numerical_enclosure",
                          "model_discrepancy","joint_prediction_enclosures"},
}


def read_bytes(root,path,expected):
    target=(root/path).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("path outside dataset root")
    data=target.read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError(f"checksum mismatch: {path}")
    return data


class Adapter:
    def __init__(self,schema):
        self.channels=sorted(schema["sensors"],key=lambda r:r["id"])
        self.clock=schema["clock"]
        self.features=tuple(Sensor(c["id"],c["kind"],"MPa" if c["kind"]=="pressure" else "kg/s")
                            for c in self.channels)
        cols=[c["column"] for c in self.channels]
        if (len({x.name for x in self.features})!=len(self.features)
                or len(set(cols))!=len(cols) or self.clock["column"] in cols
                or {c["kind"] for c in self.channels}!={"pressure","mass_flow"}):
            raise ValueError("require unique sensor mapping with pressure and mass flow")
        self.time_factor={"s":1.,"ms":.001}.get(self.clock["unit"])
        if self.time_factor is None or not self.clock.get("timebase"):
            raise ValueError("unsupported or undeclared clock")
        period=self.clock.get("nominal_step_s")
        if period is not None and (not np.isfinite(period) or period<=0):
            raise ValueError("invalid nominal step")
        for c in self.channels:
            if (c["unit"] not in UNITS[c["kind"]] or c["polarity"] not in (-1,1)
                    or not c.get("role") or not c.get("positive_direction")
                    or (c["kind"]=="pressure" and c["polarity"]!=1)):
                raise ValueError(f"invalid units, role or polarity for {c['id']}")
        # These are schema safeguards; trusted review must also verify channel semantics.
        forbidden={c.lower() for c in schema.get("metadata_columns",[])}|{"label","event_class","onset","location",
            "root_id","scenario_id","partition","mechanism","event_location","truth","label_anomaly"}
        if forbidden & ({c.lower() for c in cols}|{s.name.lower() for s in self.features}):
            raise ValueError("metadata cannot be a sensor feature")

    def parse(self,data,deadline=None):
        if deadline is None:
            frame=pd.read_csv(BytesIO(data))
        else:
            if not np.isfinite(deadline):
                raise ValueError("invalid deadline")
            # Validate only the available prefix; full-stream review is separate.
            reader=csv.reader((line.decode("utf-8-sig") for line in BytesIO(data)),strict=True)
            header=next(reader,[])
            if len(set(header))!=len(header) or self.clock["column"] not in header:
                raise ValueError("invalid CSV header")
            time_col=header.index(self.clock["column"])
            rows=[]
            for row in reader:
                if len(row)<=time_col:
                    raise ValueError("missing observed timestamp")
                arrived=float(row[time_col])*self.time_factor
                if not np.isfinite(arrived):
                    raise ValueError("invalid observed timestamp")
                if arrived>deadline:
                    break
                if len(row)!=len(header):
                    raise ValueError("invalid observed record")
                rows.append([v if v else None for v in row])
            frame=pd.DataFrame(rows,columns=header)
        clock=frame[self.clock["column"]].to_numpy(dtype=float)*self.time_factor
        if not len(clock) or not np.isfinite(clock).all() or not np.all(np.diff(clock)>0):
            raise ValueError("invalid or nonmonotone clock")
        period=self.clock.get("nominal_step_s")
        if period is not None and not np.allclose(np.diff(clock),period,rtol=0,atol=1e-8):
            raise ValueError("clock step differs")
        x=np.column_stack([frame[c["column"]].to_numpy(dtype=float)*c["polarity"]*UNITS[c["kind"]][c["unit"]]
                           for c in self.channels])
        if np.isinf(x).any():
            raise ValueError("infinite telemetry")
        obs=Observation(clock,x,self.features)
        if deadline is None:
            return obs
        t,y=obs.canonical(deadline)
        return Observation(t,y,self.features)


def open_partition(root,manifest,partition,*,test_unsealed=False):
    """Yield telemetry only; callers fetch event labels through the scoring manifest."""
    if partition not in PARTITIONS or (partition=="untouched_test" and not test_unsealed):
        raise ValueError("partition unavailable or sealed")
    adapter=Adapter(manifest["schema"])
    for row in manifest["records"]:
        if row["partition"]==partition:
            yield row["scenario_id"], adapter.parse(read_bytes(root,Path(row["path"]),row["sha256"]))


def qualify(root,manifest,registry):
    issues,observed={},{}
    adapter=Adapter(manifest["schema"])
    def issue(code,value):
        issues.setdefault(code,[]).append(value)
    records=manifest["records"]
    ids=set()
    ancestry={}
    regions=set(manifest.get("regions",[]))
    roots={p:{c:set() for c in LABELS} for p in PARTITIONS}
    location_roots={p:{c:set() for c in regions} for p in PARTITIONS}
    families={p:{c:set() for c in LABELS} for p in PARTITIONS}
    location_families={p:{c:set() for c in regions} for p in PARTITIONS}
    manifest_hash=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    bound_registry=(registry.get("dataset_id")==manifest.get("dataset_id") and bool(manifest.get("dataset_id"))
                    and registry.get("manifest_canonical_sha256")==manifest_hash)
    if not bound_registry:
        issue("evidence","no reviewed registry bound to canonical dataset manifest")
    for row in records:
        sid,part,kind=row["scenario_id"],row["partition"],row["event_class"]
        if sid in ids or part not in PARTITIONS or kind not in LABELS:
            issue("structure",f"{sid}: duplicate ID or unsupported partition/class")
            continue
        ids.add(sid)
        if any(not row.get(k) for k in ("root_id","family_id","mechanism","label_receipt")):
            issue("structure",f"{sid}: root, family, mechanism and label receipt required")
        if "parent_hashes" not in row or not isinstance(row["parent_hashes"],list):
            issue("structure",f"{sid}: explicit parent hash inventory required")
        if not row.get("ancestry_complete"):
            issue("structure",f"{sid}: ancestry unresolved")
        try:
            obs=adapter.parse(read_bytes(root,Path(row["path"]),row["sha256"]))
        except (KeyError,OSError,ValueError) as e:
            issue("structure",f"{sid}: {e}")
            continue
        clock,values=obs.clock,obs.values
        if len(clock)<2 or not np.isfinite(values).all(axis=1).any():
            issue("structure",f"{sid}: no usable multi-sample stream")
        canonical=np.where(values==0,0.,values)  # neutralize signed zero
        fingerprint=hashlib.sha256(np.asarray(clock-clock[0],dtype="<f8").tobytes()+
                                    np.asarray(canonical,dtype="<f8").tobytes()).hexdigest()
        for key in (("root",row.get("root_id")),("family",row.get("family_id")),
                    ("artifact",row["sha256"]),("normalized_trace",fingerprint),
                    *(("artifact",h) for h in row.get("parent_hashes",[]))):
            if key[1] and key in ancestry and ancestry[key]!=part:
                issue("structure",f"{sid}: {key[0]} crosses partitions")
            ancestry[key]=part
        valid_receipt=(bound_registry and registry.get("accepted_label_receipts",{}).get(sid)==
                       {"receipt":row.get("label_receipt"),"sha256":row["sha256"]}
                       and bool(row.get("label_receipt")))
        if not valid_receipt:
            issue("labels",f"{sid}: no externally reviewed label receipt")
        if kind!="NORMAL":
            start,stop=row.get("onset_s"),row.get("end_s")
            if (not isinstance(start,(int,float)) or not isinstance(stop,(int,float))
                    or not clock[0]<=start<=stop<=clock[-1]):
                issue("labels",f"{sid}: invalid event interval")
        elif row.get("onset_s") is not None or row.get("end_s") is not None:
            issue("labels",f"{sid}: NORMAL has event timing")
        if row.get("root_id"):
            roots[part][kind].add(row["root_id"])
        if row.get("family_id"):
            families[part][kind].add(row["family_id"])
        if kind=="LEAK":
            site=row.get("location")
            if site not in regions:
                issue("localization",f"{sid}: no supported location")
            elif row.get("root_id"):
                location_roots[part][site].add(row["root_id"])
                if row.get("family_id"):
                    location_families[part][site].add(row["family_id"])
        observed[sid]={"partition":part,"samples":len(clock),"topology":row.get("topology"),
                       "missing_fraction":float(np.isnan(values).mean())}
    minima=registry.get("minimum_roots_per_class",{})
    covered=bool(records)
    loc_covered=bool(regions)
    loc_minima=registry.get("minimum_roots_per_location",{})
    for part in PARTITIONS:
        n=minima.get(part)
        ln=loc_minima.get(part)
        if not isinstance(n,int) or n<1 or any(len(v)<n for v in families[part].values()):
            covered=False
        if not isinstance(ln,int) or ln<1 or any(len(v)<ln for v in location_families[part].values()):
            loc_covered=False
    approved=set()
    if bound_registry:
        for key,record in registry.get("approved_evidence",{}).items():
            try:
                if record["reviewed"] is True:
                    read_bytes(root,Path(record["path"]),record["sha256"])
                    approved.add(key)
            except (ValueError,OSError,KeyError):
                issue("evidence",f"unverified artifact: {key}")
    flags={}
    for claim,requires in QUALIFICATIONS.items():
        blocked=[]
        if issues.get("structure") or issues.get("labels") or not covered:
            blocked.append("provenance, labels or class support incomplete")
        if claim=="localization" and (not loc_covered or issues.get("localization")):
            blocked.append("location support incomplete")
        blocked.extend(f"required reviewed evidence missing: {k}" for k in sorted(requires-approved))
        flags[claim]={"status":"BLOCKED" if blocked else "ELIGIBLE_FOR_EXTERNAL_REVIEW","reasons":blocked}
    return dict(dataset=manifest.get("dataset_id"),manifest_canonical_sha256=manifest_hash,claims=flags,issues=issues,scenarios=observed,
                declared_family_counts={p:{c:len(v) for c,v in families[p].items()} for p in PARTITIONS},
                root_counts={p:{c:len(v) for c,v in roots[p].items()} for p in PARTITIONS},
                location_root_counts={p:{c:len(v) for c,v in location_roots[p].items()} for p in PARTITIONS},
                warning="Structural qualification and receipt integrity do not prove independence, scientific correctness or certified exclusions.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("root",type=Path)
    p.add_argument("manifest",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--review-registry",type=Path)
    p.add_argument("--registry-sha256")
    a=p.parse_args()
    manifest=json.loads(a.manifest.read_text(encoding="utf-8-sig"))
    registry={}
    if a.review_registry:
        data=a.review_registry.read_bytes()
        if hashlib.sha256(data).hexdigest()!=a.registry_sha256:
            p.error("out-of-band registry hash missing or mismatched")
        registry=json.loads(data)
    result=qualify(a.root,manifest,registry)
    with a.out.open("x",encoding="utf8") as f:
        json.dump(result,f,indent=2)
    raise SystemExit(int(any(r["status"]=="BLOCKED" for r in result["claims"].values())))


if __name__=="__main__":
    main()
