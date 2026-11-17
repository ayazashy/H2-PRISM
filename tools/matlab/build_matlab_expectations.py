#!/usr/bin/env python3
"""
Builds tools/matlab/h2prism_matlab_expectations.json: the pinned values the MATLAB readiness scripts check against.
Every value is derived from an existing, already-committed record (no new facts):
  model hashes        03_results/diagnostics/sensor_correspondence/MODEL_FILES.csv (cross-checked with
                      01_dataset_audit/raw_checksums.sha256)
  sensor mapping      03_results/diagnostics/sensor_correspondence/SENSOR_TRACE.csv (variable, sensor id, block SID)
  parameter interface 06_audit_preparation/simulation/v2_normal_support/generate_v2_normal_support.m header (SIDs)
  released gas        05_documentation/GAS_MODEL_LIMITATION.md (Gas Properties (G) SID 4, gas_spec = 1, R = 0.287)
  pipes               tools/simulation/h2net_v1_envelope_screening.py RELEASED_PIPES (SIDs)
  hydrogen tables     06_audit_preparation/simulation/h2net_v1/properties/OUTPUT_HASHES.sha256
  H2Net v1 grant      06_audit_preparation/simulation/h2net_v1/AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml bound hashes
Usage: python tools/matlab/build_matlab_expectations.py [--check]   (--check: exit 1 if the file is stale)
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "tools" / "matlab" / "h2prism_matlab_expectations.json"
SIM_REL = "data/raw/H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation"
H2 = REPO / "06_audit_preparation" / "simulation" / "h2net_v1"
PARAM_INTERFACE = [  # normal models only (generator header: identical SIDs in the three normal models)
    {"sid": "59", "parameter": "final_value", "meaning": "Pressure Source (G)3 set-point after t = 25 s [MPa]"},
    {"sid": "241", "parameter": "slope", "meaning": "Pressure Source (G)1 differential ramp [MPa/s]"},
    {"sid": "213", "parameter": "restriction_area", "meaning": "withdrawal G3 [m^2]"},
    {"sid": "222", "parameter": "restriction_area", "meaning": "withdrawal G4 [m^2]"},
    {"sid": "312", "parameter": "restriction_area", "meaning": "withdrawal G5 [m^2]"},
    {"sid": "215", "parameter": "restriction_area", "meaning": "withdrawal G6 [m^2]"},
]
PIPE_SIDS = ["47", "48", "49", "106", "107", "108", "221", "309"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build() -> dict:
    mf = list(csv.DictReader(open(REPO / "03_results/diagnostics/sensor_correspondence/MODEL_FILES.csv", encoding="utf-8")))
    raw = {l.split()[1]: l.split()[0] for l in (REPO / "01_dataset_audit/raw_checksums.sha256").read_text(encoding="utf-8").splitlines() if l.strip()}
    trace = list(csv.DictReader(open(REPO / "03_results/diagnostics/sensor_correspondence/SENSOR_TRACE.csv", encoding="utf-8")))
    models = []
    for r in mf:
        rel = f"{SIM_REL}/{r['model_file']}"
        key = "H2-SimNet-Dataset/MATLAB_SIMSCAPE_Simulation/" + r["model_file"]
        if raw.get(key) != r["sha256"]:
            raise SystemExit(f"hash records disagree for {r['model_file']}")
        sensors = [{"variable": t["variable"], "sensor_id": t["sensor_id"], "sid": t["sensor_sid"]}
                   for t in trace if t["scenario_kind"] == r["scenario_kind"] and t["model"] == r["model"]]
        models.append({"kind": r["scenario_kind"], "position": r["model"], "file": rel, "sha256": r["sha256"],
                       "name": Path(r["model_file"]).stem, "sensors": sensors,
                       "parameter_interface": PARAM_INTERFACE if r["scenario_kind"] == "normal" else []})
    pinned = {n: h for h, n in (l.split() for l in (H2 / "properties/OUTPUT_HASHES.sha256").read_text(encoding="utf-8").splitlines() if l.strip())}
    auth = yaml.safe_load((H2 / "AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml").read_text(encoding="utf-8"))
    return {
        "schema": "h2prism_matlab_expectations/0.1",
        "matlab": {"minimum_release": "R2025a", "models_saved_in": "R2025a (25.1.0.2943329)",
                   "required_products": ["MATLAB", "Simulink", "Simscape"], "required_licenses": ["MATLAB", "Simulink", "Simscape"],
                   "required_libraries": ["fl_lib", "nesl_utility", "simulink"]},
        "memory_mb": {"minimum_total": 7000, "minimum_available_to_start": 2500, "minimum_available_between_models": 1500},
        "released_gas": {"block_sid": "4", "block": "Gas Properties (G)", "gas_spec_raw": "1", "expected_R_kJ_per_kgK": 0.287,
                         "source": "05_documentation/GAS_MODEL_LIMITATION.md"},
        "pipe_sids": PIPE_SIDS,
        "models": models,
        "hydrogen_tables": [{"file": f"06_audit_preparation/simulation/h2net_v1/properties/{n}", "sha256": h} for n, h in sorted(pinned.items())],
        "h2net_v1_grant": {"file": "06_audit_preparation/simulation/h2net_v1/AUTH_MODEL_DEVELOPMENT_H2NET_V1_REQUEST.yaml",
                           "status": auth["status"], "scope": auth["scope"],
                           "bound": [auth["specification"], auth["reference_code"]]},
    }


def main(argv) -> int:
    d = build()
    text = json.dumps(d, indent=1) + "\n"
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("expectations: " + ("current" if ok else "STALE"))
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print(f"{len(d['models'])} models, {sum(len(m['sensors']) for m in d['models'])} sensors, {len(d['hydrogen_tables'])} H2 files -> {OUT.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
