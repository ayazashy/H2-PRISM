"""Source-trace, prepare and validate Phase 13 command experiments."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

from .final_research import SOURCE, VERIFIED, pressure_rival_source, root_connections, signature_rows
from .phase10 import CAPTURE, model_blocks, sha256
from .phase11 import BOUNDARIES, PHASE10, conservation, read_json, write_json
from .phase12 import CASES, approve, prepare, specification
from .phase12_acceptance import audit, mat, verify_pair
from .phase12_pair import framework, sensor_comparison

PAIRS = ("pressure_rival", "alternate_profile")


def designs(reference):
    frozen = read_json(VERIFIED / "experiment_manifest.json")
    old = reference / "normal" / "center_raw.mat"
    if sha256(old) != frozen["cases"]["normal"]["capture_sha256"]["center_raw.mat"]:
        raise ValueError("Phase 12 scope or baseline hash mismatch")
    data = mat(old)
    histories = {row["path"]: row for row in data["logSeries"]}
    source = pressure_rival_source(SOURCE)
    blocks = model_blocks(SOURCE)
    for name, sid in (("receiver", "55"), ("command", "59")):
        source[f"{name}_library"] = " ".join(blocks[sid]["SourceBlock"].split())
    nets = root_connections(SOURCE)
    gas = [[sorted(n) for n in nets if f"55#{port}:1" in n] for port in ("lconn","rconn")]
    # SID 55 has two conserving connections and its separate physical-signal input.
    if any(len(n) != 1 for n in gas) or frozenset(("6#rconn:1","1#rconn:2")) not in nets:
        raise ValueError("pinned receiver topology changed")
    specs = {}
    evidence = {}
    for name, role, receiver, producer, port, path, t, control, treated in (
        ("pressure_rival","internal_pressure","55","59","P","Pressure_Source_G3/P",1000,"0","-0.17"),
        ("alternate_profile","boundary_pressure","1","6","P","Reservoir/P",500,"0.005","0.005"),
    ):
        row = histories[path]
        if row["unit"] != "Pa":
            raise ValueError("unexpected source command unit")
        clock, nominal = row["time"], row["values"]
        lower, upper = float(nominal.min()), float(nominal.max())
        effects = {}
        for case, offset in zip(CASES,(control,treated)):
            applied = nominal + (clock >= t) * (float(offset)*1e6)
            if not ((applied >= lower-1e-6).all() and (applied <= upper+1e-6).all()):
                raise ValueError(f"{name}: requested command exceeds its recorded range")
            effects[case] = {"min_pa":float(applied.min()),"max_pa":float(applied.max()),
                             "before_step_pa":float(applied[np.searchsorted(clock,t)-1]),
                             "at_step_pa":float(applied[np.searchsorted(clock,t)])}
        spec = specification()
        spec["pair"] = name
        spec["overlay"] = {"role":role,"receiver_sid":receiver,"producer_sid":producer,"port":port,
                           "receiver_log":path,"step_time":str(t),"normal_final":control,"intervention_final":treated,
                           "unit":"MPa","min_pa":lower,"max_pa":upper}
        if role == "internal_pressure":
            spec["area"]["intervention_final"] = spec["area"]["normal_final"]
            spec["mechanism"] = "Late reduction in internal pressure-source differential; constant outlet area"
            spec["design_basis"] = "0.17 MPa is 5% of the original 3.4 MPa step span, applied downward within the observed command envelope."
        else:
            spec["mechanism"] = "Matched SID 213 opening under a common reservoir pressure offset"
            spec["design_basis"] = "Both twins increase source reservoir pressure by 0.05 bar at 500 s, within the observed command range; the original command continues underneath."
        spec["matching"] = "Same pinned gas network, original initial-condition policy and logging. Identical overlays except the sole approved final step value."
        spec["initialization"] = "Start from the original solver initialization at 0 s. For the profile pair, allow 500 s of shared evolution between the boundary step and opening. Equilibrium is not presumed."
        specs[name] = spec
        evidence[name] = {"approved_command_envelope_Pa":[lower,upper],"calculated_commands":effects,
                          "qualification":"Command envelope is observed in the simulator. It is not a pressure rating or error bound."}
    return specs, {"source_sha256":sha256(SOURCE),"prior_raw_sha256":sha256(old),
                   "pressure_source":source,"conserving_nets_A_B":gas,
                   "metered_paths":"SID 55 is internal transfer; reservoir SID 1 is an external boundary.",
                   "designs":evidence}


def verify_case(matrix, reference, prior, pair, case):
    specs,_ = designs(prior)
    return audit(matrix/pair,None,reference,case,specs[pair])


def run_analysis(matrix, reference, prior, rivals, output):
    specs, source = designs(prior)
    clock = mat(prior/"normal/center_raw.mat")["sensors"]["pressure_sensor1"]["time"]
    figure, native = {}, {}
    reports, formal, physics, comparisons, windows = {}, {}, {}, [], []

    def add_comparison(study, control, intervention):
        rows, window_rows = sensor_comparison(clock, control, intervention, 1000)
        for row in rows + window_rows:
            row["study"] = study
        comparisons.extend(rows)
        windows.extend(window_rows)
    for pair,spec in specs.items():
        receipts = {case:validate_and_read(matrix/pair,reference,spec,case) for case in CASES}
        a,b = [receipts[case][1] for case in CASES]
        reports[pair] = {case:receipts[case][0] for case in CASES}
        aa,bb = [sensor_values(row,clock) for row in (a,b)]
        add_comparison(pair, aa, bb)
        figure[pair] = signature(clock,aa,bb)
        native[pair] = {name:bb[name]-aa[name] for name in CAPTURE}
        physics[pair] = physical_comparison(clock, a, b, spec)
        formal[pair] = framework(clock,bb,1000,reports[pair]["outlet_opening"]["capture_hashes"]["center_raw.mat"],
                                 ground_truth=("Late operational pressure command at SID 55" if pair=="pressure_rival"
                                               else "Outlet SID 213 under a shared reservoir pressure profile"))
    registry = read_json(prior_registry())
    accepted = {"A":prior,"sid312":rivals/"sid312","sid215":rivals/"sid215"}
    for key,root in accepted.items():
        for case in CASES:
            rec = next(item for item in registry["registry"] if item["id"]==key+":"+case)
            expected = rec.get("capture_hashes") or rec["receipt"]["capture_hashes"]
            if sha256(root/case/"center_raw.mat") != expected["center_raw.mat"]:
                raise ValueError(f"Previously accepted capture changed: {key}:{case}")
        a,b = [sensor_values(mat(root/case/"center_raw.mat"),clock) for case in CASES]
        figure[key] = signature(clock,a,b)
        native[key] = {name:b[name]-a[name] for name in CAPTURE}
        add_comparison(key, a, b)
    nominal = figure["A"]
    alternate = figure["alternate_profile"]
    profile = pd.DataFrame([
        {"sensor": name, "window_s": duration,
         "unit": "MPa" if name.startswith("PS") else "kg/s",
         "native_rms_response_change": float(np.sqrt(np.mean(
             (native["alternate_profile"][name][select]-native["A"][name][select])**2))),
         "normalized_rms_response_change": float(np.sqrt(np.mean((alternate[name][select]-nominal[name][select])**2)))}
        for duration in (1, 5, 30, 120, 600)
        for select in [(clock >= 1000) & (clock <= 1000+duration)]
        for name in CAPTURE
    ])
    figure = {"NORMAL":{sensor:np.zeros(len(clock)) for sensor in CAPTURE},**figure}
    table = pd.DataFrame(signature_rows(clock,figure,1000))
    output.mkdir(parents=True, exist_ok=False)
    table.to_csv(output/"confusability.csv",index=False)
    pd.DataFrame(comparisons).to_csv(output/"per_sensor.csv",index=False)
    pd.DataFrame(windows).to_csv(output/"observation_windows.csv",index=False)
    profile.to_csv(output/"profile_sensitivity.csv",index=False)
    write_json(output/"experiment_registry.json", {
        "historical_cases": registry["registry"], "phase13_cases": reports, "phase13_designs": specs,
        "scope": "Source-derived simulations in the same Center family",
    })
    write_json(output/"results.json",{"case_acceptance":reports,"formal":formal,"source":source,"incremental_physics":physics,
              "confirmatory_status":"CONFIRMATORY ACCURACY AND ADDED VALUE: NOT ESTABLISHED"})
    from .final_research import plot_matrix
    plot_matrix(table,list(figure),output/"confusability.png")
    plot_responses(clock, figure, output/"response_signatures.png")


def physical_comparison(clock, control, intervention, spec):
    event = 1000
    post = clock >= event
    before, after = ({row["path"]:row["values"] for row in capture["logSeries"]}
                     for capture in (control, intervention))
    location = spec["location"]
    paths = {**{name: name+"/mdot_A" for name in BOUNDARIES},
             "outlet":location.get("restriction_log_node", "Local_Restriction_G3")+"/mdot_A",
             "pressure_source_into_A":"Pressure_Source_G3/mdot_A"}
    result = {}
    for name, path in paths.items():
        factor = -1 if name in BOUNDARIES else 1
        delta = factor*(after[path]-before[path])
        result[name] = {"max_abs_pre_event_kg_s":float(abs(delta[~post]).max()),
                        "increment_at_event_kg_s":float(delta[post][0]),
                        "post_event_integral_kg":float(trapezoid(delta[post], x=clock[post]))}
    histories = [conservation(capture, read_json(PHASE10), 0.2)[0]
                 for capture in (control, intervention)]
    stock = histories[1].storage_change_kg.to_numpy()-histories[0].storage_change_kg.to_numpy()
    result["stock_change_differential_kg"] = float(stock[-1]-stock[post][0])
    result["flow_sign"] = "Boundary positive into the network; outlet positive toward the sink; SID 55 positive into source port A."
    return result


def plot_responses(clock, profiles, output):
    from matplotlib import pyplot as plt

    view = (clock >= 995) & (clock <= 1120)
    fig, axes = plt.subplots(3, 1, sharex=True, figsize=(9, 7), layout="constrained")
    labels = {"A": "SID 213 nominal", "sid312": "SID 312", "sid215": "SID 215",
              "pressure_rival": "SID 55 pressure", "alternate_profile": "SID 213 alternate profile"}
    for axis, name in zip(axes, ("PS1", "MFS1", "MFS3")):
        for study, label in labels.items():
            axis.plot(clock[view]-1000, profiles[study][name][view], label=label)
        axis.set_ylabel(f"{name} / control RMS")
        axis.axvline(0, color="0.5", linewidth=0.7)
    axes[0].legend(ncol=2)
    axes[-1].set_xlabel("Time from intervention (s)")
    fig.savefig(output, dpi=220)
    plt.close(fig)


def prior_registry():
    from .data.loader import WORKSPACE_ROOT
    return WORKSPACE_ROOT/"03_results/validation/final_research/experiment_registry.json"


def validate_and_read(root, reference, spec, case):
    report = audit(root,None,reference,case,spec)
    return report, mat(root/case/"center_raw.mat")


def sensor_values(data,clock):
    output = {}
    for sensor,key in CAPTURE.items():
        row = data["sensors"][key]
        if not np.array_equal(row["time"],clock):
            raise ValueError("sensor clocks differ from the approved common clock")
        output[sensor] = row["values"]
    return output


def signature(clock,a,b):
    return {name:(b[name]-value)/np.sqrt(np.mean(value[clock<1000]**2)) for name,value in a.items()}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=("prepare","approve","validate","analyze"))
    p.add_argument("matrix",type=Path)
    p.add_argument("prior",type=Path)
    p.add_argument("--reference",type=Path)
    p.add_argument("--rivals",type=Path)
    p.add_argument("--pair",choices=PAIRS)
    p.add_argument("--case",choices=CASES)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    if args.action == "analyze":
        if not all((args.reference,args.rivals,args.output)):
            p.error("analyze requires --reference, --rivals and --output")
        run_analysis(args.matrix,args.reference,args.prior,args.rivals,args.output)
        return
    specs,source=designs(args.prior)
    if args.action=="prepare":
        args.matrix.mkdir(parents=True)
        for key,spec in specs.items():
            prepare(args.matrix/key,SOURCE,spec)
        write_json(args.matrix/"source_qualification.json",source)
    elif args.action=="approve":
        for key,spec in specs.items():
            root=args.matrix/key
            if (root/"approval.json").is_file():
                verify_pair(root,None,spec)
            else:
                approve(root,spec)
    else:
        if not all((args.reference,args.pair,args.case)):
            p.error("validate requires --reference, --pair and --case")
        record=verify_case(args.matrix,args.reference,args.prior,args.pair,args.case)
        output=args.matrix/args.pair/args.case/"phase13_acceptance.json"
        if output.is_file():
            if read_json(output)["capture_hashes"] != record["capture_hashes"]:
                raise ValueError("Existing Phase 13 acceptance hashes differ")
        else:
            write_json(output,record)
        print(f"ACCEPTED {args.pair}/{args.case}")


if __name__=="__main__":
    main()
