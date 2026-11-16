"""Prepare and qualify a new Center controlled atmospheric-outlet experiment."""
from __future__ import annotations

import argparse
from decimal import Decimal
from pathlib import Path
import shutil
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
from scipy.io import loadmat

from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT
from .phase2 import MODEL, MODEL_DIR, MODEL_HASH, checked_file
from .phase10 import CAPTURE, metrics, model_blocks, sha256, solver_grid, visible_unit
from .phase11 import model_diff, read_json, write_json

ANOMALOUS = "MATLAB_SIMSCAPE_Simulation/anomalous_scenarios/Anomalous_HNetwork_gest_center.slx"
ANOMALOUS_HASH = "e6caa8cf6558f7a524fd2a4e53ecb0530cf84479cbdf06c7dde4a02ef29acf33"
CASES = ("normal", "outlet_opening")
SOLVER = {"SolverType": "Fixed-step", "Solver": "ode14x", "FixedStep": "0.2",
          "StartTime": "0.0", "StopTime": "20000", "RelTol": "1e-3", "AbsTol": "auto",
          "LoadInitialState": "off", "LoadExternalInput": "off"}
AREA = {"initial_value": "0.001", "normal_final": "0.001", "intervention_final": "0.0011",
        "step_time": "1000", "area_unit": "m^2", "time_unit": "s",
        "min": "1e-10", "max": "0.01"}


def source_evidence(normal, anomalous):
    normal = checked_file(normal, MODEL_HASH)
    anomalous = checked_file(anomalous, ANOMALOUS_HASH)
    evidence = model_diff(normal, anomalous)
    source = model_blocks(normal)
    categories = {
        "restriction_and_actuation": ["213", "563"],
        "pressure_and_temperature_boundaries": ["1", "195", "200", "217", "224", "316", "12"],
        "pressure_source_controls": ["55", "239", "59", "241"],
        "gas_properties": ["4"], "solver_configuration": ["7"],
        "sensor_configuration": ["50", "51", "52", "109", "187", "318", "392", "418",
                                 "428", "431", "311", "210", "218"],
        "storage_and_initialization": ["47", "48", "49", "106", "107", "221", "309", "205"],
    }
    added = set(evidence["added_blocks"])
    changed = set(evidence["changed_common_blocks"])
    for category, sids in categories.items():
        evidence.setdefault("difference_matrix", {})[category] = {
            sid: {"name": source[sid]["name"] if sid in source else evidence["added_blocks"].get(sid),
                  "status": "ADDED" if sid in added else "CHANGED" if sid in changed else "UNCHANGED_ROOT_PARAMETERS"}
            for sid in sids}
    evidence["source_model_sha256"] = MODEL_HASH
    evidence["boundary_200"] = {name: source["200"][name] for name in
                              ("pressure_spec", "reservoir_pressure", "reservoir_pressure_unit",
                               "reservoir_temperature", "reservoir_temperature_unit")}
    evidence["sid_213_normal"] = {key: source["213"][key] for key in
                                  ("restriction_type", "restriction_area", "min_area", "max_area", "Cd", "area")}
    evidence["physics"] = "The existing branch withdraws gas to an atmospheric reservoir. SID 213 controls that outlet; the anomalous file substitutes a static near-closed area for the nominal outlet and supplies no verified opening event."
    return evidence


def specification():
    return {
        "classification": "NEW CONTROLLED SIMULATION",
        "status": "CONDITIONAL",
        "archived_anomalous_status": "BLOCKED",
        "source_sha256": MODEL_HASH, "solver": SOLVER, "area": AREA,
        "location": {"restriction_sid": "213", "upstream_junction_sids": ["47", "48", "50"],
                     "flow_sensor_sid": "218", "reservoir_sid": "200"},
        "mechanism": "Increase the existing PS1-to-atmosphere outlet conductance. This is an engineered incremental atmospheric withdrawal through an existing model branch.",
        "design_basis": "Set both twins to the pinned nominal 0.001 m^2 before 1000 s. Increase only the intervention final area by 10%. These are design settings, not source leak ground truth or calibration. The event is on the 0.2 s grid and separated from the existing 25 s pressure step.",
        "downstream": "Existing SID 200 atmospheric reservoir. Source reproduction logged 0.100 MPa and 293.15 K internally; re-verify runtime.",
        "matching": "Both twins receive the same variable restriction and PS Step wiring. Only final_value differs between the twins. Keep physical parameters, native controls, sensor mapping, initial-state policy, and horizon fixed.",
        "solver_basis": "0.2 s is the finest completed NORMAL resolution; no certified numerical tolerance is implied.",
        "gas": "Pinned SID 4 configured constant-property perfect-gas representation; R=0.287 kJ/(kg K), Z=0.998386; composition and hydrogen fidelity unverified.",
        "qualification": ["Verify both effective area command histories and timed change in the intervention.",
                          "Verify signed branch flow, upstream and downstream pressure, and atmospheric sink state.",
                          "Compare derived NORMAL with original 0.2 s NORMAL and both twins before the event.",
                          "Check after-event incremental outflow and all sensor histories before treating the label as a verified intervention."],
    }


