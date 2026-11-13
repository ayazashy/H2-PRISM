#!/usr/bin/env python3
"""
Acceptance checks and confirmation sealing for SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION.

Run after generate_v2_normal_support.m and add_measurement_noise.py. For every DESIGN.csv row it checks the provenance
(scenario, model, partition, parameters read back from the model, released-model SHA-256, solver, fixed step,
authorization scope, file hashes, logged sensor list = the model's own list from the diagram trace).
  development partition: the signal files are also read (columns, finite values, strictly increasing time);
  confirmation partition: signal files are NEVER read -- only hashed -- and the hashes are sealed in
                          CONFIRMATION_PARTITION.sha256 (with an aggregate hash) before anyone analyses anything.
New independence groups must not collide with the 13 existing groups of manifest v0.3.
Writes <out_dir>/VALIDATION_REPORT.json, <out_dir>/CONFIRMATION_PARTITION.sha256, <out_dir>/DEVELOPMENT_MANIFEST.csv.
Exit code 1 if any check fails (nothing is sealed then).
Usage: python tools/simulation/validate_v2_normal_outputs.py <out_dir> [--design DESIGN.csv]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DESIGN = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support" / "DESIGN.csv"
MODEL_FILES = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "MODEL_FILES.csv"
TRACE = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "SENSOR_TRACE.csv"
MANIFEST = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv"
SCOPE = "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"
PARAMS = ("ps_step_final_value_MPa", "ps_ramp_slope_MPa_per_s")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def expected_logged() -> dict:
    t = pd.read_csv(TRACE)
    t = t[t.scenario_kind == "normal"]
    return {m: sorted(g.variable) for m, g in t.groupby("model")}


def released_hashes() -> dict:
    f = pd.read_csv(MODEL_FILES)
    f = f[f.scenario_kind == "normal"]
    return dict(zip(f.model, f.sha256))


def check(out_dir: Path, design: Path) -> dict:
    D = pd.read_csv(design)
    rel, logged = released_hashes(), expected_logged()
    existing_groups = set(pd.read_csv(MANIFEST).independence_group)
    problems, dev_rows, seal = [], [], []
    clash = set(D.independence_group) & existing_groups
    if clash:
        problems.append(f"new independence groups collide with existing ones: {sorted(clash)}")
    for r in D.itertuples():
        base = out_dir / r.partition / f"{r.scenario_id}_{r.model}"
        files = {k: Path(f"{base}_{k}") for k in ("clean.csv", "noise_added.csv", "provenance.json")}
        missing = [k for k, p in files.items() if not p.exists()]
        if missing:
            problems.append(f"{base.name}: missing {missing}")
            continue
        pv = json.loads(files["provenance.json"].read_text(encoding="utf-8"))
        tag = base.name
        exp = {"scenario_id": r.scenario_id, "independence_group": r.independence_group, "partition": r.partition,
               "model": r.model, "model_name": r.model_name, "authorization_scope": SCOPE, "solver": "ode14x"}
        for k, v in exp.items():
            if str(pv.get(k)) != str(v):
                problems.append(f"{tag}: provenance {k}={pv.get(k)!r}, expected {v!r}")
        if pv.get("released_model_sha256") != rel.get(r.model):
            problems.append(f"{tag}: released model hash differs from the audited release")
        for k in PARAMS:
            if not np.isclose(float(pv.get(k, np.nan)), getattr(r, k), rtol=1e-9, atol=1e-15):
                problems.append(f"{tag}: {k} read back {pv.get(k)}, design {getattr(r, k)}")
        areas = np.asarray(pv.get("withdrawal_restriction_area_m2", []), float)
        if areas.shape != (4,) or not np.allclose(areas, r.withdrawal_restriction_area_m2, rtol=1e-9):
            problems.append(f"{tag}: withdrawal areas {areas.tolist()} != {r.withdrawal_restriction_area_m2}")
        if not np.isclose(float(pv.get("fixed_step_s", np.nan)), r.fixed_step_s):
            problems.append(f"{tag}: fixed step {pv.get('fixed_step_s')} != {r.fixed_step_s}")
        if sorted(pv.get("logged_variables", [])) != logged[r.model]:
            problems.append(f"{tag}: logged sensors differ from the model's own list")
        if pv.get("clean_csv_sha256") != _sha(files["clean.csv"]) or pv.get("noise_added_csv_sha256") != _sha(files["noise_added.csv"]):
            problems.append(f"{tag}: file hash differs from provenance")
        if int(pv.get("noise", {}).get("seed", -1)) != int(r.noise_seed):
            problems.append(f"{tag}: noise seed differs from design")
        if r.partition == "confirmation":
            seal += [(_sha(files[k]), f"{r.partition}/{base.name}_{k}") for k in files]   # hashed, never read
            continue
        for k in ("clean.csv", "noise_added.csv"):
            df = pd.read_csv(files[k])
            want = ["Timestamp"] + [("PS" if v.startswith("pressure") else "MFS") + v.rsplit("sensor", 1)[1]
                                    for v in sorted(logged[r.model], key=lambda s: (not s.startswith("pressure"),
                                                                                    int(s.rsplit("sensor", 1)[1])))]
            if list(df.columns) != want:
                problems.append(f"{tag}/{k}: columns {list(df.columns)} != {want}")
            if not np.isfinite(df.to_numpy(float)).all():
                problems.append(f"{tag}/{k}: non-finite values")
            if not (np.diff(df.Timestamp.to_numpy(float)) > 0).all():
                problems.append(f"{tag}/{k}: time not strictly increasing")
        dev_rows.append({"Scenario_ID": f"{r.scenario_id}_{r.model.upper()}", "independence_group": r.independence_group,
                         "label_mapped": "NORMAL", "topology_source_model": r.model, "partition": r.partition,
                         "file_clean": f"{r.partition}/{base.name}_clean.csv", "sha256_clean": pv["clean_csv_sha256"],
                         "file_noise_added": f"{r.partition}/{base.name}_noise_added.csv",
                         "sha256_noise_added": pv["noise_added_csv_sha256"]})
    return {"problems": problems, "dev_rows": dev_rows, "seal": seal}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--design", type=Path, default=DESIGN)
    a = ap.parse_args(argv)
    res = check(a.out_dir, a.design)
    report = {"scope": SCOPE, "design_sha256": _sha(a.design), "n_problems": len(res["problems"]),
              "problems": res["problems"], "n_development_runs": len(res["dev_rows"]),
              "n_confirmation_files_sealed": 0 if res["problems"] else len(res["seal"])}
    if not res["problems"]:
        lines = [f"{h}  {p}" for h, p in sorted(res["seal"], key=lambda x: x[1])]
        agg = hashlib.sha256("\n".join(lines).encode()).hexdigest()
        (a.out_dir / "CONFIRMATION_PARTITION.sha256").write_text("\n".join(lines) + f"\n# aggregate {agg}\n", encoding="utf-8")
        report["confirmation_aggregate_sha256"] = agg
        pd.DataFrame(res["dev_rows"]).to_csv(a.out_dir / "DEVELOPMENT_MANIFEST.csv", index=False, lineterminator="\n")
    (a.out_dir / "VALIDATION_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if not res["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
