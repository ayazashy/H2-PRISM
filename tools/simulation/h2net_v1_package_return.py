#!/usr/bin/env python3
"""
Package the ACTUAL outputs of an H2Net v1 execution for return to Ahmed (handoff step 05). Collects only what exists;
missing stages are reported, never filled in. Excludes credentials, licence files, caches and MATLAB autosaves.
Output: h2net_v1_run/return/H2NET_V1_RETURN_<UTC timestamp>.zip containing RETURN_STATUS.json and SHA256SUMS.txt.
Usage: python tools/simulation/h2net_v1_package_return.py [--run DIR] [--no-dataset]
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import h2net_v1_gates as gates  # noqa: E402

REPO = gates.REPO
EXCLUDE = ["*.lic", "*license*", "*password*", "*secret*", "*token*", "*.asv", "*.autosave", "*.slxc", "*/slprj/*", "*/return/*",
           "*__pycache__*", "*.mat"]
DECISION_FILES = ["PARAMETER_DECISIONS.yaml", "EXECUTOR_DESIGNATION.yaml", "AUTH_H2NET_V1_V7.yaml", "AUTH_H2NET_V1_DATASET.yaml",
                  "AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def status(run: Path) -> dict:
    s = {}
    pf = _json(run / "preflight" / "PREFLIGHT.json")
    s["preflight"] = pf.get("overall", "UNKNOWN") if pf else "MISSING"
    r = subprocess.run([sys.executable, str(REPO / "tools/matlab/check_matlab_reports.py"), str(run / "readiness")], capture_output=True, text=True)
    s["R0_readiness"] = "PASS" if r.returncode == 0 else ("MISSING" if not (run / "readiness").exists() else "FAIL")
    t = _json(run / "targets" / "V2_TARGETS.json")
    s["V2_targets"] = "COMPUTED" if t else "MISSING"
    b = _json(run / "build" / "BUILD_REPORT.json")
    s["build"] = b.get("status") if b else "MISSING"
    v = _json(run / "validation" / "VALIDATION_REPORT.json")
    s["validation"] = v.get("overall") if v else "MISSING"
    s["validation_gates"] = v.get("gates") if v else {}
    man = run / "dataset" / "RUN_MANIFEST.jsonl"
    if man.exists():
        recs = [json.loads(l) for l in man.read_text(encoding="utf-8").splitlines() if l.strip()]
        plan = _json(run / "scenarios" / "SCENARIO_PLAN.json") or {"runs": []}
        s["dataset"] = {"planned": len(plan["runs"]), "completed": sum(r["status"] == "COMPLETED" for r in recs),
                        "failed": sum(r["status"] == "FAILED" for r in recs), "stopped": [r for r in recs if r["status"].startswith("STOPPED")]}
    else:
        s["dataset"] = "NOT_RUN"
    order = ["preflight", "R0_readiness", "V2_targets", "build", "validation"]
    ok = {"preflight": "PASS", "R0_readiness": "PASS", "V2_targets": "COMPUTED", "build": "COMPLETE", "validation": "PASS"}
    s["missing_or_failed_stages"] = [k for k in order if s[k] != ok[k]]
    s["overall"] = "PASS" if not s["missing_or_failed_stages"] else "INCOMPLETE"
    return s


def collect(run: Path, with_dataset: bool):
    files = []
    for name in DECISION_FILES:
        p = gates.H2 / name
        if p.exists():
            files.append((p, f"decisions/{name}"))
    if run.exists():
        for p in sorted(run.rglob("*")):
            rel = p.relative_to(run).as_posix()
            if not p.is_file() or any(fnmatch.fnmatch(rel.lower(), pat) or fnmatch.fnmatch("/" + rel.lower(), pat) for pat in EXCLUDE):
                continue
            if not with_dataset and rel.startswith("dataset/") and rel.endswith(".csv"):
                continue
            files.append((p, f"run/{rel}"))
    return files


def package(run: Path, with_dataset: bool = True) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = run / "return" / f"H2NET_V1_RETURN_{stamp}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = collect(run, with_dataset)
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    except OSError:
        head = "unknown"
    st = status(run)
    st.update({"created_utc": stamp, "repository_commit": head, "files": len(files),
               "reproduce": "handoff/h2net_v1/START_HERE.md, steps 01-05, with the decision record in decisions/"})
    sums = [f"{_sha(p)}  {arc}" for p, arc in files]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p, arc in files:
            z.write(p, arc)
        z.writestr("RETURN_STATUS.json", json.dumps(st, indent=1, default=str) + "\n")
        z.writestr("SHA256SUMS.txt", "\n".join(sums) + "\n")
    (out.with_suffix(".zip.sha256")).write_text(f"{_sha(out)}  {out.name}\n", encoding="utf-8")
    return out


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--run", type=Path, default=gates.RUN)
    a.add_argument("--no-dataset", action="store_true")
    args = a.parse_args(argv)
    out = package(args.run, not args.no_dataset)
    st = json.loads(zipfile.ZipFile(out).read("RETURN_STATUS.json"))
    print(f"{out}\noverall: {st['overall']}; missing or failed: {st['missing_or_failed_stages']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
