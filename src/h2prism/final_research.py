"""Finalize the evidence-backed Center study and prepare two outlet rivals."""
from __future__ import annotations

import argparse
from copy import deepcopy
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

from .data.loader import RAW_DATASET_DIR, WORKSPACE_ROOT
from .phase2 import MODEL, MODEL_DIR, MODEL_HASH, checked_file
from .phase10 import CAPTURE, metrics, model_blocks, sha256
from .phase11 import PHASE10, conservation, read_json, write_json
from .phase12 import CASES, approve, prepare, specification
from .phase12_acceptance import REPORT11, audit, mat, verify_pair
from .phase12_pair import FLOOR, event_integral, first_sustained, framework
from .simnet_independence import build_graph, crossing_legacy, historical_exposure
from .simnet_study import catalog_tables

ARCHIVE = RAW_DATASET_DIR / MODEL_DIR
SOURCE = ARCHIVE / f"{MODEL}.slx"
VERIFIED = WORKSPACE_ROOT / "03_results/validation/phase12_center_outlet/paired_results"
RIVALS = {
    "sid312": ("312", "316", "311", ["309", "49"], "Local_Restriction_G5", "Reservoir_G4"),
    "sid215": ("215", "217", "", ["109", "221", "453"], "Local_Restriction_G6", "Reservoir_G2"),
}
UP_SHA = "5c3c76e9866dcbbe0a2ec6937d150c6ab9af3ec010ea92df19c2ff92426380d4"


def root_connections(path):
    with ZipFile(path) as archive:
        root = ET.fromstring(archive.read("simulink/systems/system_root.xml"))
    return {frozenset(p.text for p in line.iter("P") if p.get("Name") in {"Src","Dst"})
            for line in root.findall("Line")}


def rival_specs(source):
    checked_file(source, MODEL_HASH)
    blocks = model_blocks(source)
    connections = root_connections(source)
    designs = {}
    for key, (sid, sink, meter, upstream, log_node, sink_node) in RIVALS.items():
        outlet = blocks[sid]
        incoming = {f"{sid}#lconn:1"}
        incoming |= {"309#lconn:1", "49#rconn:1"} if meter else {"109#lconn:1","221#rconn:1","453#lconn:1"}
        path = [{f"{sid}#rconn:1", f"{meter}#lconn:1"}, {f"{meter}#rconn:1", f"{sink}#lconn:1"}] if meter else [
            {f"{sid}#rconn:1", f"{sink}#lconn:1"}]
        if any(frozenset(ports) not in connections for ports in [incoming,*path]):
            raise ValueError(f"{key}: source outlet port chain changed")
        if (outlet["restriction_type"] != "foundation.enum.restriction_type.fixed"
                or float(outlet["restriction_area"]) != 0.001 or outlet["restriction_area_unit"] != "m^2"
                or outlet["min_area_unit"] != "m^2" or outlet["max_area_unit"] != "m^2"
                or blocks[sink]["pressure_spec"] != "foundation.enum.pressure_spec.atmospheric"):
            raise ValueError(f"{key}: source area or reservoir semantics changed")
        spec = deepcopy(specification())
        spec["location"] = {"restriction_sid":sid,"reservoir_sid":sink,"flow_sensor_sid":meter,
                            "upstream_junction_sids":upstream,"restriction_log_node":log_node,"sink_log_node":sink_node}
        spec["mechanism"] = f"Incremental atmospheric withdrawal through existing SID {sid} to sink SID {sink}"
        spec["downstream"] = f"Existing atmospheric reservoir SID {sink}; confirm pressure and temperature in capture."
        spec["area"].update({"min":outlet["min_area"],"max":outlet["max_area"]})
        if float(outlet["max_area"]) < float(spec["area"]["intervention_final"]):
            spec["area"].update({"source_max":outlet["max_area"],"max":"0.0012"})
            spec["matching"] += " Both twins raise the inactive archived variable-mode cap to 0.0012 m^2."
        spec["source_chain"] = [sorted(ports) for ports in [incoming,*path]]
        spec["measurement_scope"] = "MFS1 directly meters the branch" if meter else "No direct MFS on this outlet; native logging supplies ground truth"
        designs[key] = spec
    return designs


