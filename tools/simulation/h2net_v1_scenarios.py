#!/usr/bin/env python3
"""
H2Net v1 scenario pipeline (design-freeze spec section 3-4). Deterministic from the decision record + master seed.

  plan   -> h2net_v1_run/scenarios/SCENARIO_PLAN.json (inputs per run, opaque run ids) + LABELS.csv (kept separate)
            + PARTITIONS.json. Needs the 'scenarios' and S4 sections decided; generating a PLAN runs nothing.
  check  -> shortcut / independence checks on the plan (exit 2 on any violation)
  noise  -> adds the APPROVED measurement noise (methods_review.value.noise_model, cited sources) to simulated runs
            h2net_v1_run/dataset/raw/<run_id>.csv -> h2net_v1_run/dataset/noisy/<run_id>.csv  (gate 'dataset')
Independence: family = initial state (topology, demand level, allocation, C2 set-point); all siblings of a family share
one partition; ancestry = [IS:<family hash>, LP:<load seed>]. Onset t0 is drawn once per operating condition and shared
by every sibling (NORMAL carries it as a pseudo-onset), so siblings are identical before t0.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_gates as gates  # noqa: E402

REPO = gates.REPO
sys.path.insert(0, str(REPO / "src"))
from h2prism import data_contracts as dc  # noqa: E402

TOPOS = {"center": "Normal_HNetwork_gest_center", "up": "Normal_HNetwork_gest_up", "down": "Normal_HNetwork_gest_down"}
ALLOC = {"nominal": {}, "shift_G3G5_+25pct": {"G3": 1.25, "G5": 1.25, "G4": 0.75, "G6": 0.75}}
CLASS_NAMES = ("NORMAL", "LEAK", "COMPRESSOR_FAULT", "DELAY")


def _h(*parts) -> str:
    return hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()


def _decided(dec, key):
    v = dec.get(key) or {}
    if v.get("decided") is not True or not gates._named(v.get("decided_by")):
        raise SystemExit(f"REFUSED: {key} must be decided with a named decided_by")
    return v["value"]


_GAS = []


def _leak_area(pt: dict, pipe_sid: str, flow: float, cd: float, T: float) -> float:
    """Orifice area giving FLOW (kg/s) at the pipe's upstream steady pressure (choked nozzle, local H2 Z and cp)."""
    from h2prism.gas_physics import PerfectGas, orifice_mass_flow
    sys.path.insert(0, str(REPO / "tools" / "simulation"))
    from h2net_v1_reference import load_h2_tables
    if not _GAS:
        _GAS.append(load_h2_tables())
    gas = _GAS[0]
    e = next(x for x in pt["pipes"] if x["sid"] == str(pipe_sid))
    p_up = e["p_in_MPa"] * 1e6
    pr = gas.props(p_up, T)
    flux = orifice_mass_flow(p_up, 101325.0, T, 1.0, PerfectGas(R=gas.R, Z=pr["Z"], cp=pr["cp"], mu=pr["mu"], k=pr["k"]), cd)
    return flow / flux


def _interp_c2(targets_pts, mult):
    xs = [p["demand_multiplier"] for p in targets_pts]
    ys = [next(c["dp_MPa"] for c in p["compressors"] if c["compressor"] == "C2") for p in targets_pts]
    return float(np.interp(mult, xs, ys))


def _load_signal(kind, base, lp, t0, T, sinus_phase):
    if kind == "constant":
        return [[0, base], [T, base]]
    if kind == "step":
        return [[0, base], [t0, base], [t0 + 10, base * (1 + lp["step_fraction"])], [T, base * (1 + lp["step_fraction"])]]
    if kind == "ramp":
        e = min(t0 + lp["ramp_s"], T)
        return [[0, base], [t0, base], [e, base * (1 + lp["ramp_fraction"])], [T, base * (1 + lp["ramp_fraction"])]]
    ts = np.arange(0, T + 60, 60.0)
    return [[float(t), float(base * (1 + lp["sinus_fraction"] * np.sin(2 * np.pi * t / lp["sinus_period_s"] + sinus_phase)))] for t in ts]


