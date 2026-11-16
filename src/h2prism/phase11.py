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
from .phase10 import capture_data, exact_pairs, json_value, metrics, sha256, solver_grid

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
        if (row["unit"] != unit or not np.array_equal(clock, row["time"])
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
        storage += row["volume_m3"] * signal(f"{name}/rho_I", "kg/m^3")
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
    if extracted["execution"]["stopEvent"] != "ReachedStopTime" or np.size(extracted["execution"]["errorDiagnostic"]):
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


def analyze(baseline, extraction, cases, output, reference):
    output.mkdir(parents=True)
    series, rows, records = {}, [], {}
    base_frame = None
    paired = {}
    for step, run, path in [(0.8,baseline,extraction), *[
        (step,cases/f"step_{step:.1f}",cases/f"step_{step:.1f}"/"center_extracted.mat") for step in (0.4,0.2)]]:
        extracted = verify_extraction(run,path)
        if step != 0.8:
            manifest = read_json(run/"case.json")
            delta = loadmat(run/"center_solver_delta.mat",simplify_cells=True)
            changed = np.asarray(delta["parameters"])[np.asarray(delta["changed"],dtype=bool)]
            if (manifest["step_s"] != step or list(changed) != ["FixedStep"]
                    or extracted["execution"]["solverInfo"]["Solver"] != "ode14x"
                    or extracted["execution"]["start_s"] != 0 or extracted["execution"]["stop_s"] != 20000
                    or extracted["execution"]["solverInfo"]["FixedStepSize"] != step
                    or "CONVERGENCE CAPTURE COMPLETED" not in (run/"center_convergence_execution.log").read_text(encoding="utf-8")):
                raise ValueError(f"incomplete or invalid resolution case {step}")
            checked_file(run/f"{MODEL}.slx",MODEL_HASH)
        mass, record = conservation(extracted,reference,step)
        record["execution"] = extracted["execution"]
        record["raw_sha256"] = extracted["raw_sha256"]
        record["extraction_sha256"] = sha256(path)
        if step != 0.8:
            record["configuration_delta_sha256"] = sha256(run/"center_solver_delta.mat")
        records[str(step)] = record
        series[f"{step} s"] = mass
        mass.to_csv(output/f"mass_{step}.csv",index=False)
        frame, integrity = capture_data(run,extracted)
        if any(not (r["csv_values_equal_mat"] and r["csv_timestamps_equal_mat"]) for r in integrity.values()):
            raise ValueError(f"MAT to CSV export mismatch at {step}")
        if step == 0.8:
            base_frame = frame
            continue
        t = base_frame.index.to_numpy(dtype=float)
        stride = round(0.8/step)
        finer = frame.iloc[::stride]
        paired_offsets = abs(t-finer.index.to_numpy(dtype=float))
        if (paired_offsets > 8*np.spacing(np.maximum(1,abs(t)))).any():
            raise ValueError("fine solver ticks do not correspond to baseline")
        records[str(step)]["max_paired_clock_delta_s"] = float(paired_offsets.max())
        paired[step] = finer
        for channel in SID:
            for stage, select in {"entire": np.ones(len(t),dtype=bool),"step_20_40": (20<=t)&(t<=40),
                                  "later_40_1000": (40<t)&(t<=1000),"late_1000_20000": t>1000,
                                  "final": t==20000}.items():
                rows.append({"step_s": step, "sensor": channel, "window": stage,
                             **metrics(finer[channel].to_numpy()[select],base_frame[channel].to_numpy()[select],t[select])})
    empirical = {}
    for channel in SID:
        medium, fine = (paired[step][channel].to_numpy() for step in (0.4, 0.2))
        coarse = base_frame[channel].to_numpy()
        coarse_medium = metrics(medium,coarse,t)
        medium_fine = metrics(fine,medium,t)
        ratio = medium_fine["rmse"] / coarse_medium["rmse"] if coarse_medium["rmse"] else None
        empirical[channel] = {"coarse_medium": coarse_medium, "medium_fine": medium_fine,
                              "successive_rmse_ratio": ratio,
                              "successive_rmse_decreases": ratio < 1 if ratio is not None else None}
    residual_sensitivity = {}
    for method in ("trapezoid", "simpson", "step_left_trapezoid", "step_split_simpson"):
        key = f"{method}_residual_kg"
        values = [abs(records[str(step)]["final"][key]) for step in (0.8, 0.4, 0.2)]
        residual_sensitivity[method] = {"absolute_residual_kg_coarse_to_fine": values,
                                        "monotonic_decrease": values[0] > values[1] > values[2]}
    pd.DataFrame(rows).to_csv(output/"per_sensor.csv",index=False)
    plot_mass(series,output/"convergence_mass.png")
    write_json(output/"convergence.json",{"cases": records, "per_sensor": rows,
                                          "successive_differences": empirical,
                                          "mass_residual_sensitivity": residual_sensitivity,
                                          "interpretation": "Successive differences indicate empirical behavior only; no formal order or bound."})


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