def eligibility():
    manifest, folds = catalog_tables()
    graph = build_graph(manifest)
    protocol = historical_exposure(manifest)
    crossing = crossing_legacy(manifest, folds, graph)
    classes = manifest.groupby(["topology_source_model","label_mapped"]).size()
    return {"verdict":"CONFIRMATORY ACCURACY COMPARISON: NOT ESTABLISHED",
            "archived_scored_scenario_candidates":len(manifest),
            "class_counts":[{"topology":topology,"label":label,"count":int(n)}
                            for (topology,label),n in classes.items()],
            "archive_dependency_components":len(graph["conservative_components"]),
            "legacy_crossing_fold_group_records":len(crossing),
            "legacy_confirmed_crossing_records":sum(row["confirmed_crossing"] for row in crossing),
            "historically_inspected_candidates":len(protocol["inspection_cases"]),
            "family_eligibility":{"confirmatory_test":0,"disjoint_confirmatory_calibration":0},
            "support":{"accuracy":None,"selective_risk":None,"risk_coverage":None,"matched_coverage_incremental_value":None},
            "blockers":["No pristine holdout established", "Physical labels and producing-run ancestry remain unqualified",
                        "Controlled variants share the same Center parent family", "Certified prediction and measurement enclosures are missing"]}


def signature_rows(clock, signatures, event):
    """Compare observed response signatures relative to their own matched controls."""
    subsections = {
        "all":list(CAPTURE),"pressure_only":[s for s in CAPTURE if s.startswith("PS")],
        "flow_only":[s for s in CAPTURE if s.startswith("MFS")],
        "without_MFS3":[s for s in CAPTURE if s != "MFS3"],"PS1_only":["PS1"],"MFS3_only":["MFS3"],
        "PS5_PS7":["PS5","PS7"]}
    rows = []
    for horizon in (1, 5, 30, 120, 600, 19000):
        use = (clock >= event) & (clock <= event+horizon)
        for a,b in combinations(signatures,2):
            for subset, keys in subsections.items():
                u,v = [np.concatenate([signatures[case][s][use] for s in keys]) for case in (a,b)]
                scale = np.linalg.norm(u)*np.linalg.norm(v)
                rows.append({"a":a,"b":b,"duration_s":horizon,"subset":subset,
                             "relative_rms_distance":float(np.sqrt(np.mean((u-v)**2))),
                             "cosine":float(np.clip(np.dot(u,v)/scale,-1,1)) if scale else None,
                             "samples_per_sensor":int(use.sum())})
    return rows


def pressure_rival_source(path):
    blocks = model_blocks(checked_file(path,MODEL_HASH))
    receiver, command = blocks["55"], blocks["59"]
    if (receiver["source_type"] != "foundation.enum.constant_controlled.controlled"
            or frozenset(("59#rconn:1", "55#lconn:2")) not in root_connections(path)):
        raise ValueError("pressure source command is not traceable")
    keys = ("step_time","step_time_unit","initial_value","initial_value_unit","final_value","final_value_unit")
    return {"source_sid":"55","command_sid":"59","saved_parameters":{k:command[k] for k in keys},
            "boundary_role":"Internal commanded pressure difference, distinct from atmospheric outlet withdrawal"}


def trace_profiles():
    normal = checked_file(SOURCE,MODEL_HASH)
    up = checked_file(ARCHIVE/"Normal_HNetwork_gest_up.slx",UP_SHA)
    down = ARCHIVE/"Normal_HNetwork_gest_down.slx"
    nc = root_connections(normal)
    checked = {}
    for name,path in (("up",up),("down",down)):
        candidate = root_connections(path)
        checked[name] = {"sha256":sha256(path),"removed_wires":[sorted(x) for x in sorted(nc-candidate,key=sorted)],
                         "added_wires":[sorted(x) for x in sorted(candidate-nc,key=sorted)],
                         "same_topology": nc==candidate}
    return checked


def uncertainty_evidence():
    convergence = read_json(REPORT11)
    summary = []
    for coarse,fine in ((0.8,0.4),(0.4,0.2),(0.8,0.2)):
        peaks = {}
        for unit in ("MPa","kg/s"):
            rows = (x for x in convergence["per_sensor"] if x["window"]=="entire" and
                    x["coarse_step_s"]==coarse and x["fine_step_s"]==fine and x["unit"]==unit)
            peak = max(rows,key=lambda x:x["max_absolute"])
            peaks[unit] = {"sensor":peak["sensor"],"max_abs":peak["max_absolute"]}
        summary.append({"coarse_s":coarse,"fine_s":fine,"max_observed_difference":peaks})
    return {"numerical":{"status":"OBSERVED_DELTAS_WITHOUT_ENCLOSURE","convergence_sha256":sha256(REPORT11),
                         "pairwise_observed_deltas":summary,
                         "event_split_mass_residual_kg":{k:v["final"]["step_split_simpson_residual_kg"]
                                                        for k,v in convergence["cases"].items()}},
            "measurement":"No signed calibration, bias, drift, resolution, or synchronization bounds",
            "model":"No independently bounded residual over a defined operating domain or validated gas composition",
            "parameter":"Configured source values and engineered command; no qualified tolerance sets",
            "operational":"One traceable Center schedule; no quantified distribution"}


