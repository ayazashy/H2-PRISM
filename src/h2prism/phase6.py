"""Phase 6 source validation gate and archive alignment audit."""
from __future__ import annotations

import argparse
from dataclasses import replace
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT, load_scenario
from .phase2 import DATA_HASH, MODEL, MODEL_DIR, PARQUET, SID, checked_file
from .phase3 import digest, source_report, write_record
from .phase5 import CSV_HASH, available_source_bounds, clock_index, independent_eligibility, physical_eligibility

PAPER = "https://www.mdpi.com/2227-9717/14/16/2636"


def aligned_residuals(raw, released):
    common = raw.index.intersection(released.index)
    if not len(common):
        raise ValueError("no exact shared timestamps")
    return released.loc[common, list(SID)] - raw.loc[common, list(SID)]


def summarize_residuals(residual):
    results = {}
    for name, data in residual.items():
        finite = data[np.isfinite(data)]
        if finite.empty:
            raise ValueError(f"no finite aligned values: {name}")
        max_at = finite.abs().idxmax()
        results[name] = {
            "block_sid": SID[name], "native_unit": "MPa" if name.startswith("PS") else "kg/s",
            "unit_evidence": "SLX pressure converter and storage metadata" if name.startswith("PS")
                             else "Release metadata; solver flow converter inherits unit",
            "finite_pairs": len(finite), "missing_pairs": len(data) - len(finite),
            "bias": float(finite.mean()), "rmse": float(np.sqrt(np.mean(finite ** 2))),
            "maximum_absolute": float(finite.abs().max()), "maximum_timestamp_s": str(max_at),
            "signed_residual_at_maximum": float(finite.loc[max_at]),
        }
    return results


def archival_alignment():
    root = RAW_DATASET_DIR
    csv = checked_file(root / MODEL_DIR / "normality_gest_center.csv", CSV_HASH)
    alias = checked_file(csv.parent.parent / csv.name, CSV_HASH)
    parquet = checked_file(root / PARQUET, DATA_HASH)
    raw = pd.read_csv(csv, dtype={"Timestamp": str}).set_index("Timestamp")
    released = load_scenario(parquet)
    if released.index.name != "Timestamp" or tuple(raw.columns) != tuple(SID) or not set(SID) <= set(released):
        raise ValueError("unverified source or release schema")
    raw.index, released.index = clock_index(raw.index), clock_index(released.index)
    residuals = aligned_residuals(raw, released)
    results = summarize_residuals(residuals)
    focus = {}
    for name in ("PS1", "MFS3"):
        peak = residuals[name].abs().idxmax()
        i = residuals.index.get_loc(peak)
        selected = residuals.index[max(0, i-2):i+3]
        focus[name] = [
            {"time_s": str(t), "solver": float(raw.at[t, name]), "release": float(released.at[t, name]),
             "release_minus_solver": float(residuals.at[t, name])} for t in selected
        ]
    return {
        "tier": "T3_ARCHIVAL_SOURCE_DERIVED_SIMULATION", "fresh_reproduction": False,
        "source_file_sha256": {p.relative_to(root).as_posix(): h
                               for p, h in ((csv, CSV_HASH), (alias, CSV_HASH), (parquet, DATA_HASH))},
        "source_rows": len(raw), "release_rows": len(released), "aligned_rows": len(residuals),
        "aligned_range_s": [str(residuals.index[0]), str(residuals.index[-1])],
        "comparison": "release minus archival solver CSV at exact stored shared timestamps; native units",
        "timestamp_policy": "no interpolation, shift, snapping, or dropped finite observations",
        "unmapped_release_columns": sorted(set(released) - set(raw)),
        "channels": results, "peak_context": focus,
        "publication": {"reference": PAPER, "author_code": "https://github.com/andysinx/H2-SimNet",
                        "documented_processing": "Linear interpolation onto a one-second grid",
                        "archive_test": "At shared knots linear interpolation preserves solver values. "
                                        "The nonzero residuals rule out this CSV plus interpolation alone.",
                        "exact_center_processing_chain": "UNVERIFIED",
                        "author_reported_solver": "Variable-step, relative tolerance 1e-3",
                        "archived_center_launcher": "Fixed-step ode14x, 0.8 s",
                        "author_reported_composition": "10% hydrogen, 90% methane; linkage to local Center SLX unverified"},
        "raw_flow_sign_observations": {
            name: {"negative_records": int((raw[name] < 0).sum()), "zero_records": int((raw[name] == 0).sum()),
                   "positive_records": int((raw[name] > 0).sum())} for name in SID if name.startswith("MFS")
        },
    }, residuals