def prepare(destination, normal):
    normal = checked_file(normal, MODEL_HASH)
    if destination.resolve().is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError("derived cases must be prepared outside the repository")
    destination.mkdir(parents=True)
    spec = specification()
    for case in CASES:
        folder = destination / case
        folder.mkdir()
        with normal.open("rb") as src, (folder / normal.name).open("xb") as dst:
            shutil.copyfileobj(src, dst)
        checked_file(folder / normal.name, MODEL_HASH)
        write_json(folder / "design.json", {"case": case, **spec})


def paired_xml(control, opening):
    """Check all saved system and configuration records except the single design delta."""
    with ZipFile(control) as a, ZipFile(opening) as b:
        def records(archive):
            return {name for name in archive.namelist() if name.startswith(("simulink/systems/", "simulink/configSet"))
                    and name.endswith(".xml")}

        files = records(a)
        if files != records(b):
            raise ValueError("twin SLX system or configuration inventories differ")
        root_name = "simulink/systems/system_root.xml"
        if root_name not in files:
            raise ValueError("missing system-root XML")
        for name in sorted(files):
            left, right = ET.fromstring(a.read(name)), ET.fromstring(b.read(name))
            if name == root_name:
                def command(root):
                    block = root.find("Block[@Name='Phase12 Outlet Area']")
                    if block is None:
                        raise ValueError("missing engineered command block")
                    return block.find(".//P[@Name='final_value']")

                p, q = command(left), command(right)
                if p is None or q is None or (Decimal(p.text), Decimal(q.text)) != (Decimal(AREA["normal_final"]), Decimal(AREA["intervention_final"])):
                    raise ValueError("incorrect twin area command delta")
                q.text = p.text
            if ET.tostring(left) != ET.tostring(right):
                raise ValueError(f"unintended twin XML difference: {name}")
    return ["Phase12 Outlet Area.final_value"]


def approve(root):
    hashes = {}
    files = []
    versions = []
    for case in CASES:
        folder = root / case
        file = folder / "Center_phase12.slx"
        record = read_json(folder / "preflight.json")
        design = {"case": case, **specification()}
        if read_json(folder / "design.json") != design:
            raise ValueError(f"unexpected prepared specification: {case}")
        expected = {"source_sha256": MODEL_HASH, "derived_sha256": sha256(file), "case": case,
                    "compile_status": "PASSED", "solver": SOLVER, "location": design["location"],
                    "existing_block_links_parameters_and_connections_unchanged": True,
                    "command_final_area_m2": AREA["normal_final" if case == "normal" else "intervention_final"]}
        if any(record.get(key) != value for key, value in expected.items()):
            raise ValueError(f"preflight evidence mismatch: {case}")
        checked_file(folder / f"{MODEL}.slx", MODEL_HASH)
        files.append(file)
        versions.append((record["version"], record["products"]))
        hashes[case] = {"derived_sha256": expected["derived_sha256"],
                        "preflight_sha256": sha256(folder / "preflight.json"),
                        "design_sha256": sha256(folder / "design.json")}
    if versions[0] != versions[1]:
        raise ValueError("preflight runtime versions differ")
    delta = paired_xml(*files)
    write_json(root / "approval.json", {"schema": "center-phase12-paired-preflight/1",
                                        "allowed_saved_xml_delta": delta, "cases": hashes})