def report(capture_root, output, matrix=None, reference=None):
    approved = read_json(VERIFIED/"experiment_manifest.json")
    results = read_json(VERIFIED/"paired_results.json")
    frames = {}
    registry = []
    for case in CASES:
        for name,digest in approved["cases"][case]["capture_sha256"].items():
            checked_file(capture_root/case/name,digest)
        frames[case] = mat(capture_root/case/"center_raw.mat")
        registry.append({"id":"A:"+case,"status":"ACCEPTED","source_family":"Center",
                         "capture_hashes":approved["cases"][case]["capture_sha256"]})
    clock = frames["normal"]["sensors"]["pressure_sensor1"]["time"]
    event = results["outlet_effect"]["onset_s"]
    rows = []
    def compare(study,control,variant):
        signals = {}
        for channel, key in CAPTURE.items():
            a,b = (capture["sensors"][key] for capture in (control,variant))
            if not all(np.array_equal(s["time"],clock) for s in (a,b)):
                raise ValueError("rival clock differs from the approved pair")
            x,y = a["values"],b["values"]
            delta = y-x
            pre, post = clock<event, clock>=event
            scale = np.sqrt(np.mean(x[pre]**2))
            if scale == 0:
                raise ValueError(f"zero baseline RMS: {channel}")
            signals[channel] = delta/scale
            before = metrics(y[pre],x[pre],clock[pre])
            after = metrics(y[post],x[post],clock[post])
            first = first_sustained(clock[post],delta[post],max(FLOOR,before["max_absolute"]))
            rows.append({"scenario":study,"sensor":channel,"unit":"MPa" if channel.startswith("PS") else "kg/s",
                         "baseline_rms":float(scale), "pre":before, "post":after, "first_descriptive_crossing_s":first,
                         "descriptive_response_delay_s":None if first is None else first-event,
                         "post_signed_integral":float(trapezoid(delta[post],clock[post])),
                         "post_absolute_integral":float(trapezoid(abs(delta[post]),clock[post]))})
        return signals
    opening = compare("A", frames["normal"], frames["outlet_opening"])
    zero = {key:np.zeros_like(value) for key,value in opening.items()}
    traces = {"NORMAL":zero,"SID213":opening}
    designs = rival_specs(SOURCE)
    rival_results = {}
    for key,spec in designs.items():
        root = matrix/key if matrix else None
        case_states = {}
        for case in CASES:
            diary = root / case / "execution.log" if root is not None else None
            started = diary is not None and diary.is_file()
            completed = started and "=== PHASE 12 CAPTURE COMPLETED ===" in diary.read_text(encoding="utf-8")
            case_states[case] = "COMPLETED_PENDING_PAIR_AUDIT" if completed else "STARTED_UNVERIFIED" if started else "AWAITING_INTERACTIVE_RUN"
        available = all(value == "COMPLETED_PENDING_PAIR_AUDIT" for value in case_states.values())
        if available and reference is None:
            raise ValueError("a Phase 11 reference is required when accepting new rival captures")
        receipts = {case:audit(root,None,reference,case,spec) for case in CASES} if available else {}
        for case in CASES:
            registry.append({"id":key+":"+case,"status":"ACCEPTED" if available else case_states[case],
                             "source_family":"Center","specification":spec,"receipt":receipts.get(case)})
        if available:
            control,variant = [mat(root/case/"center_raw.mat") for case in CASES]
            traces[key] = compare(key,control,variant)
            paired = [mat(root/case/"outlet_evidence.mat")["response"] for case in CASES]
            rate = paired[1]["signed_outlet_flow"]["values"] - paired[0]["signed_outlet_flow"]["values"]
            post = clock >= event
            decision = framework(clock,{name:variant["sensors"][signal]["values"] for name,signal in CAPTURE.items()},
                                 event,receipts["outlet_opening"]["capture_hashes"]["center_raw.mat"],
                                 spec["location"]["restriction_sid"],spec["location"]["reservoir_sid"])
            sheet = {}
            for case,capture in zip(CASES,(control,variant)):
                history, physical = conservation(capture,read_json(PHASE10),0.2)
                events = (int(np.searchsorted(clock,physical["step_bracket"][1]["time_s"])),)
                if case == "outlet_opening":
                    events += (int(np.searchsorted(clock,event)),)
                integrated = event_integral(clock,history.boundary_net_kg_s.to_numpy(),events)
                sheet[case] = {"final_mass_residual_kg":float(history.storage_change_kg.iloc[-1]-integrated[-1]),
                               "initial_mass_kg":physical["initial_storage_kg"],
                               "final_mass_kg":float(history.storage_kg.iloc[-1]),
                               "pointwise_residual_kg_s":physical["pointwise_max_abs_boundary_minus_storage_port_kg_s"]}
            rival_results[key] = {"onset_s":event,"outlet_max_pre_abs_kg_s":float(abs(rate[~post]).max()),
                                  "outlet_delta_onset_kg_s":float(rate[post][0]),"outlet_peak_post_kg_s":float(rate[post].max()),
                                  "outlet_final_delta_kg_s":float(rate[-1]),
                                  "outlet_post_integrated_delta_kg":float(trapezoid(rate[post],clock[post])),
                                  "mass":sheet,"framework":decision}
    pairs = signature_rows(clock,traces,event)
    normal_capture = frames["normal"]
    native = {row["path"]:row for row in normal_capture["logSeries"]}
    native_step = native["Pressure_Source_G3/P"]["values"]
    step_index = int(np.flatnonzero(native_step > (native_step[0]+native_step[-1])/2)[0])
    pressure_transition = {"source":pressure_rival_source(SOURCE),
                           "first_saved_post_step_s":float(clock[step_index]),
                           "prior_knot_s":float(clock[step_index-1]),
                           "pressure_command_before_after_Pa":[float(x) for x in native_step[step_index-1:step_index+1]],
                           "scope":"Observed source-control transition in the existing NORMAL run at its own clock and operating state. No isolated late pressure rival has executed.",
                           "observations": {sensor:{"sample_change":float(
                                   normal_capture["sensors"][CAPTURE[sensor]]["values"][step_index]-
                                   normal_capture["sensors"][CAPTURE[sensor]]["values"][step_index-1]),
                                   "unit":"MPa" if sensor.startswith("PS") else "kg/s"}
                               for sensor in CAPTURE}}
    archive = eligibility()
    profiles = trace_profiles()
    registry.extend([
        {"id":"D:SID55","status":"MECHANISM_TRACED_NO_MATCHED_INTERVENTION","source_family":"Center",
         "source_trace":pressure_rival_source(SOURCE),
         "evidence":"Native PS Step SID 59 controls Pressure Source (G) SID 55; existing step at 25 s drives 3 to 6.4 MPa. A second event-compatible perturbation needs a separately specified input and verified operating limits."},
        {"id":"E:OPERATING_PROFILE","status":"BLOCKED_AS_PROFILE_ONLY","profiles":profiles,
         "evidence":"Both alternative archives rewire gas topology. Their names do not establish an isolated operating-profile change."}])
    output.mkdir(parents=True)
    pd.DataFrame(pairs).to_csv(output/"subset_separability.csv",index=False)
    pd.json_normalize(rows).to_csv(output/"sensor_integrals.csv",index=False)
    write_json(output/"experiment_registry.json",{"registry":registry,"phase12_manifest_sha256":sha256(VERIFIED/"experiment_manifest.json"),
                                                  "approved_pair":approved["approved_pair"],"observed_signatures":list(traces)})
    write_json(output/"evaluation_eligibility.json",archive)
    write_json(output/"research_evidence.json",{
        "verified_pair":results["outlet_effect"],"conservation":results["mass"],
        "formal_decision":results["framework"],"rival_results":rival_results,"observed_native_pressure_transition":pressure_transition,
        "uncertainty":uncertainty_evidence(),
        "published_metrics":"Relative numerical signature distance normalized by each control's pre-event channel RMS; explanatory only. Cosine undefined for a zero response.",
        "status":archive["verdict"]})
    table = pd.DataFrame(pairs)
    plot_subsets(table,output/"subset_separability.png")
    plot_formal({"SID213":results["framework"], **{key:row["framework"] for key,row in rival_results.items()}},
                output/"formal_decisions.png")
    if rival_results:
        plot_matrix(table,list(traces),output/"observed_signature_matrix.png")
        plot_rivals(clock,event,traces,rows,output/"rival_responses.png")


