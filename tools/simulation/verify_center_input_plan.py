"""Check the Center capture plan against the pinned SLX without MATLAB."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

PLAN = Path(__file__).with_name("center_input_plan.json")


def normalized(value):
    return " ".join((value or "").replace(r"\n", " ").split())


def param(block, key):
    return next((p.text for p in block.iter("P") if p.get("Name") == key), None)


def inspect_xml(root, subsystem, plan):
    blocks = {b.get("SID"): b for b in root.findall("Block")}
    links = {frozenset(p.text for p in line.iter("P") if p.get("Name") in ("Src", "Dst"))
             for line in root.findall("Line")}

    def block(sid):
        if sid not in blocks:
            raise ValueError(f"Missing required SID {sid}")
        return blocks[sid]

    def library(sid, expected):
        if normalized(param(block(sid), "SourceBlock")) != expected:
            raise ValueError(f"Unsupported library link at SID {sid}")

    def wire(a, b):
        if frozenset((a, b)) not in links:
            raise ValueError(f"Required connection missing or unsupported: {a} -> {b}")

    reservoir = plan["reservoir_inputs"]
    controls = plan["physical_inputs"]
    if (len(reservoir) != 2 or len(controls) != 2 or
            {r["role"] for r in reservoir} != {"reservoir_temperature", "reservoir_pressure"} or
            {r["role"] for r in controls} != {"pressure_source_step", "pressure_source_ramp"}):
        raise ValueError("Required Center input roles missing or unsupported")
    library("1", plan["reservoir_library"])
    if block("12").get("BlockType") != "SubSystem":
        raise ValueError("Unsupported reservoir input subsystem")
    for item in reservoir:
        converter, source, goto = (item[k] for k in ("converter_sid", "from_sid", "goto_sid"))
        library(converter, plan["converter_library"])
        if (block(source).get("BlockType") != "From" or block(goto).get("BlockType") != "Goto" or
                param(block(source), "GotoTag") != item["tag"] or param(block(goto), "GotoTag") != item["tag"] or
                param(block(converter), "Unit") != item["unit"]):
            raise ValueError(f"Unsupported reservoir route or unit: {item['role']}")
        wire(f"{source}#out:1", f"{converter}#in:1")
        wire(f"12#out:{item['subsystem_output']}", f"{goto}#in:1")
        wire(f"{converter}#rconn:1", f"1#rconn:{item['reservoir_port']}")

    observed_controls = []
    for item in controls:
        source, target = item["source_sid"], item["target_sid"]
        library(source, item["library"])
        library(target, plan["pressure_source_library"])
        if param(block(target), "source_type") != plan["controlled_mode"]:
            raise ValueError(f"Unsupported pressure source mode at SID {target}")
        wire(f"{source}#rconn:1", f"{target}#lconn:2")
        parameters = {key: [param(block(source), key), param(block(source), key + "_unit")]
                      for key in item["parameters"]}
        if any(not all(pair) for pair in parameters.values()):
            raise ValueError(f"Missing physical source parameters at SID {source}")
        observed_controls.append({"role": item["role"], "parameters": parameters})

    all_converters = {sid for sid, b in blocks.items()
                      if normalized(param(b, "SourceBlock")) == plan["converter_library"]}
    all_pressure_controls = {sid for sid, b in blocks.items()
                             if normalized(param(b, "SourceBlock")) == plan["pressure_source_library"]
                             and param(b, "source_type") == plan["controlled_mode"]}
    if (all_converters != {r["converter_sid"] for r in reservoir} or
            all_pressure_controls != {r["target_sid"] for r in controls}):
        raise ValueError("Additional or unmapped controls require source review")

    workspace_inputs = [b.get("SID") for system in (root, subsystem) for b in system.findall("Block")
                        if b.get("BlockType") == "FromWorkspace"]
    if workspace_inputs:
        raise ValueError(f"Unsupported workspace-driven inputs: {workspace_inputs}")
    return {"reservoir_inputs": reservoir, "native_physical_inputs": observed_controls,
            "workspace_input_blocks_in_traced_systems": workspace_inputs}


def verify(path, plan_path=PLAN):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != plan["sha256"]:
        raise ValueError("Center SLX checksum changed")
    with ZipFile(path) as archive:
        root, subsystem = [ET.fromstring(archive.read(f"simulink/systems/{name}.xml"))
                           for name in ("system_root", "system_12")]
    return {"slx_sha256": actual, **inspect_xml(root, subsystem, plan)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slx", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.slx), indent=2))