def flow_roles(graph):
    components = {c["sid"]: c for c in graph["components"]}
    roles = {}
    for name in ("MFS1", "MFS2", "MFS3"):
        sid = SID[name]
        nets = components[sid]["nets"]
        neighbors = {net: sorted(c["sid"] for c in components.values() if c["sid"] != sid and net in c["nets"])
                     for net in nets if net is not None}
        roles[name] = {
            "sensor_sid": sid, "nets": nets, "adjacent_components": neighbors,
            "static_role": ("RESERVOIR_CONNECTED_BRANCH" if any(
                components[n]["class"] == "reservoir" for nodes in neighbors.values() for n in nodes)
                            else "INTERNAL_STORAGE_CONNECTED_BRANCH" if any(
                components[n]["class"] == "constant_volume_chamber" for nodes in neighbors.values() for n in nodes)
                            else "UNRESOLVED"),
            "effective_positive_direction": "UNKNOWN",
            "signed_control_volume_term": None,
        }
    categories = {
        "external_reservoir_ports": {"controlled_reservoir", "reservoir"},
        "internal_pressure_source_transfers": {"pressure_source"},
        "explicit_chamber_storage": {"constant_volume_chamber"},
        "pipe_storage_candidates": {"pipe"},
    }
    inventory = {category: [{"sid": c["sid"], "nets": c["nets"], "effective_history": None}
                            for c in components.values() if c["class"] in classes]
                 for category, classes in categories.items()}
    return {"roles": roles, "static_control_volume_inventory": inventory,
            "conservation_identity": "dM/dt = sum(signed external flows into the control volume) - leak",
            "mass_balance_closed": False,
            "missing": ["signed effective supply and withdrawal histories", "complete boundary coverage",
                        "synchronized storage inventory and accumulation", "verified leak term when applicable"],
            "gas_evidence": graph["gas_properties"], "composition": "UNKNOWN",
            "physical_hydrogen_validity": "UNESTABLISHED"}


def execution_gate(log: Path, exit_code: int):
    content = log.read_bytes()
    decoded = content.decode("utf-16" if content.startswith(b"\xff\xfe") else "utf-8-sig", errors="replace")
    blocked = "Unable to communicate with required MathWorks services" in decoded and "5202" in decoded
    if not blocked or exit_code == 0:
        raise ValueError("Phase 6 blocked-startup record requires the recorded failed 5202 attempt")
    return {
        "attempts": 1, "source_model_loaded": False, "simulation_executed": False,
        "exit_code": exit_code, "failure": "MATLAB startup: Unable to communicate with required MathWorks services (error 5202)",
        "console_sha256": hashlib.sha256(content).hexdigest(), "simulink_simscape_checkout": "NOT_REACHED",
        "planned_settings": {"solver": "ode14x", "fixed_step_s": 0.8, "stop_s": 1.6},
        "actual_solver_configuration": None, "initial_states": None, "boundary_histories": None,
        "raw_export": None, "status": "EXTERNAL_ACTION_REQUIRED",
        "required_user_action": "Open authorized MATLAB normally, resolve Service Host or licensing with the "
                                "administrator if needed, verify Simulink and Simscape checkout, then retry the isolated probe.",
    }


def source_uncertainty():
    evidence_gaps = {
        "pressure": "Center PS converter units are traced; no calibration or deterministic error certificate",
        "mass_flow": "Center MFS inherited converter units; release reports kg/s; no signed calibration bound",
        "temperature": "No Center temperature series in the solver or Parquet export",
        "clock": "CSV and Parquet time grids are preserved; clock or alignment error is unbounded",
        "boundary_inputs": "Source graph identifies ports only; effective signed input histories missing",
        "initial_state": "SLX static initial targets do not establish compiled start states",
        "gas_properties": "Paper composition and static SID 4 parameters not reconciled by a runtime trace",
        "geometry": "Archived graph gives nominal static pipe dimensions; tolerances unverified",
        "leak_parameters": "No independently traced matched leak block, magnitude, onset or uncertainty",
        "model_discrepancy": "No independent physical measurements to bound discrepancy",
        "numerical_error": "Runtime solver checkout blocked; published tolerance is not a certified error bound",
    }
    return tuple(replace(b, reference=evidence_gaps[b.name]) for b in available_source_bounds())


