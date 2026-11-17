"""Static source qualification and fail-closed independent pilot preflight."""
import argparse
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .data.loader import RAW_DATASET_DIR
from .phase2 import MODEL, MODEL_DIR, MODEL_HASH, checked_file
from .phase10 import model_blocks, sha256
from .phase12 import ANOMALOUS, ANOMALOUS_HASH
from .phase13_independent_design import admission

STATUS = {"NORMAL":"REFERENCE_ONLY", "LEAK":"CONTROLLED_OUTLET_ONLY",
          "FAULT":"BLOCKED", "DELAY":"BLOCKED"}
LOCATIONS = {"213", "312", "215"}


def audit_sources(raw):
    normal = checked_file(raw/MODEL_DIR/f"{MODEL}.slx", MODEL_HASH)
    anomaly = checked_file(raw/ANOMALOUS, ANOMALOUS_HASH)
    inventory = []
    for path in sorted((raw/"MATLAB_SIMSCAPE_Simulation").rglob("*.slx")):
        candidates = []
        with ZipFile(path) as archive:
            for member in archive.namelist():
                if not member.startswith("simulink/systems/") or not member.endswith(".xml"):
                    continue
                for block in ET.fromstring(archive.read(member)).iter("Block"):
                    name, kind = block.get("Name",""),block.get("BlockType","")
                    parameters = {p.get("Name"):p.text for p in block.iter("P")}
                    library = " ".join((parameters.get("SourceBlock") or "").split())
                    key = f"{name} {kind} {library}".lower()
                    if any(term in key for term in ("compressor","fault","delay","pressure source",
                                                     "local restriction","ps step","ps ramp","reservoir")):
                        candidates.append(dict(sid=block.get("SID"),name=name,kind=kind,library=library,
                                               system=member,parameters=parameters))
        inventory.append(dict(path=path.relative_to(raw).as_posix(),sha256=sha256(path),blocks=candidates))
    blocks = model_blocks(normal)
    archived = model_blocks(anomaly)
    assert blocks["59"]["initial_value"] == "3" and blocks["59"]["final_value"] == "6.4"
    assert archived["563"]["initial_value"] == archived["563"]["final_value"] == "1e-10"
    return dict(source_models=inventory, center_source_hash=MODEL_HASH,
                center_anomalous_hash=ANOMALOUS_HASH, class_status=STATUS,
                approved_outlet_candidates=sorted(LOCATIONS),
                controlled_only_area_m2={"baseline":.001,"opening":.0011},
                note="Static names and parameters locate candidate blocks. They do not establish a fault or delay mechanism, producing-run ancestry, or physical hydrogen validity.")


def preflight(manifest):
    structural = admission(manifest["records"],manifest["regions"])
    issues = list(structural["issues"])
    if not set(manifest["regions"]) <= LOCATIONS:
        issues.append("candidate region outside source-traced Center outlet scope")
    for run in manifest["records"]:
        sid = run.get("scenario_id")
        label = run.get("event_class")
        if label in STATUS:
            issues.append(f"{sid}: {STATUS[label]} is not an independent qualified generator")
        if run.get("model_sha256") != MODEL_HASH:
            issues.append(f"{sid}: outside pinned Center source scope")
    return dict(status="BLOCKED", structural=structural,issues=sorted(set(issues)),
                execution_authorized=False,
                reason="No independent class-qualified pilot or frozen operating acceptance thresholds have been approved.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest",type=Path)
    p.add_argument("output",type=Path)
    a = p.parse_args()
    result = {"source":audit_sources(RAW_DATASET_DIR),
              "preflight":preflight(json.loads(a.manifest.read_text(encoding="utf-8-sig")))}
    with a.output.open("x",encoding="utf8") as f:
        json.dump(result,f,indent=2)
    print(result["preflight"]["status"])


if __name__ == "__main__":
    main()
