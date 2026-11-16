"""Close the Phase 12 controlled outlet experiment using its saved captures."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import cumulative_simpson, trapezoid, simpson

from .certified_evidence import Channel, HypothesisModel, MeasurementContract, diagnose
from .data_contracts import SensorRecord
from .network_reference import localize
from .phase2 import SID
from .phase10 import CAPTURE, metrics
from .phase11 import BOUNDARIES, PHASE10, conservation, read_json, write_json
from .phase12 import CASES
from .phase12_acceptance import audit, mat, require

WINDOWS = (0.2, 1, 5, 30, 120, 600)
FLOOR = 1e-11


def first_sustained(clock, delta, threshold, count=5):
    hits = np.flatnonzero(np.convolve((abs(delta) > threshold).astype(int), np.ones(count, dtype=int), "valid") == count) if len(delta) >= count else []
    return float(clock[hits[0]]) if len(hits) else None


def sensor_comparison(clock, control, opening, event):
    pre = clock < event
    post = ~pre
    rows, windows = [], []
    for sensor in CAPTURE:
        a, b = control[sensor], opening[sensor]
        diff = b-a
        before = metrics(b[pre], a[pre], clock[pre])
        after = metrics(b[post], a[post], clock[post])
        threshold = max(before["max_absolute"], FLOOR)
        detected = first_sustained(clock[post], diff[post], threshold)
        rows.append({"sensor": sensor, "unit": "MPa" if sensor.startswith("PS") else "kg/s",
                     "pre_samples": before["matched_samples"], "pre_max_abs": before["max_absolute"],
                     "pre_rmse": before["rmse"], "post_samples": after["matched_samples"], "post_max_abs": after["max_absolute"],
                     "post_rmse": after["rmse"], "post_peak_s": after["peak_time_s"],
                     "post_signed_peak": after["signed_residual_at_peak"], "event_sample_delta": float(diff[post][0]),
                     "final_delta": float(diff[-1]), "tail_1000_s_mean": float(diff[clock>=clock[-1]-1000].mean()),
                     "post_peak_over_pre_envelope": after["max_absolute"]/threshold, "descriptive_threshold": threshold,
                     "first_sustained_s": detected, "descriptive_delay_s": None if detected is None else detected-event})
        for duration in WINDOWS:
            select = post & (clock <= event+duration+8*np.spacing(event+duration))
            windows.append({"sensor": sensor, "window_s": duration, "samples": int(select.sum()),
                            "peak_abs": float(abs(diff[select]).max()), "rmse": float(np.sqrt(np.mean(diff[select]**2))),
                            "any_over_pre_envelope": bool((abs(diff[select])>threshold).any()),
                            "five_consecutive_over_envelope": first_sustained(clock[select],diff[select],threshold) is not None})
    return rows, windows


def event_integral(clock, flow, brackets):
    """Integrate smooth sections with Simpson and left-hold each observed event bracket."""
    if any(i < 1 or i >= len(clock) for i in brackets) or tuple(sorted(set(brackets))) != tuple(brackets):
        raise ValueError("invalid integration brackets")
    output = np.empty(len(clock))
    start, mass = 0, 0.0
    for end in (*brackets, len(clock)):
        segment = cumulative_simpson(flow[start:end], x=clock[start:end], initial=0)
        output[start:end] = mass + segment
        if end < len(clock):
            mass = output[end-1] + float(flow[end-1]*(clock[end]-clock[end-1]))
        start = end
    return output


def framework(clock, opening, event, source_id):
    mask = (clock>=event)&(clock<=event+5)
    times = tuple(clock[mask].tolist())
    sensors = tuple(SensorRecord(name, "Center", "node" if name.startswith("PS") else "edge", SID[name],
                                 "pressure" if name.startswith("PS") else "mass_flow",
                                 "MPa" if name.startswith("PS") else "kg/s", 0.2) for name in CAPTURE)
    channels = tuple(Channel(s.sensor_id,s.unit,times,"Saved approved Phase 12 MAT clock",
                             tuple(opening[s.sensor_id][mask].tolist()), ()) for s in sensors)
    observation = MeasurementContract(sensors,times,channels,"Phase12 outlet opening","Center source family",
                                      source_id,"No qualified measurement bounds or prediction enclosures",1e-9)
    regions = ("OUTLET_SID_213", "OUTLET_SID_312", "OUTLET_SID_215", "OUTLET_SID_222")
    models = tuple(HypothesisModel(name,None,("Requires a validated source-compatible prediction enclosure",))
                   for name in ("NORMAL",*regions))
    result = diagnose(observation, models)
    return {"diagnostic": json.loads(result.to_json()), "localization": asdict(localize(result,regions)),
            "ground_truth": "Engineered area command on restriction SID 213 toward atmospheric reservoir SID 200",
            "bounds": "Unknown measurement, model discrepancy and prediction enclosure. No numerical floor entered as a measurement bound.",
            "independence": "Both runs share a source and form one exploratory controlled pair."}


def figures(output, clock, event, data, rates, areas, mass):
    from matplotlib import pyplot as plt

    labels = ("NORMAL", "Outlet opening")
    event_view = (clock >= event-10) & (clock <= event+600)
    fig, axes = plt.subplots(3, 1, sharex=True, layout="constrained", figsize=(8, 7))
    for label, area, rate in zip(labels, areas, rates):
        axes[0].step(clock[event_view], area[event_view]*1e6, where="post", label=label)
        axes[1].plot(clock[event_view], rate[event_view], label=label)
    axes[2].plot(clock[event_view], (rates[1]-rates[0])[event_view], color="#20746e")
    axes[0].set_ylabel("Received area (mm$^2$)")
    axes[0].legend()
    axes[1].set_ylabel("Outlet flow (kg/s)")
    axes[2].set_ylabel("Opening minus control (kg/s)")
    axes[2].set_xlabel("Saved time (s)")
    for ax in axes:
        ax.axvline(event, color="0.5", lw=.8, ls=":")
    fig.savefig(output/"outlet_response.png", dpi=220)
    plt.close(fig)

    for prefix, title, unit in (("PS","Pressure response","MPa"),("MFS","Mass-flow response","kg/s")):
        names = [name for name in CAPTURE if name.startswith(prefix)]
        fig, axs = plt.subplots(len(names),2,sharex=True,layout="constrained",figsize=(10,max(5,len(names)*1.3)))
        stride = slice(None,None,10)
        for i,name in enumerate(names):
            a,b = (run[name] for run in data)
            for y,label in zip((a,b),labels):
                axs[i,0].plot(clock[stride],y[stride],lw=.85,label=label)
            axs[i,1].plot(clock[stride],(b-a)[stride],lw=.85,color="#20746e")
            axs[i,0].set_ylabel(name)
            for ax in axs[i]:
                ax.axvline(event,color="0.5",lw=.6,ls=":")
        axs[0,0].set_title(f"Saved trajectories ({unit})")
        axs[0,1].set_title(f"Opening minus control ({unit})")
        axs[0,0].legend()
        for ax in axs[-1]:
            ax.set_xlabel("Saved time (s)")
        fig.suptitle(title)
        fig.savefig(output/f"{prefix.lower()}_comparison.png",dpi=190)
        plt.close(fig)

    fig, axes = plt.subplots(2,1,sharex=True,layout="constrained",figsize=(8,5.5))
    for label,row in zip(labels,mass):
        axes[0].plot(clock,row["storage"]-row["storage"][0],label=label)
        axes[1].plot(clock,row["event_residual"],label=label)
    axes[0].set_ylabel("Storage change (kg)")
    axes[0].legend()
    axes[1].set_ylabel("Event-aware residual (kg)")
    axes[1].set_xlabel("Saved time (s)")
    for ax in axes:
        ax.axvline(event,color="0.5",lw=.8,ls=":")
    fig.savefig(output/"conservation.png",dpi=200)
    plt.close(fig)


def run(root, previous, reference, output):
    receipts = {case: audit(root,previous,reference,case) for case in CASES}
    captures = [mat(root/case/"center_raw.mat") for case in CASES]
    responses = [mat(root/case/"outlet_evidence.mat")["response"] for case in CASES]
    t = captures[0]["sensors"]["pressure_sensor1"]["time"]
    require(np.array_equal(t,captures[1]["sensors"]["pressure_sensor1"]["time"]), "pair clock mismatch")
    event = receipts["outlet_opening"]["outlet"]["first_received_area_change_s"]
    j = int(np.searchsorted(t,event))
    charts = [{name:c["sensors"][key]["values"] for name,key in CAPTURE.items()} for c in captures]
    rows, windows = sensor_comparison(t,*charts,event)
    historical = {r["sensor"]: r["max_absolute"] for r in receipts["normal"]["residuals"]
                  if r["window"] == "pre_1000_s"}
    for row in rows:
        prior = historical[row["sensor"]]
        row["historical_pre_event_max_abs"] = prior
        row["pre_event_within_observed_reference_scale"] = row["pre_max_abs"] <= max(prior,FLOOR)
    rates = [r["signed_outlet_flow"]["values"] for r in responses]
    areas = [r["restriction_area_input"]["values"] for r in responses]
    delta = rates[1]-rates[0]
    peak = j + int(delta[j:].argmax())
    tail = t>=t[-1]-1000
    outlet = {"onset_s": event, "prior_knot_s": float(t[j-1]), "command_before_m2": float(areas[1][j-1]),
              "command_after_m2": float(areas[1][j]), "pre_max_abs_kg_s": float(abs(delta[:j]).max()),
              "pre_rmse_kg_s": float(np.sqrt(np.mean(delta[:j]**2))),
              "at_event_delta_kg_s": float(delta[j]), "event_control_kg_s": float(rates[0][j]),
              "at_event_relative_change": float(delta[j]/rates[0][j]),
              "min_post_delta_kg_s": float(delta[j:].min()), "peak_delta_kg_s": float(delta[peak]), "peak_time_s": float(t[peak]),
              "final_delta_kg_s": float(delta[-1]), "final_relative_change": float(delta[-1]/rates[0][-1]),
              "tail_1000_s_mean_delta_kg_s": float(delta[tail].mean()),
              "post_trapezoid_increment_kg": float(trapezoid(delta[j:],t[j:])),
              "post_simpson_increment_kg": float(simpson(delta[j:],x=t[j:])),
              "event_resolution": "Area and outlet flow first differ on the same saved knot; a sub-tick delay is unresolved."}
    phase10 = read_json(PHASE10)
    mass_stats, mass = {}, []
    for case,capture in zip(CASES,captures):
        frame, summary = conservation(capture,phase10,0.2)
        boundary=np.asarray(frame.boundary_net_kg_s)
        storage=np.asarray(frame.storage_kg)
        indices = (int(np.searchsorted(t,summary["step_bracket"][1]["time_s"])),)
        if case == "outlet_opening":
            indices += (j,)
        integrated = event_integral(t,boundary,indices)
        r = storage-storage[0]-integrated
        mass.append({"boundary":boundary,"storage":storage,"event_residual":r,"integrated":integrated})
        mass_stats[case] = {"initial_storage_kg":float(storage[0]),"final_storage_kg":float(storage[-1]),
                            "trapezoid_residual_kg":summary["final"]["trapezoid_residual_kg"],
                            "event_aware_residual_kg":float(r[-1]),"peak_abs_event_aware_residual_kg":float(abs(r).max()),
                            "pointwise_flow_residual_kg_s":summary["pointwise_max_abs_boundary_minus_storage_port_kg_s"],
                            "event_right_knots_s":[float(t[i]) for i in indices]}
    paired_mass = {"final_storage_delta_kg":float(mass[1]["storage"][-1]-mass[0]["storage"][-1]),
                   "final_net_inflow_delta_kg_s":float(mass[1]["boundary"][-1]-mass[0]["boundary"][-1]),
                   "signed_boundary_integral_delta_kg":float(mass[1]["integrated"][-1]-mass[0]["integrated"][-1])}
    logs = [{x["path"]:x["values"] for x in capture["logSeries"]} for capture in captures]
    for name, sid in BOUNDARIES.items():
        key = name + "/mdot_A"
        change = logs[0][key]-logs[1][key]
        paired_mass.setdefault("boundary_components_positive_into_network", {})[sid] = {
            "post_integrated_delta_kg": float(simpson(change[j:],x=t[j:])),
            "final_delta_kg_s": float(change[-1])}
    decision = framework(t,charts[1],event,receipts["outlet_opening"]["capture_hashes"]["center_raw.mat"])
    output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(output/"sensor_comparison.csv",index=False)
    pd.DataFrame(windows).to_csv(output/"observation_windows.csv",index=False)
    pd.DataFrame({"time_s":t,"area_normal_m2":areas[0],"area_opening_m2":areas[1],"outlet_normal_kg_s":rates[0],
                  "outlet_opening_kg_s":rates[1],"outlet_delta_kg_s":delta,
                  **{f"{case}_{key}":values for case,row in zip(CASES,mass) for key,values in row.items()}}).to_csv(
                    output/"paired_histories.csv.gz",index=False,compression={"method":"gzip","mtime":0})
    figures(output,t,event,charts,rates,areas,mass)
    write_json(output/"experiment_manifest.json", {
        "classification": "New source-derived controlled simulation",
        "family": "Center source family",
        "approved_pair": receipts["normal"]["pair"],
        "cases": {case: {"capture_sha256": row["capture_hashes"], "solver": row["runtime_model"],
                         "logging_policy": row["logging_policy"]} for case,row in receipts.items()},
        "historical_reference_extraction_sha256": receipts["normal"]["reference_extraction_sha256"],
        "nominal_onset_s": 1000, "actual_received_onset_s": event, "location": decision["ground_truth"]})
    write_json(output/"paired_results.json", {
        "classification":"ACCEPTED","tier":"New source-derived controlled simulation",
        "samples_per_case":len(t),"timing":"Exact saved common clock; no interpolation",
        "capture_acceptance":receipts,"outlet_effect":outlet,"sensors":rows,"windows":windows,
        "mass":mass_stats,"paired_mass":paired_mass,"framework":decision,
        "pre_event_tolerance":"Pre-event max by channel with a 1e-11 native-unit numerical reporting floor. "
                              "The pair screen is descriptive. Historical reference scale is reported separately. No certified bound is available.",
        "remaining_cases":[{"restriction_sid":"312","sink_sid":"316","purpose":"Competing metered outlet via MFS1 SID 311"},
                           {"restriction_sid":"215","sink_sid":"217","purpose":"Competing outlet without a direct flow measurement"}],
        "limitations":["Single shared source family; no independent confirmation or accuracy estimate.",
                       "Archived LEAK reproduction remains blocked; no hydrogen validation.",
                       "No uniform bound for numerical or physical uncertainty."]})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("root","previous","reference","output"):
        p.add_argument(name,type=Path)
    a=p.parse_args()
    run(a.root,a.previous,a.reference,a.output)


if __name__ == "__main__":
    main()
