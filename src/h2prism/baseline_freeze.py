"""Verify accepted capture receipts and freeze controlled-study baselines."""
import argparse
import json
from pathlib import Path

from .phase10 import sha256
from .phase2 import MODEL, MODEL_DIR, MODEL_HASH
from .data.loader import RAW_DATASET_DIR
from .simnet_study import archive_path, catalog_tables

FROZEN_OUTPUTS = (
    "phase13_recovered_final","phase13_extended_benchmark","phase13_independent_audit",
    "phase13_causal_validation","phase13_alarm_validation","phase13_integrated_timing",
    "phase13_sequential","phase13_causal_intelligence","phase13_decisive","nres_v1",
    "mechanism_screen_v1","phase13_pilot_qualification",
)
BASELINES = {
    "controlled_primary":"B3 time-aligned matched residuals",
    "exploratory_comparator":"full competing-mechanism library",
    "NRES":"RETAIN_AS_EQUIVALENT_BASELINE; no incremental rank improvement over B3",
    "mechanism_eligibility_gate":"REVISE_OR_REJECT; NOT_ADOPTED",
    "operational_reference":"BLOCKED_REFERENCE",
    "formal":"12 UNRESOLVED; zero qualified exclusions; L0",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def frozen_manifest(repo,workspace):
    old=read(workspace/"outputs/phase13_recovered_final/evidence.json")
    recent=read(workspace/"outputs/phase13_integrated_timing/evidence.json")
    prior={r["id"]:r for r in old["historical"]}
    folders={"A":"phase12_sdi_retry_01","sid312":"final_research_matrix/sid312",
             "sid215":"final_research_matrix/sid215","pressure_rival":"phase13_02/pressure_rival",
             "alternate_profile":"phase13_02/alternate_profile","timing":"phase13_command_delay_01"}
    captures={}
    all_hashes={"workspace":{},"repository":{}}
    def check(path,expected=None):
        d=sha256(path)
        if expected is not None and d!=expected:
            raise ValueError(f"checksum differs: {path}")
        return d
    def record(path,base,expected=None):
        all_hashes[base][path.relative_to(workspace if base=="workspace" else repo).as_posix()]=check(path,expected)
    for key,relative in folders.items():
        for case in ("normal","outlet_opening"):
            sid=key+":"+case
            root=workspace/"work"/relative
            if sid=="alternate_profile:outlet_opening":
                root=workspace/"work/phase13_alternate_retry_02"
            r=recent["accepted"][case] if key=="timing" else old["accepted"].get(sid) or prior[sid]
            if "receipt" in r:
                r=r["receipt"]
            if r.get("classification",r.get("status"))!="ACCEPTED":
                raise ValueError(f"capture is not accepted: {sid}")
            checks=r["capture_hashes"]
            for name,d in checks.items():
                record(root/case/name,"workspace",d)
            approval=read(root/"approval.json")
            approved=approval["cases"][case]
            record(root/"approval.json","workspace",r.get("pair",{}).get("approval_sha256"))
            record(root/case/"Center_phase12.slx","workspace",approved["derived_sha256"])
            record(root/case/"design.json","workspace",approved["design_sha256"])
            record(root/case/"preflight.json","workspace",approved["preflight_sha256"])
            record(root/case/"Normal_HNetwork_gest_center.slx","workspace",MODEL_HASH)
            captures[sid]={"files_verified_against_receipt":len(checks),"raw_sha256":checks["center_raw.mat"],
                           "case_path":(root/case).relative_to(workspace).as_posix()}
    record(RAW_DATASET_DIR/MODEL_DIR/f"{MODEL}.slx","repository",MODEL_HASH)
    catalog,_=catalog_tables()
    for row in catalog.itertuples(index=False):
        # archive_path checks the pinned clean digest and confines path traversal.
        path=archive_path(row)
        record(path,"repository",row.sha256_clean)
        rel=Path(row.file_noise_added).relative_to("H2-SimNet-Dataset")
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("invalid archived noise path")
        record(RAW_DATASET_DIR/rel,"repository",row.sha256_noise_added)
    for folder in FROZEN_OUTPUTS:
        output=workspace/"outputs"/folder
        if not output.is_dir():
            raise ValueError(f"missing frozen output: {folder}")
        for p in sorted(output.rglob("*")):
            if p.is_file():
                record(p,"workspace")
    for name in ("phase13.py","phase13_ml.py","phase13_benchmark.py","phase13_monitor.py",
                 "phase13_alarms.py","phase13_audit.py","sequential_replay.py",
                 "causal_intelligence.py","decisive_sprint.py","nres.py","mechanism_screen.py",
                 "certified_evidence.py","phase12.py","phase12_acceptance.py","phase13_command_delay.py"):
        p=repo/"src/h2prism"/name
        if name=="phase13_independent_audit.py":
            p=repo/"src/h2prism/phase13_audit.py"
        record(p,"repository")
    return dict(version="baseline-freeze-v1",baseline=BASELINES,captures=captures,
                source_families=1,verified_independent_families=0,sha256=all_hashes)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo",type=Path)
    p.add_argument("workspace",type=Path)
    p.add_argument("manifest",type=Path)
    p.add_argument("--verify",action="store_true")
    a=p.parse_args()
    if a.verify:
        frozen=read(a.manifest)
        for role,root in (("repository",a.repo),("workspace",a.workspace)):
            for name,d in frozen["sha256"][role].items():
                if sha256(root/name)!=d:
                    raise ValueError(f"frozen checksum differs: {role}/{name}")
        print(f"{len(frozen['captures'])} captures; {sum(map(len,frozen['sha256'].values()))} frozen files matched")
    else:
        with a.manifest.open("x",encoding="utf8") as stream:
            json.dump(frozen_manifest(a.repo,a.workspace),stream,indent=2)


if __name__=="__main__":
    main()
