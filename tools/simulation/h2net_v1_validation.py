#!/usr/bin/env python3
"""
H2Net v1 physical-validation EVALUATOR (V2, V3, V4, V5, V6, V8, D1). Reads the raw MATLAB results written by
tools/matlab/h2prism_validate_h2net_v1.m (h2net_v1_run/validation/VALIDATION_RAW.json), the V2 targets, the decided build
spec, BUILD_REPORT.json and the decision record; writes h2net_v1_run/validation/VALIDATION_REPORT.json.
Thresholds come from the specification (V2: pressures within 0.5 % of the network pressure drop, flows within 1 %;
V6: 0.5 %) and from the decision record (V3 band: S3.value.aftercoolers.outlet_tolerance_K; V4 tolerance:
methods_review.value.v4_tolerance_fraction). A missing threshold or missing raw data gives NOT_EVALUABLE, never PASS.
overall = PASS only if V2, V3, V4, V5, V6, V8 and D1 are all PASS. V7 is separate (own grant); D2 is checked per dataset.
Usage: python tools/simulation/h2net_v1_validation.py [--run DIR] [--decisions PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_gates as gates  # noqa: E402

DRIFT_MAX = 1e-4          # steady-state criterion on the last 10 % of a validation run


def _expected(kind: dict, pt: dict):
    if kind["kind"] == "pressure":
        return pt["node_pressures_MPa"].get(kind["net"]), "pressure"
    if kind["kind"] == "flow":
        return next((e["mdot_kg_s"] for e in pt["pipes"] if e["sid"] == kind["pipe_sid"]), None), "flow"
    if kind["kind"] == "demand":
        return pt["demand_kg_s"].get(kind["outlet"]), "flow"
    if kind["kind"] == "chamber":
        return 0.0, "flow"
    return None, None


def v2(raw_m, pts, smap):
    res, ok = [], True
    for r in raw_m.get("V2", []):
        pt = next(p for p in pts if abs(p["demand_multiplier"] - r["demand_multiplier"]) < 1e-9)
        dp_net = sum(e["dp_kPa"] for e in pt["pipes"]) * 1e-3          # MPa: total frictional drop of the network
        tol_p = 0.005 * dp_net
        for var, kind in smap.items():
            exp, q = _expected(kind, pt)
            got = r["values"].get(var)
            if exp is None or got is None:
                if got is None and kind["kind"] != "flow_at_net":
                    ok = False
                    res.append({"var": var, "point": r["demand_multiplier"], "result": "MISSING"})
                continue
            err = abs(got["last"] - exp)
            passed = (err <= tol_p) if q == "pressure" else (err <= max(0.01 * abs(exp), 1e-3))
            steady = got["drift"] <= DRIFT_MAX
            ok &= passed and steady
            res.append({"var": var, "point": r["demand_multiplier"], "expected": exp, "simulated": got["last"], "abs_error": err,
                        "tolerance": tol_p if q == "pressure" else max(0.01 * abs(exp), 1e-3), "steady": steady,
                        "result": "PASS" if passed and steady else "FAIL"})
    if not raw_m.get("V2"):
        return "NOT_EVALUABLE", res
    return ("PASS" if ok else "FAIL"), res


def v3(raw_m, pts, dec):
    tol = ((dec.get("S3_compressor_stations") or {}).get("value") or {}).get("aftercoolers", {}).get("outlet_tolerance_K")
    target = ((dec.get("S3_compressor_stations") or {}).get("value") or {}).get("aftercoolers", {}).get("outlet_temperature_K")
    if tol is None or target is None or not raw_m.get("V2"):
        return "NOT_EVALUABLE", "S3.value.aftercoolers.outlet_tolerance_K (decision) or raw data missing"
    rows = []
    for r in raw_m["V2"]:
        for k in ("C1", "C2"):
            got = r["values"].get(f"temperature_sensor_{k}_out")
            rows.append({"point": r["demand_multiplier"], "compressor": k, "T_K": got and got["last"],
                         "result": "PASS" if got and abs(got["last"] - target) <= tol else "FAIL"})
    return ("PASS" if all(x["result"] == "PASS" for x in rows) else "FAIL"), rows


def v4(raw_m, dec, nominal_raw):
    tol = ((dec.get("methods_review") or {}).get("value") or {}).get("v4_tolerance_fraction")
    if tol is None or not raw_m.get("V4") or nominal_raw is None:
        return "NOT_EVALUABLE", "methods_review.value.v4_tolerance_fraction (Faisal) or raw data missing"
    base = nominal_raw["values"].get("flow_sensor_MFS0", {}).get("last")
    rows = []
    for r in raw_m["V4"]:
        leak = r["values"].get("flow_sensor_MFS0", {}).get("last")
        sim = None if (leak is None or base is None) else leak - base
        exp = r.get("expected_leak_kg_s_nozzle")
        rows.append({"leak": r["leak"], "simulated_leak_kg_s": sim, "nozzle_formula_kg_s": exp,
                     "rel_diff": None if (sim is None or not exp) else abs(sim - exp) / exp})
    ok = all(x["rel_diff"] is not None and x["rel_diff"] <= tol for x in rows)
    return ("PASS" if ok else "FAIL"), rows


def v6(raw_m):
    d = raw_m.get("V6") or {}
    if not d.get("ref") or not d.get("tight"):
        return "NOT_EVALUABLE", "raw data missing"
    rows = []
    for k, a in d["ref"].items():
        b = d["tight"].get(k)
        if b is None:
            continue
        rel = abs(a["last"] - b["last"]) / max(abs(b["last"]), 1e-6)
        rows.append({"var": k, "rel_change": rel, "result": "PASS" if rel < 0.005 else "FAIL"})
    return ("PASS" if rows and all(r["result"] == "PASS" for r in rows) else "FAIL"), rows


def v8(raw_m, dec):
    env = ((dec.get("operating_envelope_V8") or {}).get("value") or {}).get("normal") or {}
    lo, hi = env.get("pressure_MPa", [None, None])
    tmax = (env.get("temperature_K") or [None, None])[1]
    if lo is None or not raw_m.get("V2"):
        return "NOT_EVALUABLE", "envelope or raw data missing"
    bad = []
    for r in raw_m["V2"]:
        for var, got in r["values"].items():
            if var.startswith("pressure_sensor") and not (lo - 0.05 <= got["last"] <= hi):   # supply node may sit at 3.2
                if got["last"] > 0.2:                                                           # ignore atmospheric-side sensors
                    bad.append({"point": r["demand_multiplier"], "var": var, "value": got["last"]})
            if var.startswith("temperature_sensor") and tmax and got["last"] > tmax:
                bad.append({"point": r["demand_multiplier"], "var": var, "value": got["last"]})
    return ("PASS" if not bad else "FAIL"), bad


def d1(build, spec):
    if not build or build.get("status") != "COMPLETE":
        return "FAIL", "BUILD_REPORT not COMPLETE"
    rows = []
    for name, m in spec["models"].items():
        if "operations" not in m:
            continue
        b = next((x for x in build.get("models", []) if x["model"] == name), None)
        want = {o["id"] for o in m["operations"] if o["op"] not in ("apply_h2_tables", "log_existing_or_check")}
        got = {d["id"] for d in (b or {}).get("diff", [])}
        rows.append({"model": name, "missing_ops": sorted(want - got), "released_hash_ok": bool(b and b.get("released_hash_ok")),
                     "copy_sha256": b and b.get("copy_sha256")})
    ok = rows and all(not r["missing_ops"] and r["released_hash_ok"] and r["copy_sha256"] for r in rows)
    return ("PASS" if ok else "FAIL"), rows


def evaluate(run: Path, decisions: Path) -> dict:
    dec = yaml.safe_load(decisions.read_text(encoding="utf-8"))
    rd = lambda p: json.loads(p.read_text(encoding="utf-8")) if p.exists() else None  # noqa: E731
    raw = rd(run / "validation" / "VALIDATION_RAW.json") or {"models": {}}
    T = rd(run / "targets" / "V2_TARGETS.json") or {"targets": {}}
    spec = rd(run / "build" / "H2NET_V1_BUILD_SPEC_DECIDED.json") or {"models": {}}
    build = rd(run / "build" / "BUILD_REPORT.json")
    rep = {"decisions_sha256": gates.sha(decisions), "models": {}}
    status = {}
    for name, m in spec["models"].items():
        if "operations" not in m:
            continue
        rm = raw["models"].get(name, {})
        pts = T["targets"].get(name) or []
        leaks = {o["id"]: o for o in m["operations"] if o["op"] == "split_pipe_with_leak"}
        for r in rm.get("V4", []):
            r["expected_leak_kg_s_nozzle"] = leaks.get(r["leak"], {}).get("v4_expected_leak_kg_s_nozzle")
        nominal = min(rm.get("V2", []), key=lambda r: abs(r["demand_multiplier"] - 1.0), default=None)
        res = {"V2": v2(rm, pts, m["sensor_map"]), "V3": v3(rm, pts, dec), "V4": v4(rm, dec, nominal), "V6": v6(rm), "V8": v8(rm, dec)}
        rep["models"][name] = {k: {"status": v[0], "detail": v[1]} for k, v in res.items()}
        for k, v in res.items():
            status.setdefault(k, []).append(v[0])
    s5 = dec.get("S5_discretisation") or {}
    status["V5"] = ["NOT_EVALUABLE" if not s5.get("decided") else ("PASS" if (raw.get("V5") or {}).get("status") == "PASS" else "NOT_EVALUABLE")]
    d1s, d1d = d1(build, spec)
    status["D1"] = [d1s]
    rep["D1"] = d1d
    rep["gates"] = {k: ("PASS" if v and all(x == "PASS" for x in v) else ("FAIL" if "FAIL" in v else "NOT_EVALUABLE")) for k, v in status.items()}
    rep["overall"] = "PASS" if all(rep["gates"].get(k) == "PASS" for k in ("V2", "V3", "V4", "V5", "V6", "V8", "D1")) else "NOT_PASSED"
    out = run / "validation" / "VALIDATION_REPORT.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    return rep


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--run", type=Path, default=gates.RUN)
    a.add_argument("--decisions", type=Path, default=gates.DECISIONS)
    args = a.parse_args(argv)
    r = evaluate(args.run, args.decisions)
    print(f"VALIDATION overall: {r['overall']}  " + ", ".join(f"{k}={v}" for k, v in r["gates"].items()))
    return 0 if r["overall"] == "PASS" else 3


if __name__ == "__main__":
    sys.exit(main())
