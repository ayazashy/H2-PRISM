#!/usr/bin/env python3
"""
Independent PASS/FAIL evaluation of the MATLAB readiness reports (does not trust the reports' own 'overall' field).
  python tools/matlab/check_matlab_reports.py <report_dir>        exit 0 = READY_FOR_AUTHORIZED_STEPS, 1 = NOT_READY

Criteria (all required):
  ENVIRONMENT_REPORT.json   E1 release >= R2025a; E2.* products; E3.* licences; E4 memory not FAIL; E5 no pool;
                            E6 Python; E7.* all six released models present with pinned hashes; E8.* hydrogen files and
                            E8.S parameter struct; E9.* H2Net v1 grant-bound files; E10.* libraries load
  SMOKE_REPORT.json         for each of the six models: .1 hash, .2 load copy, .3 no unresolved links, .5 gas
                            specification as recorded in GAS_MODEL_LIMITATION.md, .6 sensor SIDs, .7 output schema,
                            .8 parameter interface (normal models), .9 update diagram, .10 released file unchanged;
                            no memory-guard stop
  H2_INTEGRATION_REPORT     I1 grant-bound files, I3 parameter-file hash, I4 dialog parameters, I5 real-gas option
WARN (callbacks, memory total) is reported but does not fail. A PASS means software/load/compile/interface readiness,
NOT physical validation, and it does NOT open the H2Net v1 build gate (PARAMETER_DECISIONS.yaml).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

N_MODELS = 6
ENV_PREFIXES = ("E1", "E2.", "E3.", "E5", "E6", "E7.", "E8.", "E9.", "E10.")
SMOKE_SUFFIXES = (".1", ".2", ".3", ".5", ".6", ".7", ".8", ".9", ".10")
INTEGRATION_IDS = ("I1", "I3", "I4", "I5")


def _load(d: Path, name: str):
    p = d / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _checks(rep):
    c = rep.get("checks", [])
    return [c] if isinstance(c, dict) else c


def evaluate(d: Path) -> dict:
    problems, notes = [], []
    env = _load(d, "ENVIRONMENT_REPORT.json")
    if env is None:
        problems.append("ENVIRONMENT_REPORT.json missing")
    else:
        cs = _checks(env)
        for c in cs:
            if c["id"].startswith(ENV_PREFIXES) and c["status"] != "PASS":
                problems.append(f"env {c['id']} {c['name']}: {c['status']} ({c['detail']})")
            if c["id"] == "E4" and c["status"] == "FAIL":
                problems.append(f"env E4 memory: {c['detail']}")
            if c["status"] == "WARN":
                notes.append(f"env {c['id']} WARN: {c['detail']}")
        if sum(c["id"].startswith("E7.") for c in cs) != N_MODELS:
            problems.append("env: not all six released models were checked")
        for pre in ("E1", "E2.", "E3.", "E8.S", "E9.", "E10."):
            if not any(c["id"].startswith(pre) for c in cs):
                problems.append(f"env: check {pre} absent")
    sm = _load(d, "SMOKE_REPORT.json")
    if sm is None:
        problems.append("SMOKE_REPORT.json missing")
    else:
        cs = {c["id"]: c for c in _checks(sm)}
        if (sm.get("extra") or {}).get("stopped"):
            problems.append(f"smoke stopped: {sm['extra']['stopped']}")
        for k in range(1, N_MODELS + 1):
            for suf in SMOKE_SUFFIXES:
                c = cs.get(f"M{k}{suf}")
                if c is None:
                    problems.append(f"smoke M{k}{suf} absent")
                elif c["status"] == "SKIP" and suf == ".8" and "anomalous" in c["detail"]:
                    continue
                elif c["status"] != "PASS":
                    problems.append(f"smoke M{k}{suf} {c['name']}: {c['status']} ({c['detail']})")
            gas = cs.get(f"M{k}.5")
            if gas:
                notes.append(f"M{k} gas: {gas['detail']}")
    it = _load(d, "H2_INTEGRATION_REPORT.json")
    if it is None:
        problems.append("H2_INTEGRATION_REPORT.json missing")
    else:
        cs = {c["id"]: c for c in _checks(it)}
        for i in INTEGRATION_IDS:
            c = cs.get(i)
            if c is None or c["status"] != "PASS":
                problems.append(f"integration {i}: {'absent' if c is None else c['status'] + ' (' + c['detail'] + ')'}")
        notes.append(f"H2Net v1 build gate: {(it.get('extra') or {}).get('build_gate', 'UNKNOWN')}")
    return {"verdict": "READY_FOR_AUTHORIZED_STEPS" if not problems else "NOT_READY", "problems": problems, "notes": notes}


def main(argv) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    r = evaluate(Path(argv[0]))
    print(r["verdict"] + "  (software readiness only; not physical validation; build gate unchanged)")
    for p in r["problems"]:
        print("  FAIL  " + p)
    for n in r["notes"]:
        print("  note  " + n)
    return 0 if not r["problems"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