def plot_subsets(table,path):
    from matplotlib import pyplot as plt

    select = table[(table.a=="NORMAL") & (table.b=="SID213")]
    fig, ax = plt.subplots(figsize=(8,4.5),layout="constrained")
    for label,rows in select.groupby("subset",sort=False):
        ax.plot(rows.duration_s,rows.relative_rms_distance,"o-",label=label.replace("_"," "),lw=1.2)
    ax.set(xscale="log",yscale="log",xlabel="Observation window after event (s)",
           ylabel="RMS difference / pre-event channel RMS",title="Observed Center NORMAL vs SID 213")
    ax.legend(ncol=2,fontsize=8)
    fig.savefig(path,dpi=220)
    plt.close(fig)


def plot_formal(decisions,path):
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(7.5,3.4),layout="constrained")
    names = list(decisions)
    counts = {key:[len(decisions[name]["diagnostic"]["certificate"][key]) for name in names]
              for key in ("feasible","excluded","indeterminate")}
    left = np.zeros(len(names))
    for key, color in zip(counts,("#1b9e77","#d95f02","#758395")):
        ax.barh(names,counts[key],left=left,label=key.upper(),color=color)
        left += counts[key]
    for i, name in enumerate(names):
        row = decisions[name]
        status = row["diagnostic"]["status"] + " / " + row["localization"]["level"]
        ax.text(left[i]+0.1,i,status,va="center",fontsize=9)
    ax.set_xlim(0,max(left)+2.5)
    ax.set_xlabel("Hypothesis count in the existing consistency engine")
    ax.legend(loc="lower center",bbox_to_anchor=(.5,1.01),ncol=3)
    fig.savefig(path,dpi=220)
    plt.close(fig)


