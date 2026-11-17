import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from scipy.integrate import trapezoid
from scipy.io import loadmat
from h2prism.phase13 import (CAPTURE, CASES, designs, physical_comparison, prior_registry,
                            read_json, sensor_values, sha256, validate_and_read)
from h2prism.phase12_acceptance import verify_pair
from h2prism.phase12_pair import framework, sensor_comparison

def main(base, out):
    work = base / "work"
    prior = work / "phase12_sdi_retry_01"
    matrix = work / "phase13_02"
    reference = work / "phase11_cases/step_0.2"
    rivals = work / "final_research_matrix"
    specs, source = designs(prior)
    accepted = {}
    captures = {}
    paired = {}
    physics = {}
    recovered = work / "phase13_alternate_retry_02"
    histories = {}
    for pair, names in (("pressure_rival", CASES), ("alternate_profile", CASES)):
        for name in names:
            case_root = recovered if (pair, name) == ("alternate_profile", "outlet_opening") else matrix / pair
            report, data = validate_and_read(case_root, reference, specs[pair], name)
            if case_root == recovered:
                assert report["pair"]["cases"] == accepted["alternate_profile:normal"]["pair"]["cases"]
            else:
                assert report["capture_hashes"] == read_json(case_root / name / "phase13_acceptance.json")["capture_hashes"]
            accepted[pair + ":" + name] = report
            key = pair + ":" + name
            captures[key] = {"sensors":data["sensors"]}
            logs = {r["path"]:r["values"] for r in data["logSeries"]}
            clock = data["sensors"]["pressure_sensor1"]["time"]
            paths = ("Reservoir/P","Reservoir/A/p","Reservoir/mdot_A","Pressure_Source_G3/P",
                     "Pressure_Source_G3/A/p","Pressure_Source_G3/B/p","Pressure_Source_G3/mdot_A","Pressure_Source_G3/mdot_B")
            histories[key] = {p: {str(t):float(logs[p][np.searchsorted(clock,t)]) for t in (499.8,500,999.8,1000,1000.2,20000)} for p in paths}
            paired[name] = data
            if name == "outlet_opening":
                physics[pair] = physical_comparison(clock, paired["normal"], data, specs[pair])
                paired.clear()
            del data, logs
    registry = read_json(prior_registry())["registry"]
    for study, folder in (("A", prior), ("sid312", rivals / "sid312"), ("sid215", rivals / "sid215")):
        for case in CASES:
            key = study + ":" + case
            rec = next(r for r in registry if r["id"] == key)
            hashes = rec.get("capture_hashes") or rec["receipt"]["capture_hashes"]
            assert all(sha256(folder / case / file) == digest for file, digest in hashes.items())
            captures[key] = loadmat(folder / case / "center_raw.mat", simplify_cells=True, variable_names=["sensors"])
    failroot = matrix / "alternate_profile"
    failed = failroot / "outlet_opening"
    approval = verify_pair(failroot, None, specs["alternate_profile"])
    failure = {"file_hashes": {p.name: sha256(p) for p in failed.iterdir() if p.is_file()},
               "stages": (failed / "stages.log").read_text().splitlines(),
               "exception": (failed / "execution.log").read_text(), "approval": approval,
               "status": "BLOCKED: no returned simulation output or solver diagnostic; underlying cause unverified"}
    clock = captures["A:normal"]["sensors"]["pressure_sensor1"]["time"]
    post = clock >= 1000
    names = list(CAPTURE)
    rows, windows, traces, decisions = [], [], {}, {}
    values = {key: sensor_values(data, clock) for key, data in captures.items()}
    scale = np.array([np.sqrt(np.mean(values["A:normal"][n][~post]**2)) for n in names])
    assert np.all(np.isfinite(scale) & (scale > 0))
    traces["NORMAL"] = np.zeros((post.sum(), len(names)))
    for study in ("A", "sid312", "sid215", "pressure_rival", "alternate_profile"):
        a, b = (values[study + ":" + case] for case in CASES)
        records, win = sensor_comparison(clock, a, b, 1000)
        for r in records:
            delta = (b[r["sensor"]] - a[r["sensor"]])[post]
            r["signed_integral_native_unit_s"] = float(trapezoid(delta, x=clock[post]))
            r["absolute_integral_native_unit_s"] = float(trapezoid(abs(delta), x=clock[post]))
        rows.extend(dict(r, study=study) for r in records)
        windows.extend(dict(r, study=study) for r in win)
        traces[study] = np.column_stack([(b[n] - a[n])[post] for n in names]) / scale
    for key, data in values.items():
        result = framework(clock, data, 1000, sha256_for(key, accepted, registry), ground_truth=key)
        cert = result["diagnostic"]["certificate"]
        # A conventional singleton rule abstains unless there is one feasible candidate and no unknown rival.
        policy_a = ("SPECIFIC" if len(cert["feasible"]) == 1 and not cert["indeterminate"] else "UNRESOLVED")
        decisions[key] = {"policy_a": policy_a, "policy_b": result}
    subsets = {"all": names, "pressure": [n for n in names if n.startswith("PS")],
               "flow": [n for n in names if n.startswith("MFS")], "PS1_MFS3": ["PS1", "MFS3"],
               **{n: [n] for n in names}, **{"omit_" + n: [m for m in names if m != n] for n in names}}
    distance, sensitivity = [], []
    for duration in (1, 5, 10, 30, 60, 120):
        t = clock[post] <= 1000 + duration
        for subset, sensors in subsets.items():
            idx = [names.index(n) for n in sensors]
            selected = {k: v[t][:,idx] for k,v in traces.items()}
            for a,b in combinations(selected,2):
                delta = selected[a]-selected[b]
                distance.append(dict(a=a,b=b,seconds=duration,subset=subset,rms=np.sqrt(np.mean(delta**2)), box_transition=np.max(abs(delta))))
            if subset in ("all","pressure","flow","PS1_MFS3"):
                for a,x in selected.items():
                    thresholds = {b: np.max(abs(x-y)) for b,y in selected.items()}
                    for measurement in (0, 0.0001, 0.001, 0.01, 0.1):
                        for model in (0, 0.0001, 0.001, 0.01, 0.1):
                            members = [b for b,d in thresholds.items() if d <= measurement+model]
                            sensitivity.append(dict(observation=a,seconds=duration,subset=subset,
                                measurement_halfwidth_fraction=measurement,model_halfwidth_fraction=model,
                                member_count=len(members),members=" ".join(members)))
    out.mkdir(parents=True)
    df = pd.DataFrame(distance)
    df.to_csv(out/"pairwise.csv",index=False)
    pd.DataFrame(rows).to_csv(out/"per_sensor.csv",index=False)
    pd.DataFrame(windows).to_csv(out/"windows.csv",index=False)
    sf = pd.DataFrame(sensitivity)
    sf.to_csv(out/"hypothetical_sensitivity.csv",index=False)
    (out/"evidence.json").write_text(json.dumps(dict(accepted=accepted, historical=registry, source=source,
        failure=failure, physical_comparison=physics, physical_knots=histories, decisions=decisions,
        normalizers=dict(zip(names,scale))),indent=2,allow_nan=False,default=lambda value: value.tolist()),encoding="utf8")
    fig, axes = plt.subplots(3,1,sharex=True,layout="constrained",figsize=(8,7))
    view = clock[post] <= 1120
    for ax,name in zip(axes,("PS1","MFS1","MFS3")):
        j=names.index(name)
        for k,color in zip(("pressure_rival","A","sid312","sid215","alternate_profile"),("#143253","#078781","#3678af","#5f677d","#775a98")):
            ax.plot(clock[post][view]-1000,traces[k][view,j]*scale[j],label=k,color=color)
        ax.set_ylabel(name + (" (MPa)" if name.startswith("PS") else " (kg/s)"))
    axes[0].legend()
    axes[-1].set_xlabel("Seconds after intervention")
    fig.savefig(out/"responses.png",dpi=240)
    plt.close(fig)

def sha256_for(key, accepted, registry):
    if key in accepted:
        return accepted[key]["capture_hashes"]["center_raw.mat"]
    rec = next(r for r in registry if r["id"]==key)
    return (rec.get("capture_hashes") or rec["receipt"]["capture_hashes"])["center_raw.mat"]

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("base",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    main(args.base,args.output)