def external_candidates():
    return [
        {"name": "Ibrahim et al. inline hydrogen leak experiments", "tier": "T4_CANDIDATE",
         "availability": "Primary paper inspected; raw measurements available on author request",
         "measurements": "Inline pressure transducers and flowmeters; hydrogen and nitrogen experiments",
         "labels": "Two controlled leak locations and multiple operating conditions",
         "ground_truth": "Physical leak locations documented; raw event timing, calibration and repeats require review",
         "licensing": "Open-access article; raw-data reuse terms must be confirmed with authors",
         "fit": "Closest candidate for independent in-pipe pressure/flow and location checks; topology differs",
         "reference": "https://doi.org/10.1016/j.jlp.2024.105452"},
        {"name": "Multiphase experimental plant", "tier": "T4_CANDIDATE",
         "availability": "Open Zenodo dataset; inspected repository and associated article, raw files not ingested",
         "measurements": "Pressure, flow and valve data in an air/water plant",
         "labels": "Normal, induced leak and obstruction conditions",
         "ground_truth": "Experimental interventions described; event timing and family independence require raw verification",
         "licensing": "Dataset license not verified here; article CC BY-NC is separate",
         "fit": "Possible instrumentation and event-gating benchmark after model adaptation; different gas and phase regime",
         "reference": "https://zenodo.org/records/16978349",
         "methods": "https://doi.org/10.1016/j.dib.2025.112038"},
        {"name": "PE pipe pressure decay", "tier": "T4_CANDIDATE",
         "availability": "Open Zenodo spreadsheet listing and documented measurement schema; raw file not ingested",
         "measurements": "Gauge pressure and gas/ambient temperature sampled at 30 s; no boundary mass-flow channel documented",
         "labels": "Background and two artificial capillary configurations in five non-hydrogen gases",
         "ground_truth": "Controlled defect configurations reported; calibration and repeat-run independence unverified",
         "licensing": "Dataset license not verified here",
         "fit": "Candidate for pressure-decay submodel checks, no signed network flow or region localization evaluation",
         "reference": "https://zenodo.org/records/20582921"},
    ]


def plot(residuals, report, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True, layout="constrained")
    for ax, name, unit in zip(axes, ("PS1", "MFS3"), ("MPa", "kg/s, release metadata")):
        ax.plot([float(t) for t in residuals.index], residuals[name], lw=0.75)
        peak = report["alignment"]["channels"][name]
        ax.scatter(float(Fraction(peak["maximum_timestamp_s"])), peak["signed_residual_at_maximum"],
                   s=16, color="black", zorder=3)
        ax.set_ylabel(f"{name} ({unit})")
    axes[-1].set_xlabel("Exact shared stored timestamp (s)")
    fig.suptitle(f"T3 archive | Release minus archived solver CSV | {report['sha256'][:12]}")
    with path.open("xb") as f:
        fig.savefig(f, format="png", dpi=160)
    plt.close(fig)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--probe-log", required=True, type=Path)
    cli.add_argument("--exit-code", required=True, type=int)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--figure", type=Path)
    cli.add_argument("--residuals", type=Path)
    args = cli.parse_args()
    gate = execution_gate(args.probe_log, args.exit_code)
    source = source_report(args.probe_log)
    alignment, residuals = archival_alignment()
    bounds = source_uncertainty()
    report = {
        "schema": "phase6/1", "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=WORKSPACE_ROOT, text=True).strip(),
        "execution": gate, "source": source, "alignment": alignment,
        "physics": flow_roles(source["source_port_graph"]),
        "uncertainty": {"records": [json.loads(b.to_json()) for b in bounds],
                        "blockers": physical_eligibility(bounds, MODEL),
                        "physical_exclusion": "BLOCKED"},
        "normal_leak": {"status": "BLOCKED_SOURCE_NORMAL_NOT_REPRODUCED",
                        "requirement": "Verified NORMAL launch plus documented, matched leak block, location, "
                                       "mechanism, timing, magnitude, and separately traceable generation"},
        "evaluation": independent_eligibility(), "external_candidates": external_candidates(),
        "historical_comparator": "Phase 4 matched joint set-membership equivalence preserved",
        "tier_policy": {"T1": "mathematical fixture", "T2": "controlled reference model",
                        "T3": "source-derived simulation", "T4": "independently measured experiment"},
    }
    report = json.loads(json.dumps(report))
    report["sha256"] = digest(report)
    write_record(args.output, report)
    if args.residuals:
        write_record(args.residuals, {
            "report_sha256": report["sha256"], "tier": report["alignment"]["tier"],
            "timestamps_s": list(map(str, residuals.index)),
            "release_minus_solver": {
                name: [float(value) if np.isfinite(value) else None for value in data]
                for name, data in residuals.items()
            },
        })
    if args.figure:
        plot(residuals, report, args.figure)


if __name__ == "__main__":
    main()