def plan(dec: dict, targets: dict) -> dict:
    sc, s4 = _decided(dec, "scenarios"), dec["S4_demand_and_leaks"]["value"]
    s3 = dec["S3_compressor_stations"]["value"]
    rng = np.random.default_rng(int(sc["master_seed"]))
    T, lo_hi = float(sc["run_duration_s"]), sc["onset_window_s"]
    lp, leaks = s4["load_profiles"], s4["leaks"]
    nominal = {k: float(v) for k, v in s4["nominal_demand_kg_s"].items()}
    runs, labels, families = [], [], {}
    for pos, model in TOPOS.items():
        pts = targets["targets"].get(model)
        if not isinstance(pts, list):
            continue
        combos = [(lv, al, c2) for lv in s4["demand_levels"] for al in s4.get("allocation_variants", ["nominal"]) for c2 in sc["c2_setpoints_MPa"]]
        need = sc["families_per_topology"]["development"] + sc["families_per_topology"]["confirmation"]
        if len(combos) < need:
            raise SystemExit(f"REFUSED: only {len(combos)} distinct initial states for {need} families in {pos}")
        idx = rng.permutation(len(combos))[:need]
        for j, ci in enumerate(idx):
            lv, al, c2 = combos[ci]
            fam = _h("IS", pos, lv, al, c2)[:16]
            part = "development" if j < sc["families_per_topology"]["development"] else "confirmation"
            families[fam] = {"topology": pos, "demand_level": lv, "allocation": al, "c2_setpoint_MPa": c2, "partition": part}
            kind = lp["types"][int(rng.integers(len(lp["types"])))]
            t0 = float(rng.uniform(lo_hi[0], lo_hi[1]))
            load_seed, noise_seed, phase = int(rng.integers(2**31)), int(rng.integers(2**31)), float(rng.uniform(0, 2 * np.pi))
            dem = {k: v * lv * ALLOC[al].get(k, 1.0) for k, v in nominal.items()}
            p_nom = min(pts, key=lambda p: abs(p["demand_multiplier"] - lv))
            dp1 = next(c["dp_MPa"] for c in p_nom["compressors"] if c["compressor"] == "C1")
            dp2 = _interp_c2(pts, lv) + (c2 - float(s3["C2_pressure_source_sid_239"]["discharge_setpoint_MPa"]))
            change = {"step": lp["step_fraction"], "ramp": lp["ramp_fraction"]}.get(kind, 0.0)
            dp2_after = _interp_c2(pts, lv * (1 + change)) + (dp2 - _interp_c2(pts, lv))
            sib = [("NORMAL", {})]
            sizes = leaks["classes_percent"]
            for i, pipe in enumerate(leaks["pipes"]):
                sib.append(("LEAK", {"pipe": str(pipe), "severity_percent": sizes[(i + j) % len(sizes)]}))
            sib += [("COMPRESSOR_FAULT", {"fault": f}) for f in sc["faults"]]
            if kind in ("step", "ramp"):
                sib += [("DELAY", {"delay_s": float(d)}) for d in sc["delays_s"]]
            for s_i, (cls, ev) in enumerate(sib):
                rid = _h("RUN", sc["master_seed"], fam, s_i)[:20]
                sig = {f"h2_demand_{k}": _load_signal(kind, v, lp, t0, T, phase) for k, v in dem.items()}
                f1 = {"C1_trip": 0.0, "C1_half": 0.5}.get(ev.get("fault"), 1.0)
                f2 = {"C2_trip": 0.0, "C2_half": 0.5}.get(ev.get("fault"), 1.0)
                sig["h2_dp_C1"] = [[0, dp1], [t0, dp1], [t0 + 10, dp1 * f1], [T, dp1 * f1]]
                tc = t0 + ev.get("delay_s", 0.0)
                sig["h2_dp_C2"] = [[0, dp2], [min(tc, T), dp2], [min(tc + 10, T), dp2_after * f2], [T, dp2_after * f2]] if change else \
                                  [[0, dp2], [t0, dp2], [t0 + 10, dp2 * f2], [T, dp2 * f2]]
                for pipe in leaks["pipes"]:
                    sig[f"h2_leak_area_{pipe}"] = [[0, 0.0], [T, 0.0]]
                if cls == "LEAK":
                    Tref = float(dec["operating_envelope_V8"]["value"]["isothermal_reference_temperature_K"])
                    if leaks["severity_definition"] == "A":       # fraction of this OC's actual throughput
                        area = _leak_area(p_nom, ev["pipe"], ev["severity_percent"] / 100 * sum(dem.values()), float(leaks["Cd"]), Tref)
                    elif leaks["severity_definition"] == "B":     # fixed class area, sized once at the nominal point
                        p1 = min(pts, key=lambda q: abs(q["demand_multiplier"] - 1.0))
                        area = _leak_area(p1, ev["pipe"], ev["severity_percent"] / 100 * sum(nominal.values()), float(leaks["Cd"]), Tref)
                    else:
                        raise SystemExit("REFUSED: S4.value.leaks.severity_definition must be A or B")
                    sig[f"h2_leak_area_{ev['pipe']}"] = [[0, 0.0], [t0, 0.0], [t0 + leaks["onset_ramp_s"], area], [T, area]]
                runs.append({"run_id": rid, "family": fam, "topology": pos, "model": f"h2net_v1_{pos}", "stop_time_s": T,
                             "sample_period_s": sc["sample_period_s"], "noise_seed": noise_seed, "ancestry": [f"IS:{fam}", f"LP:{load_seed}"],
                             "partition": part, "signals": sig})
                labels.append({"run_id": rid, "class": cls, "event": json.dumps(ev, sort_keys=True), "onset_s": round(t0, 3),
                               "family": fam, "partition": part, "load_profile": kind, "severity_definition": leaks["severity_definition"]})
    return {"runs": runs, "labels": labels, "families": families}