def plot_rivals(clock,event,signatures,metrics_rows,path):
    from matplotlib import pyplot as plt

    lookup = {(("SID213" if row["scenario"]=="A" else row["scenario"]),row["sensor"]):row["baseline_rms"]
              for row in metrics_rows}
    select = (clock>=event-5)&(clock<=event+300)
    fig, axes = plt.subplots(3,1,sharex=True,layout="constrained",figsize=(8,6))
    for ax,sensor in zip(axes,("PS1","MFS1","MFS3")):
        for case,signature in signatures.items():
            if case != "NORMAL":
                ax.plot(clock[select],signature[sensor][select]*lookup[(case,sensor)],label=case,lw=1)
        ax.axvline(event,color="0.5",lw=.7,ls=":")
        ax.set_ylabel(sensor+" ("+("MPa" if sensor=="PS1" else "kg/s")+")")
    axes[0].legend()
    axes[-1].set_xlabel("Saved time (s)")
    fig.suptitle("Measured opening minus own matched control")
    fig.savefig(path,dpi=220)
    plt.close(fig)


def plot_matrix(table, labels, path):
    from matplotlib import pyplot as plt

    fig, axes = plt.subplots(1,2,layout="constrained",figsize=(8.5,4))
    for ax, subset in zip(axes,("all","pressure_only")):
        selected = table[(table.duration_s==30)&(table.subset==subset)]
        image = np.zeros((len(labels),len(labels)))
        for row in selected.itertuples():
            a,b = labels.index(row.a),labels.index(row.b)
            image[a,b] = image[b,a] = row.relative_rms_distance
        ax.imshow(image,cmap="Blues",vmin=0)
        for a,b in np.ndindex(image.shape):
            ax.text(b,a,f"{image[a,b]:.2g}",ha="center",va="center",
                    color="white" if image[a,b] > 0.55*image.max() else "black")
        ax.set(xticks=range(len(labels)),yticks=range(len(labels)),xticklabels=labels,yticklabels=labels,
               title=subset.replace("_"," "))
    fig.suptitle("Relative sensor-signature RMS distance, first 30 s")
    fig.savefig(path,dpi=220)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("prepare","approve","report"))
    p.add_argument("path",type=Path)
    p.add_argument("--output",type=Path)
    p.add_argument("--matrix",type=Path)
    p.add_argument("--reference",type=Path)
    a = p.parse_args()
    if a.action == "report":
        if a.output is None:
            p.error("report requires --output")
        report(a.path,a.output,a.matrix,a.reference)
    else:
        designs = rival_specs(SOURCE)
        if a.action == "prepare":
            a.path.mkdir(parents=True)
            for key,spec in designs.items():
                prepare(a.path/key,SOURCE,spec)
        else:
            for key,spec in designs.items():
                root = a.path / key
                if (root / "approval.json").is_file():
                    verify_pair(root,None,spec)
                else:
                    approve(root,spec)


if __name__ == "__main__":
    main()
