"""Audit Center NORMAL mass and analyze prepared resolution cases when captured."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_simpson, cumulative_trapezoid
from scipy.io import loadmat

from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT
from .phase2 import DATA_HASH, MODEL, MODEL_DIR, MODEL_HASH, PARQUET, SID, checked_file
from .phase10 import CAPTURE, capture_data, exact_pairs, json_value, metrics, sha256, solver_grid, visible_unit

PHASE10 = WORKSPACE_ROOT / "03_results/validation/phase10_center_normal/comparison.json"
BOUNDARIES = dict(zip(("Reservoir", "Reservoir_G", "Reservoir_G1", "Reservoir_G2",
                       "Reservoir_G3", "Reservoir_G4"), ("1", "195", "200", "217", "224", "316")))
EVENTS = (10.0, 25.0)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, record):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2, allow_nan=False, default=json_value)
        stream.write("\n")


def prepare(baseline, destination, reference):
    source = checked_file(baseline / f"{MODEL}.slx", MODEL_HASH)
    baseline_hash = sha256(baseline / "center_setup.mat")
    if baseline_hash != reference["capture_hashes"]["center_setup.mat"]:
        raise ValueError("baseline setup differs from the Phase 10 capture")
    destination = destination.resolve()
    if destination.is_relative_to(WORKSPACE_ROOT.resolve()):
        raise ValueError("convergence cases must be outside the repository")
    destination.mkdir(parents=True)
    for step in (0.4, 0.2):
        case = destination / f"step_{step:.1f}"
        case.mkdir()
        copy = case / source.name
        with source.open("rb") as src, copy.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        checked_file(copy, MODEL_HASH)
        write_json(case / "case.json", {"step_s": step, "baseline_setup_sha256": baseline_hash,
                                        "model_sha256": MODEL_HASH, "stop_s": 20000,
                                        "solver": "ode14x"})


def mass_integrals(time, boundary, storage, event_right_index):
    """Compare integrators and isolate the bracket containing a discontinuity."""
    dt = np.diff(time)
    if not (dt > 0).all() or not 1 <= event_right_index < len(time):
        raise ValueError("invalid clock or event bracket")
    trap = cumulative_trapezoid(boundary, time, initial=0)
    simpson = cumulative_simpson(boundary, x=time, initial=0)
    j = event_right_index
    correction = (boundary[j] - boundary[j-1]) * dt[j-1] / 2
    left_jump = trap.copy()
    left_jump[j:] -= correction
    smooth = cumulative_simpson(boundary[:j], x=time[:j], initial=0)
    after = cumulative_simpson(boundary[j:], x=time[j:], initial=0)
    split = np.r_[smooth, smooth[-1] + boundary[j-1] * dt[j-1] + after]
    return pd.DataFrame({
        "time_s": time, "boundary_net_kg_s": boundary, "storage_kg": storage,
        "storage_change_kg": storage - storage[0], "trapezoid_kg": trap, "simpson_kg": simpson,
        "step_left_trapezoid_kg": left_jump, "step_split_simpson_kg": split,
        "trapezoid_residual_kg": storage - storage[0] - trap,
        "simpson_residual_kg": storage - storage[0] - simpson,
        "step_left_trapezoid_residual_kg": storage - storage[0] - left_jump,
        "step_split_simpson_residual_kg": storage - storage[0] - split,
    })


def conservation(extracted, reference, step):
    traces = {row["path"]: row for row in extracted["logSeries"]}
    clock = traces["Reservoir/mdot_A"]["time"]
    solver_grid(clock, step, 20000)

    def signal(name, unit):
        row = traces[name]
        if (row["unit"] != unit or np.shape(row["values"]) != clock.shape or not np.array_equal(clock, row["time"])
                or not np.isfinite(row["values"]).all()):
            raise ValueError(f"unsupported conservation series {name}")
        return row["values"]

    boundary = np.zeros(len(clock))
    through = np.zeros(len(clock))
    for name in BOUNDARIES:
        flow = signal(f"{name}/mdot_A", "kg/s")
        boundary -= flow
        through += abs(flow)
    storage = np.zeros(len(clock))
    for name, row in reference["physics"]["storage"].items():
        density = signal(f"{name}/rho_I", "kg/m^3")
        if (density <= 0).any():
            raise ValueError(f"nonpositive density for {name}")
        storage += row["volume_m3"] * density
    ports = np.zeros(len(clock))
    for name in reference["physics"]["storage"]:
        ports += signal(f"{name}/mdot_A", "kg/s")
        if name.startswith("Pipe_"):
            ports += signal(f"{name}/mdot_B", "kg/s")
    step_cmd = signal("PS_Step/O", "Pa")
    j = np.flatnonzero(step_cmd > (step_cmd[0] + step_cmd[-1]) / 2)[0]
    result = mass_integrals(clock, boundary, storage, j)
    gross = float(cumulative_trapezoid(through, clock)[-1])
    residual = result.trapezoid_residual_kg.to_numpy()
    peak = np.argmax(abs(np.diff(residual))) + 1
    return result, {
        "step_s": step, "samples": len(clock), "pointwise_max_abs_boundary_minus_storage_port_kg_s": float(abs(boundary-ports).max()),
        "clock_quality": {"first": float(clock[0]), "last": float(clock[-1]),
                          "duplicate_times": len(clock)-len(np.unique(clock)),
                          "minimum_spacing_s": float(np.diff(clock).min())},
        "initial_storage_kg": float(storage[0]), "final": result.iloc[-1].to_dict(),
        "gross_boundary_kg": gross, "trapezoid_final_abs_fraction_of_gross": abs(float(residual[-1]))/gross,
        "trapezoid_final_abs_fraction_of_storage_change": abs(float(residual[-1]) / float(storage[-1]-storage[0])),
        "largest_single_interval_residual_change": result.iloc[[peak-1, peak]].to_dict("records"),
        "step_bracket": result.iloc[[j-1,j]].to_dict("records"),
        "ramp_bracket": result.iloc[[np.searchsorted(clock,EVENTS[0])-1,np.searchsorted(clock,EVENTS[0])]].to_dict("records"),
        "jump_treatment": "Left-held net flow over the interval ending at the first post-step observation; "
                          "sensitivity estimate, with no claim of resolved between-knot flow."}


def model_diff(normal, anomaly):
    def parameters(block):
        return {item.get("Name"): item.text for item in block.iter("P")
                if item.get("Name") not in {"Position", "ZOrder", "Location", "FontSize", "NameLocation", "Priority"}}

    def delta(a, b):
        return {key: [a.get(key), b.get(key)] for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)}

    def wires(root):
        return Counter(tuple(sorted(p.text for p in line.iter("P") if p.get("Name") in {"Src","Dst"}))
                       for line in root.findall("Line"))

    with ZipFile(normal) as a, ZipFile(anomaly) as b:
        root_a, root_b = [ET.fromstring(z.read("simulink/systems/system_root.xml")) for z in (a,b)]
        ba, bb = [{item.get("SID"): item for item in root.findall("Block")} for root in (root_a,root_b)]
        pa, pb = [parameters(ET.fromstring(z.read("simulink/configSet0.xml"))) for z in (a,b)]
        system_a, system_b = [{name for name in z.namelist() if name.startswith("simulink/systems/system")
                               and name != "simulink/systems/system_root.xml"} for z in (a,b)]
        children = {name: name in system_a and name in system_b and a.read(name) == b.read(name)
                    for name in sorted(system_a | system_b)}
        step = parameters(bb["563"])
        normal_restriction, variable_restriction = parameters(ba["213"]), parameters(bb["213"])
        return {
            "status": "BLOCKED", "sha256": sha256(anomaly), "lineage": "Local archived anomalous Center candidate. Generating-run ancestry is unverified.",
            "added_blocks": {key: bb[key].get("Name") for key in sorted(bb.keys()-ba.keys())},
            "removed_blocks": {key: ba[key].get("Name") for key in sorted(ba.keys()-bb.keys())},
            "changed_common_blocks": {key: changes for key in sorted(ba.keys() & bb.keys())
                                     if (changes := delta(parameters(ba[key]),parameters(bb[key])))},
            "added_connections": sorted((wires(root_b)-wires(root_a)).elements()),
            "removed_connections": sorted((wires(root_a)-wires(root_b)).elements()),
            "child_system_bytes_equal": children, "configuration_deltas": delta(pa,pb),
            "sid_213": {"normal_area_m2": float(normal_restriction["restriction_area"]),
                        "candidate_min_area_m2": float(variable_restriction["min_area"]),
                        "affected_branch": "Main gas junction at PS1 to flow sensor SID 218 (MFS3) and downstream reservoir SID 200"},
            "sid_563": {key: step[key] for key in ("step_time","step_time_unit","initial_value","initial_value_unit","final_value","final_value_unit")},
            "blocker": "The area command is identical before and after the configured step. A restricted branch "
                       "has static topology evidence, but a nonzero leak opening, effective onset, label lineage, "
                       "and independently verified localization truth do not."}


def release_findings(capture):
    frame = pd.read_parquet(checked_file(RAW_DATASET_DIR / PARQUET, DATA_HASH))
    x, y = exact_pairs(capture.index, frame.index)
    t = capture.index.to_numpy(dtype=float)[x]
    out = {}
    for channel in SID:
        residual = frame[channel].to_numpy()[y] - capture[channel].to_numpy()[x]
        total = np.dot(residual,residual)
        out[channel] = {}
        for lo, hi in ((0,10),(10,25),(25,160),(160,1000),(1000,20001)):
            select = (t >= lo) & (t < hi)
            error = residual[select]
            out[channel][f"{lo}:{hi}"] = {"samples": len(error), "max_absolute": float(abs(error).max()),
                                          "rmse": float(np.sqrt(np.mean(error**2))),
                                          "squared_error_fraction": float(np.dot(error,error)/total) if total else None}
    return out


def verify_extraction(run, path):
    extracted = loadmat(path, simplify_cells=True)
    if sha256(run/"center_raw.mat") != extracted["raw_sha256"]:
        raise ValueError("extraction is not bound to this raw capture")
    execution = extracted["execution"]
    if (execution["stopEvent"] != "ReachedStopTime" or np.size(execution["errorDiagnostic"])
            or np.size(execution["simulationErrorMessage"])):
        raise ValueError("unsuccessful simulation")
    return extracted


def audit(baseline, extraction, output, reference):
    extracted = verify_extraction(baseline,extraction)
    frames, stats = conservation(extracted, reference, 0.8)
    phase10 = reference["physics"]["mass_balance"]
    if not np.isclose(stats["final"]["trapezoid_residual_kg"],phase10["final_storage_minus_integrated_net_kg"],rtol=0,atol=1e-7):
        raise ValueError("Phase 10 calculation did not reproduce")
    normal = checked_file(baseline/f"{MODEL}.slx",MODEL_HASH)
    anomaly = RAW_DATASET_DIR / "MATLAB_SIMSCAPE_Simulation/anomalous_scenarios/Anomalous_HNetwork_gest_center.slx"
    capture, _ = capture_data(baseline,extracted)
    output.mkdir(parents=True)
    frames.to_csv(output/"baseline_mass.csv",index=False)
    plot_mass({"0.8 s baseline":frames},output/"baseline_mass.png")
    write_json(output/"static_audit.json", {
        "baseline_raw_sha256": extracted["raw_sha256"], "baseline_extraction_sha256": sha256(extraction),
        "inventory": {"boundary_sids_all_at_A": BOUNDARIES, "boundary_sign_into_network_factor": -1,
                      "storage_m3": {key: value["volume_m3"] for key,value in reference["physics"]["storage"].items()},
                      "method": "Internal density in kg/m^3 times each fixed component volume; pipe volume is length times cross-section."},
        "mass": stats, "candidate": model_diff(normal,anomaly),
        "release_exact_knot_epochs": release_findings(capture),
        "release_28s": reference["discrepancies"]["release_at_28_s"],
        "release_required_evidence": "Authoritative generating-run identity, original solver timestamps and raw sensor vectors, and the exact Center preprocessing code and version.",
        "convergence": "PENDING_EXECUTION"})


def plot_mass(cases, output):
    from matplotlib import pyplot as plt

    fig, axes = plt.subplots(2,1,layout="constrained",figsize=(8,6))
    for name, case in cases.items():
        for ax in axes:
            ax.plot(case.time_s,case.trapezoid_residual_kg,label=name)
            ax.plot(case.time_s,case.step_left_trapezoid_residual_kg,"--",label=f"{name}, step sensitivity")
    axes[0].set_xlim(0,50)
    axes[0].legend()
    for ax in axes:
        ax.set_ylabel("Storage minus integrated flow (kg)")
    axes[-1].set_xlabel("Saved time (s)")
    fig.savefig(output,dpi=140)
    plt.close(fig)


def shared_solver_grid(coarse, fine, coarse_step, fine_step):
    stride = round(coarse_step / fine_step)
    if stride < 1 or coarse_step != stride * fine_step:
        raise ValueError("non-nested solver steps")
    t = coarse.index.to_numpy(dtype=float)
    paired = fine.iloc[::stride]
    other = paired.index.to_numpy(dtype=float)
    if len(t) != len(other):
        raise ValueError("fine solver grid has incomplete shared support")
    offsets = abs(t - other)
    if (offsets > 8 * np.spacing(np.maximum(1, abs(t)))).any():
        raise ValueError("fine solver ticks do not correspond to coarse grid")
    return paired, t, float(offsets.max())


def validate_case(step, run, path, reference, baseline_setup):
    """Bind an extracted run to its raw capture and archived configuration evidence."""
    fine = step != 0.8
    log_name = "center_convergence_execution.log" if fine else "interactive_capture_preflight_passed.log"
    marker = "=== CONVERGENCE CAPTURE COMPLETED ===" if fine else "=== CAPTURE COMPLETED ==="
    if marker not in (run / log_name).read_text(encoding="utf-8"):
        raise ValueError(f"completion marker missing at {step}")
    files = [f"{MODEL}.slx", "center_setup.mat", "center_raw.mat", log_name,
             *(f"{name}.csv" for name in CAPTURE.values())]
    if fine:
        files += ["case.json", "center_solver_delta.mat"]
    hashes = {name: sha256(run / name) for name in files}
    if hashes[f"{MODEL}.slx"] != MODEL_HASH:
        raise ValueError("isolated source hash differs")
    if not fine and hashes != reference["capture_hashes"]:
        raise ValueError("baseline capture differs from Phase 10")
    extracted = verify_extraction(run, path)
    execution = extracted["execution"]
    solver = execution["solverInfo"]
    if (solver["Type"] != "Fixed-Step" or solver["Solver"] != "ode14x"
            or solver["FixedStepSize"] != step or execution["start_s"] != 0 or execution["stop_s"] != 20000):
        raise ValueError(f"solver or horizon mismatch at {step}")
    setup = loadmat(run / "center_setup.mat", simplify_cells=True)
    if float(setup["configured"]["FixedStep"]) != step:
        raise ValueError("saved setup step differs from runtime")
    limits = []
    if fine:
        manifest = read_json(run / "case.json")
        delta = loadmat(run / "center_solver_delta.mat", simplify_cells=True)
        changed = np.asarray(delta["parameters"])[np.asarray(delta["changed"], dtype=bool)]
        if (manifest["step_s"] != step or manifest["model_sha256"] != MODEL_HASH
                or manifest["baseline_setup_sha256"] != reference["capture_hashes"]["center_setup.mat"]
                or manifest["stop_s"] != 20000 or manifest["solver"] != "ode14x"
                or list(changed) != ["FixedStep"] or delta["before"] != baseline_setup["configured"]
                or delta["after"] != setup["configured"] or delta["localSolverBefore"] != "off"):
            raise ValueError(f"invalid resolution configuration delta at {step}")
        for key in ("original", "configured", "inputMap", "physicalInputs", "gasBlocks", "gasSettings", "release", "products"):
            a, b = setup[key], baseline_setup[key]
            if key == "configured":
                a, b = ({k: v for k, v in cfg.items() if k != "FixedStep"} for cfg in (a, b))
            if json.dumps(a, sort_keys=True, default=json_value) != json.dumps(b, sort_keys=True, default=json_value):
                raise ValueError(f"{key} differs from baseline")
        limits = np.atleast_1d(delta["unavailable"]).tolist()
    frame, integrity = capture_data(run, extracted)
    for sensor, row in integrity.items():
        pressure = sensor.startswith("PS")
        if (not row["csv_values_equal_mat"] or not row["csv_timestamps_equal_mat"]
                or not row["strictly_increasing"] or row["invalid_timestamps"]
                or row["duplicates"] or row["nan_or_missing"] or row["infinite"]
                or row["mat_time_unit"] != "seconds" or visible_unit(row["mat_data_unit"]) != ("MPa" if pressure else "kg/s")
                or pressure and row["min"] <= 0):
            raise ValueError(f"sensor integrity failed for {sensor} at {step}")
        row["mat_data_unit"] = visible_unit(row["mat_data_unit"])
        solver_grid(extracted["sensors"][CAPTURE[sensor]]["time"], step, 20000)
    return extracted, frame, {"execution": execution, "setup": setup["configured"],
                               "unavailable_solver_enumeration_fields": limits, "file_hashes": hashes,
                               "extraction_sha256": sha256(path), "sensors": integrity,
                               "runtime": setup["release"], "products": setup["products"]}


def analyze(baseline, extraction, cases, output, reference):
    output.mkdir(parents=True)
    series, records, frames, rows, event_rows, mass_rows = {}, {}, {}, [], [], []
    baseline_setup = loadmat(baseline / "center_setup.mat", simplify_cells=True)
    for step in (0.8, 0.4, 0.2):
        run = baseline if step == 0.8 else cases / f"step_{step:.1f}"
        path = extraction if step == 0.8 else run / "center_extracted.mat"
        extracted, frame, integrity = validate_case(step, run, path, reference, baseline_setup)
        mass, record = conservation(extracted, reference, step)
        before, after = record["step_bracket"]
        event = {"step_s": step, "configured_step_s": 25,
                 "last_saved_pre_step_s": before["time_s"], "first_saved_post_step_s": after["time_s"],
                 "pre_flow_kg_s": before["boundary_net_kg_s"], "post_flow_kg_s": after["boundary_net_kg_s"],
                 "bracket_storage_change_kg": after["storage_kg"] - before["storage_kg"],
                 "bracket_trapezoid_kg": after["trapezoid_kg"] - before["trapezoid_kg"],
                 "bracket_left_hold_kg": after["step_left_trapezoid_kg"] - before["step_left_trapezoid_kg"],
                 "bracket_trapezoid_residual_change_kg": after["trapezoid_residual_kg"] - before["trapezoid_residual_kg"],
                 "post_step_minus_configured_s": after["time_s"] - 25,
                 "coincident_pre_and_post_limits_logged": False}
        event_rows.append(event)
        end = record["final"]
        for rule in ("trapezoid", "simpson", "step_left_trapezoid", "step_split_simpson"):
            error = end[f"{rule}_residual_kg"]
            mass_rows.append({"step_s": step, "method": rule, "initial_storage_kg": record["initial_storage_kg"],
                              "final_storage_kg": end["storage_kg"], "storage_change_kg": end["storage_change_kg"],
                              "integrated_net_kg": end[f"{rule}_kg"], "residual_kg": error,
                              "absolute_residual_fraction_of_storage_change": abs(error / end["storage_change_kg"]),
                              "absolute_residual_fraction_of_gross": abs(error / record["gross_boundary_kg"])})
        records[str(step)] = {**record, **integrity, "event": event}
        frames[step] = frame
        series[f"{step} s"] = mass
        mass.to_csv(output / f"mass_{step}.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    for coarse, fine in ((0.8, 0.4), (0.4, 0.2), (0.8, 0.2)):
        frame = frames[coarse]
        paired, t, delta = shared_solver_grid(frame, frames[fine], coarse, fine)
        for channel in SID:
            for window, keep in {"entire": np.ones(len(t), dtype=bool), "step_20_40": (20 <= t) & (t <= 40),
                                 "outside_step": (t < 20) | (t > 40),
                                 "later_40_1000": (40 < t) & (t <= 1000), "late_1000_20000": t > 1000,
                                 "final": t == 20000}.items():
                rows.append({"coarse_step_s": coarse, "fine_step_s": fine, "sensor": channel, "window": window,
                             "unit": "MPa" if channel.startswith("PS") else "kg/s",
                             "max_paired_timestamp_delta_s": delta,
                             **metrics(paired[channel].to_numpy()[keep], frame[channel].to_numpy()[keep], t[keep])})
    base, t, _ = shared_solver_grid(frames[0.8], frames[0.4], 0.8, 0.4)
    finest, _, _ = shared_solver_grid(frames[0.8], frames[0.2], 0.8, 0.2)
    empirical = {}
    for channel in SID:
        medium, fine, coarse = (f[channel].to_numpy() for f in (base, finest, frames[0.8]))
        previous, successive = metrics(medium, coarse, t), metrics(fine, medium, t)
        # Values below this floor are dominated by observed near-roundoff channel variations.
        resolved = max(previous["max_absolute"], successive["max_absolute"]) > 1e-11
        ratio = successive["rmse"] / previous["rmse"] if resolved and previous["rmse"] else None
        empirical[channel] = {"coarse_medium": previous, "medium_fine": successive,
                              "successive_rmse_ratio": ratio, "ratio_floor_native_units": 1e-11,
                              "successive_rmse_decreases": ratio < 1 if ratio is not None else None}
    resolvable = [entry["successive_rmse_decreases"] for entry in empirical.values()
                  if entry["successive_rmse_decreases"] is not None]
    split_improves = all(abs(record["final"]["step_split_simpson_residual_kg"]) <
                         abs(record["final"]["trapezoid_residual_kg"]) for record in records.values())
    pd.DataFrame(rows).to_csv(output / "per_sensor.csv", index=False)
    pd.DataFrame(mass_rows).to_csv(output / "mass_balance.csv", index=False)
    pd.DataFrame(event_rows).to_csv(output / "event_window.csv", index=False)
    plot_mass(series, output / "convergence_mass.png")
    plot_event(series, output / "pressure_step.png")
    write_json(output / "convergence.json", {
        "schema": "phase11-center-convergence/2", "cases": records, "per_sensor": rows,
        "mass_balance": mass_rows, "event_window": event_rows, "successive_differences_on_0_8_s_grid": empirical,
        "empirical_summary": {"channels_with_resolvable_differences": len(resolvable),
                              "channels_with_decreased_successive_rmse": sum(resolvable),
                              "split_simpson_improves_all_cases": split_improves},
        "scientific_status": {
            "three_case_execution_integrity": "VERIFIED",
            "numerical_sensor_convergence": "PARTIALLY VERIFIED" if any(resolvable) else "UNVERIFIED",
            "integrated_mass_conservation": "PARTIALLY VERIFIED" if split_improves else "UNVERIFIED",
            "archived_model_source_reproduction": "VERIFIED",
            "exact_clean_release_reproduction": "CONTRADICTED",
            "physical_hydrogen_fidelity": "UNVERIFIED",
            "controlled_normal_leak_eligibility": "UNVERIFIED",
        },
        "methods": {"clock": "Decimate nested saved grids to the coarser grid of each pair; check all pairs within "
                             "8 binary64 spacings, with no interpolation. Solver grids are independently verified.",
                    "difference": "Fine minus coarse in native units, computed in binary64.",
                    "event_integration": "Keep the preceding rate on the bracket ending at the first saved post-step sample. "
                                         "Apply trapezoid or Simpson separately elsewhere. Bracket is a sensitivity estimate.",
                    "order": "Successive ratios demonstrate empirical differences only, without an inferred formal order."},
        "prior_evidence": {"release_28s": reference["discrepancies"]["release_at_28_s"],
                           "leak_candidate": "BLOCKED; archived area command has identical initial and final values."}})


def plot_event(cases, output):
    from matplotlib import pyplot as plt

    fig, axes = plt.subplots(2, 1, sharex=True, layout="constrained", figsize=(8, 6))
    for name, case in cases.items():
        focus = case[(case.time_s >= 23) & (case.time_s <= 29)]
        line, = axes[0].plot(focus.time_s, focus.boundary_net_kg_s, ".-", ms=4, label=name)
        axes[1].plot(focus.time_s, focus.trapezoid_residual_kg, ".-", ms=4, color=line.get_color())
        axes[1].plot(focus.time_s, focus.step_left_trapezoid_residual_kg, "--", color=line.get_color())
    for axis in axes:
        axis.axvline(25, color="0.5", lw=1, linestyle=":")
    axes[0].legend(title="Fixed step")
    axes[0].set_ylabel("Net boundary flow (kg/s)")
    axes[1].set_ylabel("Conservation residual (kg)")
    axes[1].set_xlabel("Saved time (s), configured step at 25 s")
    axes[1].set_title("Solid: trapezoid. Dashed: left-held event bracket.")
    fig.savefig(output, dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=("prepare","audit","analyze"))
    parser.add_argument("baseline",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--extraction",type=Path)
    parser.add_argument("--cases",type=Path)
    args = parser.parse_args()
    reference = read_json(PHASE10)
    if args.action == "prepare":
        prepare(args.baseline,args.output,reference)
    elif args.extraction is None:
        parser.error("--extraction is required")
    elif args.action == "audit":
        audit(args.baseline,args.extraction,args.output,reference)
    elif args.cases is None:
        parser.error("--cases is required for analyze")
    else:
        analyze(args.baseline,args.extraction,args.cases,args.output,reference)


if __name__ == "__main__":
    main()