def analyze(root, reference_dir, output):
    """Summarize only completed approved runs and their exact-clock comparison."""
    approval = read_json(root / "approval.json")
    extracts, responses = {}, {}
    for case in CASES:
        folder = root / case
        if "=== PHASE 12 CAPTURE COMPLETED ===" not in (folder / "execution.log").read_text(encoding="utf-8"):
            raise ValueError(f"capture did not complete: {case}")
        evidence = loadmat(folder / "outlet_evidence.mat", simplify_cells=True)
        extracted = loadmat(folder / "center_extracted.mat", simplify_cells=True)
        if (sha256(folder / "Center_phase12.slx") != evidence["hash"]
                or approval["cases"][case]["derived_sha256"] != evidence["hash"]
                or sha256(folder / "center_raw.mat") != extracted["raw_sha256"]):
            raise ValueError(f"capture or derived checksum mismatch: {case}")
        info = extracted["execution"]
        if (info["stopEvent"] != "ReachedStopTime" or np.size(info["errorDiagnostic"])
                or np.size(info["simulationErrorMessage"])
                or info["solverInfo"]["Solver"] != SOLVER["Solver"]
                or info["solverInfo"]["FixedStepSize"] != float(SOLVER["FixedStep"])):
            raise ValueError(f"invalid execution record: {case}")
        extracts[case] = extracted
        responses[case] = evidence["response"]
    reference = loadmat(reference_dir / "center_extracted.mat", simplify_cells=True)
    if sha256(reference_dir / "center_raw.mat") != reference["raw_sha256"]:
        raise ValueError("original 0.2 s reference checksum mismatch")
    opening = float(responses["outlet_opening"]["first_change_s"])
    t = responses["normal"]["area"]["time"]
    solver_grid(t, float(SOLVER["FixedStep"]), float(SOLVER["StopTime"]))
    before = t < opening
    after = t >= opening
    sensor_results = {}
    for channel, name in CAPTURE.items():
        signals = [record["sensors"][name] for record in (reference, *(extracts[key] for key in CASES))]
        unit = "MPa" if channel.startswith("PS") else "kg/s"
        if any(not np.array_equal(t, y["time"]) or visible_unit(y["unit"]) != unit
               or np.shape(y["values"]) != t.shape or not np.isfinite(y["values"]).all() for y in signals):
            raise ValueError(f"incompatible runtime sensor history: {channel}")
        original, control, intervention = [y["values"] for y in signals]
        sensor_results[channel] = {
            "unit": unit, "control_minus_original_normal": metrics(control, original, t),
            "pre_event": metrics(intervention[before], control[before], t[before]),
            "post_event": metrics(intervention[after], control[after], t[after]),
        }
    rates = [responses[key]["signed_outlet_flow"] for key in CASES]
    if any(not np.array_equal(t, rate["time"]) or rate["unit"] != "kg/s" for rate in rates):
        raise ValueError("incompatible outlet clocks or units")
    difference = rates[1]["values"] - rates[0]["values"]
    write_json(output, {"status": "REVIEW_REQUIRED", "opening_s": opening,
                        "execution": {key: extracts[key]["execution"] for key in CASES},
                        "measured_outlet_delta_kg_s": {"min_post": float(difference[after].min()),
                                                      "max_post": float(difference[after].max()),
                                                      "pre_event_max_abs": float(abs(difference[before]).max())},
                        "sensors": sensor_results,
                        "qualification": "Review pre-event agreement and the measured incremental atmospheric flow. A single engineered event is not independent diagnostic evaluation."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("audit", "prepare", "approve", "analyze"))
    parser.add_argument("path", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    normal = RAW_DATASET_DIR / MODEL_DIR / f"{MODEL}.slx"
    if args.action == "prepare":
        prepare(args.path, normal)
    elif args.action == "approve":
        approve(args.path)
    elif args.action == "analyze":
        if args.reference is None or args.output is None:
            parser.error("analyze requires --reference and --output")
        analyze(args.path, args.reference, args.output)
    else:
        args.path.mkdir(parents=True)
        write_json(args.path / "source_difference.json", source_evidence(normal, RAW_DATASET_DIR / ANOMALOUS))
        write_json(args.path / "experiment.json", specification())


if __name__ == "__main__":
    main()
