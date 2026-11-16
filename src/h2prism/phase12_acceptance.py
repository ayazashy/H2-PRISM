"""Read-only acceptance audit for the numeric Center Phase 12 NORMAL capture."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
from scipy.io import loadmat

from .data.loader import WORKSPACE_ROOT
from .phase2 import MODEL, MODEL_HASH
from .phase10 import CAPTURE, metrics, quality, sha256, solver_grid, visible_unit
from .phase11 import BOUNDARIES, PHASE10, conservation, read_json, write_json
from .phase12 import AREA, CASES, SOLVER, paired_design_xml, specification

REPORT11 = WORKSPACE_ROOT / "03_results/validation/phase11_center_convergence/convergence.json"
POLICY = ("SignalLogging", "SaveState", "SaveOutput", "SaveFinalState")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def same(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return np.array_equal(a, b)


def mat(path):
    return {k: v for k, v in loadmat(path, simplify_cells=True).items() if not k.startswith("__")}


def trace(signal, clock, unit, name):
    values = np.asarray(signal["values"], dtype=float)
    require(visible_unit(signal["unit"]) == unit, f"{name}: unexpected units")
    require(values.shape == clock.shape and np.array_equal(signal["time"], clock)
            and np.isfinite(values).all(), f"{name}: incomplete, nonfinite or misaligned samples")
    return values


def normal_area(values):
    require(np.array_equal(values, np.full(values.shape, float(AREA["initial_value"]))),
            "NORMAL outlet area changed or differs from the intended plateau")


def range_record(values):
    return {"min": float(values.min()), "max": float(values.max()),
            "initial": float(values[0]), "final": float(values[-1])}


def verify_pair(root, previous, spec=None):
    spec = specification() if spec is None else spec
    provenance_path = root / "retry_provenance.json"
    provenance = read_json(provenance_path) if previous is not None else None
    approval = read_json(root / "approval.json")
    digest = sha256(root / "approval.json")
    if previous is not None:
        require(digest == provenance["fresh_approval_sha256"] == provenance["prior_approval_sha256"]
                == sha256(previous / "approval.json"), "approval receipt checksum mismatch")
    require(approval["schema"] == "center-phase12-paired-preflight/1", "unexpected approval schema")
    cases = {}
    derived = []
    for name in CASES:
        target = root / name
        files = {f: sha256(target / f) for f in (f"{MODEL}.slx", "Center_phase12.slx", "preflight.json", "design.json")}
        expected = approval["cases"][name]
        require((provenance is None or files == provenance["copied_input_sha256"][name]) and
                files[f"{MODEL}.slx"] == MODEL_HASH and files["Center_phase12.slx"] == expected["derived_sha256"]
                and files["preflight.json"] == expected["preflight_sha256"]
                and files["design.json"] == expected["design_sha256"], f"{name}: approval input checksum mismatch")
        preflight = read_json(target / "preflight.json")
        require(read_json(target / "design.json") == {"case": name, **spec} and
                preflight["case"] == name and preflight["compile_status"] == "PASSED"
                and preflight["source_sha256"] == MODEL_HASH
                and preflight["derived_sha256"] == files["Center_phase12.slx"]
                and preflight["solver"] == SOLVER
                and preflight["location"] == spec["location"]
                and preflight["existing_block_links_parameters_and_connections_unchanged"]
                and preflight["command_final_area_m2"] == spec["area"]["normal_final" if name == "normal" else "intervention_final"],
                f"{name}: invalid preflight")
        derived.append(target / "Center_phase12.slx")
        cases[name] = {"input_sha256": files, "preflight": preflight}
    require(same(cases["normal"]["preflight"]["products"], cases["outlet_opening"]["preflight"]["products"])
            and cases["normal"]["preflight"]["version"] == cases["outlet_opening"]["preflight"]["version"],
            "preflight runtimes differ")
    delta = paired_design_xml(derived, spec)
    require(delta == approval["allowed_saved_xml_delta"], "pair diff disagrees with approval")
    return {"approval_sha256": digest, "retry_provenance_sha256": sha256(provenance_path) if provenance is not None else None,
            "saved_model_delta": delta, "configset_json_checked": True, "cases": cases}


def audit(root, previous, reference_dir, case="normal", spec=None):
    spec = specification() if spec is None else spec
    area = spec["area"]
    location = spec["location"]
    require(case in CASES, "unknown Phase 12 case")
    pair = verify_pair(root, previous, spec)
    folder = root / case
    files = ("execution.log", "stages.log", "center_raw.mat", "center_extracted.mat",
             "sensor_checkpoint.mat", "outlet_evidence.mat", "logging_policy.mat")
    stages = (folder / "stages.log").read_text().splitlines()
    require(stages == ["SIM_STARTED", "SIM_RETURNED", "NUMERIC_EXTRACTION_STARTED", "NUMERIC_CAPTURE_SAVED"],
            "execution stages are incomplete or unexpected")
    require((folder / "execution.log").read_text().strip() == "=== PHASE 12 CAPTURE COMPLETED ===",
            "completion marker missing or unexpected execution output")
    hashes = {name: sha256(folder / name) for name in files}
    raw, extracted, check, outlet, policy = [mat(folder / name) for name in files[2:]]
    model_hash = pair["cases"][case]["input_sha256"]["Center_phase12.slx"]
    require(extracted.pop("raw_sha256") == hashes["center_raw.mat"] and same(raw, extracted),
            "raw and extracted content differ")
    require(same(check, {k: raw[k] for k in ("execution", "sensors")}), "sensor checkpoint differs")
    require(raw["approved_model_sha256"] == outlet["hash"] == policy["hash"] == model_hash,
            "logging policy, captured output or outlet evidence is not bound to the approved model")
    with ZipFile(folder / "Center_phase12.slx") as archive:
        info = json.loads(archive.read("simulink/configSetInfo.json"))["ConfigSetInfo"]
        active, = (item["PartName"].lstrip("/") for item in info if item["Active"])
        config = json.loads(archive.read(active))["_properties"]["Components"]["_elements"]
    saved, = (item["_properties"] for item in config if item["_object_class"] == "Simulink.DataIOCC")
    defaults = dict(zip(POLICY, ("on", "off", "on", "off")))
    require(tuple(policy["keys"]) == POLICY and list(policy["after"]) == ["off"] * len(POLICY)
            and all(saved.get(key, defaults[key]) == value for key, value in zip(POLICY, policy["before"])),
            "logging overrides disagree with the approved configuration")
    execution = raw["execution"]
    require(execution["stopEvent"] == "ReachedStopTime" and execution["warningCount"] == 0
            and not any(np.size(execution[key]) for key in ("errorDiagnostic", "simulationErrorMessage", "warnings"))
            and execution["modelName"] == "Center_phase12"
            and execution["start_s"] == 0 and execution["stop_s"] == 20000
            and execution["solverInfo"] == {"Type": "Fixed-Step", "Solver": "ode14x", "FixedStepSize": 0.2},
            "invalid execution metadata or solver configuration")

    refs = read_json(REPORT11)["cases"]["0.2"]
    ref_hash = sha256(reference_dir / "center_extracted.mat")
    require(ref_hash == refs["extraction_sha256"], "reference extraction differs from Phase 11")
    for name, digest in refs["file_hashes"].items():
        require(sha256(reference_dir / name) == digest, f"Phase 11 reference checksum mismatch: {name}")
    reference = mat(reference_dir / "center_extracted.mat")
    phase10 = read_json(PHASE10)
    clock = raw["sensors"]["pressure_sensor1"]["time"]
    grid_delta = solver_grid(clock, 0.2, 20000)
    pre = clock < float(area["step_time"])
    require(set(raw["sensors"]) == set(CAPTURE.values()), "capture does not have exactly the mapped sensor channels")
    logs = {row["path"]: row for row in raw["logSeries"]}
    overlay = spec.get("overlay")
    require(len(logs) == len(raw["logSeries"]) == (108 if overlay else 101) and not np.size(raw["logErrors"]),
            "missing or duplicate physical log paths, or extraction errors")
    for path, row in logs.items():
        require(isinstance(row["unit"], str) and bool(row["unit"]), f"{path}: absent unit")
        trace(row, clock, row["unit"], path)
    sensors, residuals = {}, []
    pressure_floor = float(phase10["setup"]["gasSettings"]["p_min_perfect"])
    for name, sensor in CAPTURE.items():
        unit = "MPa" if name.startswith("PS") else "kg/s"
        row = raw["sensors"][sensor]
        x = trace(row, clock, unit, sensor)
        y = trace(reference["sensors"][sensor], clock, unit, f"reference {sensor}")
        require(row["timeUnit"] == "seconds" and
                (unit != "MPa" or (x >= pressure_floor).all()), f"{sensor}: invalid clock unit or absolute pressure")
        proxy = phase10["physics"]["channels"][name]
        native = trace(logs[proxy["log_path"]], clock, proxy["log_unit"], proxy["log_path"])
        delta = float(abs(x - native * proxy["factor_log_to_csv"]).max())
        require(delta <= 1e-10, f"{sensor}: disagrees with the native physical sensor")
        sensors[name] = {**quality(clock, x), "unit": unit, "native_log_max_difference": delta}
        for window, mask in (("pre_1000_s", pre), ("at_or_after_1000_s", ~pre), ("entire", np.ones(len(clock), dtype=bool))):
            residuals.append({"sensor": name, "unit": unit, "window": window, **metrics(x[mask], y[mask], clock[mask])})

    commands = {}
    old_logs = {r["path"]: r for r in reference["logSeries"]}
    if overlay:
        physical = {port: trace(logs[f"Pressure_Source_G3/{port}"], clock, unit, f"SID 55 {port}")
                    for port, unit in (("mdot_A", "kg/s"), ("mdot_B", "kg/s"), ("A/p", "Pa"), ("B/p", "Pa"))}
        signed_source = {"into_A_kg_s": range_record(physical["mdot_A"]),
                         "into_B_kg_s": range_record(physical["mdot_B"]),
                         "max_abs_port_mass_residual_kg_s": float(np.max(np.abs(physical["mdot_A"] + physical["mdot_B"]))),
                         "max_abs_command_vs_pB_minus_pA_pa": float(np.max(np.abs(
                             physical["B/p"] - physical["A/p"] - logs["Pressure_Source_G3/P"]["values"])))}
        offset = float(overlay["normal_final"] if case == "normal" else overlay["intervention_final"]) * 1e6
        expected_overlay = np.where(clock < float(overlay["step_time"]), 0., offset)
        source = trace(logs["Phase13_Command_Offset/O"], clock, "Pa", "overlay step")
        out = trace(logs["Phase13_Command_Sum/O"], clock, "Pa", "overlay sum")
        base = trace(logs["Phase13_Command_Sum/I1"], clock, "Pa", "overlay base")
        require(np.allclose(source, expected_overlay, atol=1e-6, rtol=0)
                and np.allclose(out-base, expected_overlay, atol=1e-6, rtol=0)
                and np.any(clock == float(overlay["step_time"])), "overlay command or timing differs")
        require(np.allclose(out, logs[overlay["receiver_log"]]["values"], atol=1e-6, rtol=0)
                and min(out) >= overlay["min_pa"]-1e-6 and max(out) <= overlay["max_pa"]+1e-6,
                "receiver command differs or lies outside audited design range")
    for path, unit in (("Reservoir/P", "Pa"), ("Reservoir/T", "K"), ("PS_Step/O", "Pa"),
                       ("PS_Ramp/O", "Pa"), ("Pressure_Source_G1/P", "Pa"), ("Pressure_Source_G3/P", "Pa")):
        x = trace(logs[path], clock, unit, path)
        y = trace(old_logs[path], clock, unit, f"reference {path}")
        expected_delta = expected_overlay if overlay and path == overlay["receiver_log"] else 0
        delta = float(abs(x - y - expected_delta).max())
        require(delta <= (1e-6 if unit == "Pa" else 1e-10), f"{path}: a native boundary or operating command changed")
        commands[path] = {**range_record(x), "unit": unit, "max_abs_change_from_reference": delta}
    require(same(raw["commands"], {"reservoir_pressure": logs["Reservoir/P"],
                                   "reservoir_temperature": logs["Reservoir/T"]}), "command records disagree")
    response = outlet["response"]
    restriction = location.get("restriction_log_node", "Local_Restriction_G3")
    sink = location.get("sink_log_node", "Reservoir_G1")
    routes = {"area": ("Phase12_Outlet_Area/O", "m^2"), "restriction_area_input": (restriction+"/area_in", "m^2"),
              "signed_outlet_flow": (restriction+"/mdot_A", "kg/s"), "signed_sink_flow": (sink+"/mdot_A", "kg/s"),
              "upstream_pressure": (restriction+"/A/p", "Pa"), "downstream_pressure": (restriction+"/B/p", "Pa"),
              "sink_pressure": (sink+"/p_I", "Pa"), "sink_temperature": (sink+"/T_I", "K")}
    outlet_report = {}
    values = {}

    for key, (path, unit) in routes.items():
        x = trace(response[key], clock, unit, key)
        native_unit = logs[path]["unit"]
        factor = 1e6 if (native_unit, unit) == ("MPa", "Pa") else 1
        require(native_unit == unit or factor != 1, f"{path}: incompatible outlet evidence unit")
        y = trace(logs[path], clock, native_unit, path) * factor
        delta = float(abs(x-y).max())
        require(delta <= (1e-8 if unit == "Pa" else 1e-12), f"{path}: outlet evidence differs from raw")
        outlet_report[key] = {**range_record(x), "unit": unit, "max_abs_change_from_native": delta}
        values[key] = x
    if case == "normal" or (overlay and overlay["role"] == "internal_pressure"):
        require(not np.size(response["first_change_s"]), "NORMAL recorded an opening event")
        normal_area(values["area"])
        normal_area(values["restriction_area_input"])
        first = None
    else:
        expected = np.where(pre, float(area["initial_value"]), float(area["intervention_final"]))
        for key in ("area", "restriction_area_input"):
            require(np.allclose(values[key], expected, atol=1e-12, rtol=0),
                    f"{key}: differs from the approved opening command")
        first = float(clock[np.flatnonzero(abs(values["restriction_area_input"]-float(area["initial_value"]))>1e-12)[0]])
        require(first == float(area["step_time"]) == response["first_change_s"],
                "opening timing differs from the saved command or design")
    metered = {"218": "flow_sensor3", "311": "flow_sensor1"}.get(location["flow_sensor_sid"])
    if metered:
        require(np.allclose(values["signed_outlet_flow"], raw["sensors"][metered]["values"], atol=1e-8, rtol=0),
                "metered outlet does not agree with the native sensor")
    require(np.allclose(values["signed_outlet_flow"], values["signed_sink_flow"], atol=1e-8, rtol=0)
            and (values["signed_outlet_flow"] > 0).all() and (values["upstream_pressure"] > values["downstream_pressure"]).all()
            and np.allclose(values["sink_pressure"], 100000, atol=1e-4, rtol=0)
            and np.allclose(values["sink_temperature"], 293.15, atol=1e-6, rtol=0),
            "outlet sign, sink condition or nominal flow linkage is inconsistent")

    boundaries = {name: {"sid": sid, **range_record(-trace(logs[name+"/mdot_A"], clock, "kg/s", name))}
                  for name, sid in BOUNDARIES.items()}
    storage = {}
    for name in phase10["physics"]["storage"]:
        storage[name] = {}
        for suffix, unit in (("rho_I", "kg/m^3"), ("p_I", "MPa"), ("T_I", "K")):
            path = name + "/" + suffix
            y = trace(logs[path], clock, unit, path)
            require((y > 0).all(), f"{path}: nonpositive state")
            storage[name][suffix] = {"unit": unit, **range_record(y)}
    initial = {row["name"]: row["samples"] for row in raw["initial"]}
    require(len(initial) == len(raw["initial"]) and all(
        path in initial and initial[path]["firstTime"] == 0 and initial[path]["lastTime"] == 20000
        and np.array_equal(initial[path]["values"], logs[path]["values"][[0,-1]])
        and initial[path]["units"] == unit
        for name in storage for suffix, unit in (("rho_I", "kg/m^3"), ("p_I", "MPa"), ("T_I", "K"))
        for path in [name + "/" + suffix]), "physical initial-state samples disagree with histories")
    history, mass = conservation(raw, phase10, 0.2)
    if overlay:
        from .phase12_pair import event_integral
        knots = [mass["step_bracket"][1]["time_s"]]
        if offset:
            knots.append(float(overlay["step_time"]))
        if first is not None:
            knots.append(first)
        indices = tuple(int(np.searchsorted(clock,k)) for k in sorted(set(knots)))
        integrated = event_integral(clock,history.boundary_net_kg_s.to_numpy(),indices)
        mass["phase13_event_knots_s"] = sorted(set(knots))
        mass["phase13_event_aware_final_residual_kg"] = float(history.storage_change_kg.iloc[-1]-integrated[-1])
    return {"classification": "ACCEPTED", "authorized_next": "Execute only the approved outlet_opening twin" if case == "normal" else "Analyze completed pair",
            "runtime_model": execution, "stages": stages, "capture_hashes": hashes, "pair": pair,
            "logging_policy": dict(zip(POLICY, zip(policy["before"], policy["after"]))),
            "policy_hash_basis": "Computed from the completed file. Its payload is bound by the approved model hash; no independently recorded pre-run file digest exists.",
            "reference_extraction_sha256": ref_hash, "max_clock_grid_error_s": grid_delta,
            "sensors": sensors, "residuals": residuals, "native_commands": commands,
            "overlay": {"specification": overlay, "received_range_pa": range_record(out),
                        "first_changed_sample_s": float(overlay["step_time"]) if offset else None,
                        "signed_pressure_source": signed_source} if overlay else None,
            "outlet": {"histories": outlet_report, "sign": "Positive from restriction A toward atmospheric reservoir SID " + location["reservoir_sid"],
                       "first_received_area_change_s": first, "pre_1000_samples": int(pre.sum()), "at_or_after_1000_samples": int((~pre).sum())},
            "boundary_flows_positive_into_network_kg_s": boundaries, "storage": storage,
            "log_inventory": {"series": len(logs), "initial_samples": len(initial), "extraction_errors": 0},
            "mass_balance": mass,
            "limitations": ["Derived NORMAL is measurably different from the fixed-restriction historical reference.",
                            "The reference comparison is descriptive and carries no certified agreement tolerance.",
                            "Numerical logging retains the physical initial-state samples, with Simulink Dataset state logging disabled.",
                            "Opening runtime response, hydrogen fidelity and independent diagnostic validity remain unverified."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("previous", type=Path)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True)
    try:
        record = audit(args.root, args.previous, args.reference)
    except (OSError, ValueError, KeyError, TypeError) as error:
        write_json(args.output / "acceptance.json", {"classification": "REJECTED", "reason": str(error)})
        raise
    write_json(args.output / "acceptance.json", record)
    pd.DataFrame(record["residuals"]).to_csv(args.output / "sensor_comparison.csv", index=False)


if __name__ == "__main__":
    main()
