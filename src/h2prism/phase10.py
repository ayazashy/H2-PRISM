"""Audit the completed Center NORMAL capture against the local H2-SimNet archives."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.io import loadmat

from .data.loader import RAW_DATASET_DIR
from .phase2 import DATA_HASH, MODEL, MODEL_DIR, MODEL_HASH, PARQUET, SID, checked_file
from .phase5 import CSV_HASH, clock_index

CAPTURE = dict(zip(SID, [f"pressure_sensor{i}" for i in range(1, 11)] +
                   [f"flow_sensor{i}" for i in range(1, 4)]))
CLEAN_CSV = PARQUET.replace("/parquet/", "/csv/").replace(".parquet", ".csv")


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_csv(path):
    return pd.read_csv(path, dtype={"Timestamp": str}, float_precision="round_trip").set_index("Timestamp")


def quality(times, values):
    times, values = np.asarray(times, dtype=float), np.asarray(values, dtype=float)
    if times.ndim != 1 or times.shape != values.shape or not len(times):
        raise ValueError("expected nonempty scalar samples on a one-dimensional clock")
    good_time = np.isfinite(times)
    finite = np.isfinite(values)
    result = {
        "samples": len(times), "first_s": float(times[0]) if good_time[0] else None,
        "last_s": float(times[-1]) if good_time[-1] else None,
        "invalid_timestamps": int((~good_time).sum()), "duplicates": int(len(times[good_time]) - len(np.unique(times[good_time]))),
        "strictly_increasing": bool(good_time.all() and (np.diff(times) > 0).all()),
        "nan_or_missing": int(np.isnan(values).sum()), "infinite": int(np.isinf(values).sum()),
        "min": float(values[finite].min()) if finite.any() else None,
        "max": float(values[finite].max()) if finite.any() else None,
        "negative": int((values[finite] < 0).sum()), "zero": int((values[finite] == 0).sum()),
        "positive": int((values[finite] > 0).sum()),
    }
    return result


def exact_pairs(target, reference, decimal=True):
    if decimal:
        target, reference = clock_index(target), clock_index(reference)
    else:
        target, reference = pd.Index(np.asarray(target, dtype=float)), pd.Index(np.asarray(reference, dtype=float))
        if any(not clock.is_unique or not clock.is_monotonic_increasing or clock.hasnans for clock in (target, reference)):
            raise ValueError("invalid binary64 clock")
    both = target.intersection(reference, sort=False)
    return target.get_indexer(both), reference.get_indexer(both)


def solver_grid(times, step, stop):
    """Qualify row-index pairing against the fixed-step clock and explicit roundoff bound."""
    clock = np.asarray(times, dtype=float)
    ticks = np.arange(round(stop / step) + 1) * step
    if clock.shape != ticks.shape or not np.isfinite(clock).all() or not (np.diff(clock) > 0).all():
        raise ValueError("solver clock has missing, duplicate, or unordered ticks")
    offset = clock - ticks
    bound = 8 * np.spacing(np.maximum(1, np.abs(ticks)))
    if (np.abs(offset) > bound).any():
        raise ValueError("solver clock differs from documented fixed-step grid beyond roundoff")
    return float(np.abs(offset).max())


def metrics(target, reference, times):
    target, reference, times = map(np.asarray, (target, reference, times))
    good = np.isfinite(target) & np.isfinite(reference)
    row = {"matched_samples": len(times), "finite_pairs": int(good.sum())}
    if not good.any():
        return row
    residual = target[good] - reference[good]
    absolute = np.abs(residual)
    rmse = float(np.sqrt(np.mean(residual**2)))
    scale = float(np.sqrt(np.mean(reference[good]**2)))
    peak = int(absolute.argmax())
    return {**row, "max_absolute": float(absolute[peak]), "mae": float(absolute.mean()),
            "rmse": rmse, "relative_rmse_reference_rms": rmse / scale if scale else None,
            "bias": float(residual.mean()), "peak_time_s": float(times[good][peak]),
            "signed_residual_at_peak": float(residual[peak])}


def compare(frames, step, stop):
    pairs = [("capture", "archive"), ("capture", "clean_csv"), ("capture", "parquet"),
             ("clean_csv", "archive"), ("parquet", "archive"), ("clean_csv", "parquet")]
    rows, clocks = [], {}
    for target, reference in pairs:
        a, b = frames[target], frames[reference]
        ai, bi = a.index.to_numpy(dtype=float), b.index.to_numpy(dtype=float)
        alignments = {name: exact_pairs(a.index, b.index, decimal=decimal)
                      for name, decimal in (("exact_decimal", True), ("exact_binary64", False))}
        if target == "capture" and reference == "archive":
            clocks["fixed_step_grid"] = {"step_s": step, "stop_s": stop,
                "max_target_off_grid_s": solver_grid(ai, step, stop),
                "max_reference_off_grid_s": solver_grid(bi, step, stop)}
            alignments["verified_solver_tick"] = (np.arange(len(ai)), np.arange(len(bi)))
        for method, (x, y) in alignments.items():
            clocks[f"{target}:{reference}:{method}"] = {
                "pairs": len(x), "target_only": len(a) - len(x), "reference_only": len(b) - len(y),
                "first_s": float(ai[x[0]]) if len(x) else None, "last_s": float(ai[x[-1]]) if len(x) else None,
                "max_paired_timestamp_delta_s": float(np.abs(ai[x] - bi[y]).max()) if len(x) else None}
            for channel, sid in SID.items():
                rows.append({"target": target, "reference": reference, "alignment": method,
                             "sensor": channel, "sid": sid, "unit": "MPa" if channel.startswith("PS") else "kg/s",
                             **metrics(a[channel].to_numpy()[x], b[channel].to_numpy()[y], ai[x])})
    return rows, clocks


def capture_data(run, extracted):
    capture_rows, integrity = {}, {}
    for sensor, name in CAPTURE.items():
        exported = read_csv(run / f"{name}.csv")
        stored = extracted["sensors"][name]
        t, x = exported.index.to_numpy(dtype=float), exported["Value"].to_numpy()
        record = quality(t, x)
        record["csv_timestamps_equal_mat"] = bool(np.array_equal(t, stored["time"]))
        record["csv_values_equal_mat"] = bool(np.array_equal(x, stored["values"]))
        record["mat_data_unit"] = stored["unit"] if isinstance(stored["unit"], str) else None
        record["mat_time_unit"] = stored["timeUnit"]
        integrity[sensor] = record
        capture_rows[sensor] = exported["Value"]
    return pd.DataFrame(capture_rows), integrity


def json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(type(value).__name__)


def plot_focus(frames, path):
    from matplotlib import pyplot as plt

    fig, axes = plt.subplots(2, 1, sharex=True, layout="constrained", figsize=(8, 5.5))
    for axis, name, unit in zip(axes, ("PS1", "MFS3"), ("MPa", "kg/s")):
        for key, label, style in (("archive", "Archived solver", "-"), ("capture", "R2026b capture", "--"),
                                  ("parquet", "Clean release (Parquet)", ".")):
            frame = frames[key]
            t = frame.index.to_numpy(dtype=float)
            selected = (20 <= t) & (t <= 40)
            axis.plot(t[selected], frame[name][selected], style, label=label, ms=4, lw=1.4)
        axis.axvline(28, color="0.5", lw=0.8)
        axis.set_ylabel(f"{name} ({unit})")
    axes[0].legend()
    axes[-1].set_xlabel("Stored time (s)")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def visible_unit(value):
    import re

    if not isinstance(value, str):
        return None
    match = re.search(r"Name: '([^']+)'", value)
    return match[1] if match else value


def describe_signal(signal, scale=1):
    values = np.asarray(signal["values"], dtype=float) * scale
    return {**quality(signal["time"], values), "unit": visible_unit(signal["unit"]),
            "initial": float(values[0]), "final": float(values[-1])}


def model_blocks(model):
    from xml.etree import ElementTree
    from zipfile import ZipFile

    with ZipFile(model) as archive:
        root = ElementTree.fromstring(archive.read("simulink/systems/system_root.xml"))
    return {block.get("SID"): {
        "name": block.get("Name").replace("\n", " ").strip(),
        **{p.get("Name"): p.text for p in block.iter("P")},
    } for block in root.findall("Block")}


def fields(record, keys):
    return {key: record[key] for key in keys if key in record}


def physical_audit(extracted, blocks, capture, setup):
    from scipy.integrate import cumulative_trapezoid

    log = {item["path"]: item for item in extracted["logSeries"]}
    t = capture.index.to_numpy(dtype=float)

    def on_sensor_clock(path, unit):
        signal = log[path]
        y = np.asarray(signal["values"])
        if signal["unit"] != unit or not np.array_equal(signal["time"], t) or not np.isfinite(y).all():
            raise ValueError(f"invalid physical series: {path}")
        return y

    pressure_prefix = "Pressure & Temperature Sensor (G)"
    flow_prefix = "Flow Rate Sensor (G)"
    channels = {}
    for sensor, sid in SID.items():
        pressure = sensor.startswith("PS")
        prefix = pressure_prefix if pressure else flow_prefix
        suffix = blocks[sid]["name"].removeprefix(prefix)
        node = ("Pressure_Temperature_Sensor_G" if pressure else "Flow_Rate_Sensor_G") + suffix
        path = node + ("/Pa" if pressure else "/M")
        # Pressure is logged in MPa or Pa depending on the Simscape variable.
        unit = log[path]["unit"]
        factors = {"Pa": 1e-6, "MPa": 1} if pressure else {"kg/s": 1}
        factor = factors[unit]
        raw = on_sensor_clock(path, unit)
        channels[sensor] = {"sid": sid, "log_path": path, "log_unit": unit,
                            "factor_log_to_csv": factor,
                            "max_absolute_log_to_csv": float(np.abs(raw * factor - capture[sensor]).max())}
        if pressure:
            channels[sensor]["absolute_pressure"] = True
            channels[sensor]["local_temperature"] = describe_signal(log[node + "/A/T"])

    reservoirs = {"Reservoir": "1", "Reservoir_G": "195", "Reservoir_G1": "200",
                  "Reservoir_G2": "217", "Reservoir_G3": "224", "Reservoir_G4": "316"}
    boundaries, rates = {}, []
    for node, sid in reservoirs.items():
        flow = log[node + "/mdot_A"]
        rates.append(-on_sensor_clock(node + "/mdot_A", "kg/s"))
        boundary = {"sid": sid, "positive_into_network_factor": -1,
                    "signed_into_network": describe_signal(flow, -1),
                    "internal_pressure": describe_signal(log[node + ("/P" if sid == "1" else "/p_I")]),
                    "internal_temperature": describe_signal(log[node + ("/T" if sid == "1" else "/T_I")]),
                    "internal_value_basis": "logged static-mode setpoints" if sid == "1" else "logged internal states",
                    "port_pressure": describe_signal(log[node + "/A/p"]),
                    "port_temperature": describe_signal(log[node + "/A/T"]),
                    "configured": fields(blocks[sid], ("pressure_spec", "reservoir_pressure", "reservoir_pressure_unit",
                                                       "reservoir_temperature", "reservoir_temperature_unit"))}
        boundaries[node] = boundary
    boundary_rate = np.sum(rates, axis=0)
    storage, mass, port_rates = {}, np.zeros(len(t)), np.zeros(len(t))
    for sid, block in blocks.items():
        name = block["name"]
        if name.startswith("Pipe (G)"):
            assert block["length_unit"] == "m" and block["area_unit"] == "m^2"
            assert block["dynamic_compressibility"] == "true"
            node = "Pipe_G" + name.removeprefix("Pipe (G)")
            volume = float(block["length"]) * float(block["area"])
            port_rates += on_sensor_clock(node + "/mdot_B", "kg/s")
        elif name == "Constant Volume Chamber (G)":
            assert block["volume_unit"] == "m^3" and block["num_ports"] == "foundation.enum.num_ports.one"
            node, volume = "Constant_Volume_Chamber_G", float(block["volume"])
        else:
            continue
        density = on_sensor_clock(node + "/rho_I", "kg/m^3")
        temperature = on_sensor_clock(node + "/T_I", "K")
        pressure = on_sensor_clock(node + "/p_I", "MPa")
        gas = setup["gasSettings"]
        expected_pressure = density * temperature * float(gas["Z"]) * float(gas["R"]) / 1000
        mass += volume * density
        port_rates += on_sensor_clock(node + "/mdot_A", "kg/s")
        targets = {key: value for key, value in block.items()
                   if key.startswith(("p_init", "T_init", "mdot_init", "p_I", "T_I"))}
        storage[node] = {"sid": sid, "volume_m3": volume,
                         "configured_initial_targets_from_slx": targets,
                         "pressure": describe_signal(log[node + "/p_I"]),
                         "temperature": describe_signal(log[node + "/T_I"]),
                         "density": describe_signal(log[node + "/rho_I"]),
                         "max_abs_p_minus_ZrhoRT_MPa": float(np.abs(pressure - expected_pressure).max())}
    integrated = cumulative_trapezoid(boundary_rate, t, initial=0)
    gross = sum(float(cumulative_trapezoid(np.abs(rate), t)[-1]) for rate in rates)
    residual = mass - mass[0] - integrated
    peak = int(np.abs(residual).argmax())
    commands = {key: describe_signal(value) for key, value in extracted["commands"].items()}
    commands.update({path: describe_signal(log[path]) for path in (
        "Reservoir/P", "Reservoir/T", "PS_Step/O", "PS_Ramp/O", "Pressure_Source_G1/P", "Pressure_Source_G3/P")})
    for native, received in (("PS_Step/O", "Pressure_Source_G3/P"), ("PS_Ramp/O", "Pressure_Source_G1/P")):
        commands[native]["max_error_at_pressure_source_Pa"] = float(np.abs(
            on_sensor_clock(native, "Pa") - on_sensor_clock(received, "Pa")).max())
    step = on_sensor_clock("PS_Step/O", "Pa")
    changed = np.flatnonzero(step > (step[0] + step[-1]) / 2)
    commands["PS_Step/O"]["first_sample_above_plateau_midpoint_s"] = float(t[changed[0]])
    ramp = on_sensor_clock("PS_Ramp/O", "Pa")
    commands["PS_Ramp/O"]["first_change_larger_than_one_Pa_s"] = float(t[np.flatnonzero(
        np.abs(ramp - ramp[0]) > 1)[0]])
    initial = extracted["initial"]
    state_count = sum(isinstance(state["samples"], dict) and state["samples"]["firstTime"] == 0 for state in initial)
    return {
        "channels": channels, "boundaries": boundaries, "storage": storage, "commands": commands,
        "signed_sensor_roles": {"convention": "Flow Rate Sensor (G) positive from A to B",
            "MFS1": "withdrawal path to Reservoir_G4", "MFS2": "internal chamber port A",
            "MFS3": "withdrawal path to Reservoir_G1"},
        "logged_state_entries": len(initial), "state_entries_with_first_sample_at_zero": state_count,
        "mass_balance": {"scope": "Seven compressible pipes and one single-port chamber, bounded by six reservoirs",
            "external_flow": "negative sum of reservoir mdot_A; reservoir signs checked against network-side rates",
            "pointwise_boundary_minus_storage_port_sum_max_kg_s": float(np.abs(boundary_rate - port_rates).max()),
            "storage_initial_kg": float(mass[0]), "storage_final_kg": float(mass[-1]),
            "storage_change_kg": float(mass[-1] - mass[0]), "integrated_boundary_net_kg": float(integrated[-1]),
            "integrated_boundary_gross_kg": gross, "final_storage_minus_integrated_net_kg": float(residual[-1]),
            "max_absolute_residual_kg": float(abs(residual[peak])), "peak_residual_time_s": float(t[peak]),
            "final_residual_fraction_of_gross": float(abs(residual[-1]) / gross),
            "quadrature": "trapezoidal integration at saved 0.8 s knots; no bound for between-knot integration error",
            "status": "PARTIALLY VERIFIED"},
        "log_extraction_limitations": extracted["logErrors"],
    }


def diagnostic_time_shift(times, values, at, reference, limit):
    """Fit a bounded local shift for exploration only, using a shared interior support."""
    from scipy.optimize import minimize_scalar

    times, values, at, reference = map(np.asarray, (times, values, at, reference))
    if not len(at) or at[0] - limit < times[0] or at[-1] + limit > times[-1]:
        raise ValueError("time-shift diagnostic would extrapolate")

    def rmse(shift):
        return float(np.sqrt(np.mean((np.interp(at + shift, times, values) - reference)**2)))

    fit = minimize_scalar(rmse, bounds=(-limit, limit), method="bounded")
    if not fit.success:
        raise ValueError("time-shift diagnostic did not converge")
    return {"samples": len(at), "shift_s": float(fit.x), "rmse_zero_shift": rmse(0),
            "rmse_fitted_shift": float(fit.fun), "near_search_boundary": bool(limit - abs(fit.x) < 0.001)}


def offset_diagnostics(frames):
    capture, release = frames["capture"], frames["parquet"]
    t = capture.index.to_numpy(dtype=float)
    x, y = exact_pairs(capture.index, release.index)
    shared = t[x]
    results = {}
    for sensor in ("PS1", "MFS3"):
        results[sensor] = []
        for lo, hi in ((24, 40), (24, 160), (160, 1000), (1000, 19996)):
            selected = (shared >= lo) & (shared <= hi)
            fit = diagnostic_time_shift(t, capture[sensor], shared[selected], release[sensor].iloc[y[selected]], 0.8)
            results[sensor].append({"window_s": [lo, hi], **fit})
    return {"method": "Exploratory linear interpolation of capture at t + shift on exact shared times; "
                      "bounded scalar fit in [-0.8, 0.8] s. Positive estimates mean release leads the local capture. "
                      "This does not change the exact-clock metrics or identify a generating transformation.",
            "channels": results}


def discrepancy_register(frames, physics):
    focus = []
    for sensor in ("PS1", "MFS3"):
        values = {}
        for name, frame in frames.items():
            row = frame[sensor].to_numpy()[frame.index.to_numpy(dtype=float) == 28]
            if len(row) != 1:
                raise ValueError(f"ambiguous or missing 28 s sample in {name}")
            values[name] = float(row[0])
        focus.append({"sensor": sensor, "time_s": 28, "values": values,
                      "capture_minus_archive": values["capture"] - values["archive"],
                      "parquet_minus_archive": values["parquet"] - values["archive"],
                      "status": "CONTRADICTED",
                      "finding": "Release differs at an exact shared knot, ruling out linear interpolation of the archived solver CSV alone."})
    return {
        "release_at_28_s": focus,
        "source_to_release_processing": {"status": "UNVERIFIED",
            "finding": "Exact generation and preprocessing chain for the clean release is unidentified."},
        "storage_integral": physics["mass_balance"],
        "gas_qualification": {"status": "UNVERIFIED", "finding": "No source-bound composition or validation; fitted/effective model constants cannot establish mixture identity."},
        "boundary_configuration": {"status": "VERIFIED", "finding": "Fixed reservoirs use atmospheric pressure at runtime (0.1 MPa), while their stored specified-pressure field is 0.101325 MPa."},
        "initial_targets": {"status": "VERIFIED", "finding": "Stored targets and logged time-zero states differ; the audit uses the logged states for physical checks."},
    }


def run_audit(run, extraction, output):
    raw = RAW_DATASET_DIR
    capture_model = checked_file(run / f"{MODEL}.slx", MODEL_HASH)
    source_model = checked_file(raw / MODEL_DIR / f"{MODEL}.slx", MODEL_HASH)
    source_files = {
        "archive": checked_file(raw / MODEL_DIR / "normality_gest_center.csv", CSV_HASH),
        "clean_csv": raw / CLEAN_CSV, "parquet": checked_file(raw / PARQUET, DATA_HASH)}
    capture_files = [capture_model, run / "center_raw.mat", run / "center_setup.mat",
                     run / "interactive_capture_preflight_passed.log",
                     *(run / f"{name}.csv" for name in CAPTURE.values())]
    hashes = {path.name: sha256(path) for path in capture_files}
    extracted = loadmat(extraction, simplify_cells=True)
    if hashes["center_raw.mat"] != extracted["raw_sha256"]:
        raise ValueError("MAT extraction does not identify the supplied raw capture")
    if "=== CAPTURE COMPLETED ===" not in capture_files[3].read_text(encoding="utf-8"):
        raise ValueError("missing completion marker")
    setup = loadmat(run / "center_setup.mat", simplify_cells=True)
    capture, integrity = capture_data(run, extracted)
    for name, record in integrity.items():
        expected = "MPa" if name.startswith("PS") else "kg/s"
        record["mat_data_unit"] = visible_unit(record["mat_data_unit"])
        if (not (record["csv_timestamps_equal_mat"] and record["csv_values_equal_mat"] and record["strictly_increasing"])
                or record["mat_data_unit"] != expected or record["mat_time_unit"] != "seconds"
                or record["nan_or_missing"] or record["infinite"]
                or (expected == "MPa" and record["min"] <= 0)):
            raise ValueError(f"capture integrity or units failed: {name}")
    frames = {"capture": capture, "archive": read_csv(source_files["archive"]),
              "clean_csv": read_csv(source_files["clean_csv"]),
              "parquet": pd.read_parquet(source_files["parquet"])}
    execution = extracted["execution"]
    if (execution["stopEvent"] != "ReachedStopTime" or np.size(execution["simulationErrorMessage"]) != 0
            or np.size(execution["errorDiagnostic"]) != 0 or execution["start_s"] != 0 or execution["stop_s"] != 20000):
        raise ValueError("execution metadata does not establish successful 20,000 s run")
    rows, clocks = compare(frames, execution["solverInfo"]["FixedStepSize"], execution["stop_s"])
    blocks = model_blocks(source_model)
    physics = physical_audit(extracted, blocks, capture, setup)
    anomaly = raw / MODEL_DIR.split("/")[0] / "anomalous_scenarios/Anomalous_HNetwork_gest_center.slx"
    report = {
        "schema": "h2prism-center-normal-reproduction/1",
        "source_hashes": {key: {"path_in_dataset": path.relative_to(raw).as_posix(), "sha256": sha256(path)}
                          for key, path in source_files.items()},
        "capture_hashes": hashes, "extraction_sha256": sha256(extraction),
        "execution": execution, "matlab_version": setup["release"],
        "capture_integrity": integrity,
        "setup": {key: setup[key] for key in ("original", "configured", "inputMap", "physicalInputs", "gasBlocks", "gasSettings")},
        "units": {"pressure": "MPa absolute", "pressure_to_Pa": 1e6, "flow": "kg/s signed",
                  "flow_to_kg_s": 1, "capture_time": "s", "capture_to_archive_and_release_value_scale": 1,
                  "release_channel_scope": "13 traced channels; PS11, PS12, MFS4 and labels excluded"},
        "gas_runtime": {"model": "constant-property perfect-gas relation checked against logged p, rho and T",
                        "gas_properties_block_sid": "4", "verified_species_or_mole_fractions": None},
        "anomalous_center_candidate": {"path_in_dataset": anomaly.relative_to(raw).as_posix(),
                                        "sha256": sha256(anomaly), "status": "UNVERIFIED"},
        "time_alignment": clocks, "exploratory_time_shift": offset_diagnostics(frames),
        "per_sensor": rows, "physics": physics,
        "discrepancies": discrepancy_register(frames, physics),
        "claims": {
            "software_execution": "VERIFIED", "capture_csv_equals_raw_mat": "VERIFIED",
            "archival_solver_trajectory": "PARTIALLY VERIFIED",
            "exact_clean_release_trajectory": "CONTRADICTED",
            "mass_conservation_resolved_at_logged_knots": "PARTIALLY VERIFIED",
            "physical_hydrogen_fidelity": "UNVERIFIED", "certified_diagnosis": "UNVERIFIED",
            "independent_confirmatory_evaluation": "UNVERIFIED"},
        "leak_decision": {"eligible": False,
            "next_experiment": "Qualify the archived anomalous Center SLX against NORMAL before a paired simulation. "
                               "Trace one documented LEAK mechanism, location, opening schedule and magnitude to its actual controls; "
                               "hold solver, gas, baseline initialization and unrelated boundaries fixed. "
                               "Capture external signed rates and storage through the event and resolve numerical closure."},
    }
    output.mkdir(parents=True, exist_ok=False)
    with (output / "comparison.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, default=json_value, allow_nan=False)
        stream.write("\n")
    with (output / "discrepancies.json").open("x", encoding="utf-8") as stream:
        json.dump(report["discrepancies"], stream, indent=2, allow_nan=False)
        stream.write("\n")
    pd.DataFrame(rows).to_csv(output / "per_sensor.csv", index=False, mode="x")
    plot_focus(frames, output / "shared_knot_discrepancies.png")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("extracted", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run_audit(args.run, args.extracted, args.output)


if __name__ == "__main__":
    main()