def check(p: dict) -> list:
    v = []
    lab = {l["run_id"]: l for l in p["labels"]}
    for r in p["runs"]:
        if any(c.lower() in r["run_id"].lower() for c in CLASS_NAMES) or any(c in json.dumps(r) for c in CLASS_NAMES):
            v.append(f"{r['run_id']}: class name visible in the run definition")
    by_fam = {}
    for l in p["labels"]:
        by_fam.setdefault(l["family"], set()).add(l["onset_s"])
    v += [f"family {f}: siblings do not share one onset" for f, s in by_fam.items() if len(s) > 1]
    records = [dc.RunRecord(r["run_id"], r["topology"], r["family"], lab[r["run_id"]]["class"], lab[r["run_id"]]["onset_s"], {"H2": 1.0},
                            {"generator": "h2net_v1_scenarios", "file_sha256": "planned"}, tuple(r["ancestry"])) for r in p["runs"]]
    v += dc.check_partition_integrity(records, {r["run_id"]: r["partition"] for r in p["runs"]})
    for cls in ("LEAK", "COMPRESSOR_FAULT"):
        fams = {l["family"] for l in p["labels"] if l["class"] == cls}
        if fams != {l["family"] for l in p["labels"] if l["class"] == "NORMAL"}:
            v.append(f"{cls} is not present in every family (matched design broken)")
    return v


def add_noise(run_csv: Path, out_csv: Path, noise_model: dict, seed: int):
    sig = {"pressure": noise_model["pressure"]["sigma_kPa"] / 1e3, "flow": noise_model["mass_flow"]["sigma_kg_s"],
           "temperature": noise_model["temperature"]["sigma_K"]}
    rng = np.random.default_rng(seed)
    with open(run_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    head, data = rows[0], np.array(rows[1:], dtype=float)
    for j, h in enumerate(head):
        k = "pressure" if h.startswith("pressure") else "flow" if h.startswith("flow") else "temperature" if h.startswith("temperature") else None
        if k:
            data[:, j] += rng.normal(0.0, float(sig[k]), len(data))
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(head)
        w.writerows(data.tolist())


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("cmd", choices=["plan", "check", "noise"])
    a.add_argument("--run", type=Path, default=gates.RUN)
    a.add_argument("--decisions", type=Path, default=gates.DECISIONS)
    args = a.parse_args(argv)
    sd = args.run / "scenarios"
    if args.cmd == "plan":
        dec = yaml.safe_load(args.decisions.read_text(encoding="utf-8"))
        tp = args.run / "targets" / "V2_TARGETS.json"
        if not tp.exists():
            print("REFUSED: V2 targets missing")
            return 2
        p = plan(dec, json.loads(tp.read_text(encoding="utf-8")))
        sd.mkdir(parents=True, exist_ok=True)
        (sd / "SCENARIO_PLAN.json").write_text(json.dumps({"decisions_sha256": gates.sha(args.decisions), "runs": p["runs"]}, indent=1) + "\n", encoding="utf-8")
        (sd / "PARTITIONS.json").write_text(json.dumps(p["families"], indent=1) + "\n", encoding="utf-8")
        with open(sd / "LABELS.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(p["labels"][0]), lineterminator="\n")
            w.writeheader()
            w.writerows(p["labels"])
        viol = check(p)
        print(f"{len(p['runs'])} runs in {len(p['families'])} families -> {sd}; checks: {'PASS' if not viol else viol[:5]}")
        return 0 if not viol else 2
    if args.cmd == "check":
        runs = json.loads((sd / "SCENARIO_PLAN.json").read_text(encoding="utf-8"))["runs"]
        labels = list(csv.DictReader(open(sd / "LABELS.csv", encoding="utf-8")))
        for l in labels:
            l["onset_s"] = float(l["onset_s"])
        viol = check({"runs": runs, "labels": labels})
        print("PLAN CHECK: " + ("PASS" if not viol else "FAIL"))
        for x in viol[:20]:
            print("  - " + x)
        return 0 if not viol else 2
    probs = gates.check("dataset")
    if probs:
        print("REFUSED: dataset gate closed:\n  - " + "\n  - ".join(probs))
        return 2
    dec = yaml.safe_load(args.decisions.read_text(encoding="utf-8"))
    nm = dec["methods_review"]["value"]["noise_model"]
    runs = {r["run_id"]: r for r in json.loads((sd / "SCENARIO_PLAN.json").read_text(encoding="utf-8"))["runs"]}
    n = 0
    for f in sorted((args.run / "dataset" / "raw").glob("*.csv")):
        add_noise(f, args.run / "dataset" / "noisy" / f.name, nm, runs[f.stem]["noise_seed"])
        n += 1
    print(f"noise added to {n} runs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
