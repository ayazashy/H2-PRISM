#!/usr/bin/env python3
"""
Acceptance checks and confirmation sealing for SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION (package v2).
Run after generate_v2_normal_support.m ('run') and postprocess_v2_normal_runs.py.

Integrity (every run): provenance fields (scenario, group, partition, model, solver ode14x, fixed step, scope,
package version), parameters read back from the model equal the design, released-model SHA-256 equals the audited
release, logged sensors = the model's own list from the diagram trace, every file hash equals the provenance, noise
seed equals the design, no *_FAILED.json anywhere.

Physical validity (every run; thresholds FIXED BEFORE EXECUTION from the released clean NORMAL runs, see README):
  P1 grid       Timestamp = 0..19999 s (20,000 rows), all values finite
  P2 pressure   every PS channel within [0.09, 9.5] MPa (gas-property table limit 10 MPa, range check = error)
  P3 withdrawal MFS1 and MFS3 > 0 for t >= 1000 s (outflow direction of the released NORMAL runs)
  P4 drift      max |slope of consecutive 60 s means| over 1000-19000 s <= 7.5e-4 MPa/s (PS), 2.75e-3 kg/s per s (MFS)
                (5 x the released maximum 1.5e-4 / 5.5e-4; the design doubles the ramp rate at most)
  P5 oscillation max |60 s mean - centred 11-window mean| over 1000-19000 s <= 0.053 MPa (PS), 0.163 kg/s (MFS)
                (5 x the released maximum 0.0106 / 0.0325)
  P6 noise      development only: SD(noise_added - clean) within 5 % of the specified sigma per channel

Confirmation partition: signals are read only to evaluate P1-P5 and the result is recorded as PASS/FAIL per check;
no value, statistic or plot of confirmation data is written or printed. Its files are then hashed into
CONFIRMATION_PARTITION.sha256 (with an aggregate hash). Nothing is sealed if any check fails.
Writes <out_dir>/VALIDATION_REPORT.json, CONFIRMATION_PARTITION.sha256, DEVELOPMENT_MANIFEST.csv.
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
DESIGN = REPO / "06_audit_preparation" / "simulation" / "v2_normal_support" / "DESIGN.csv"
MODEL_FILES = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "MODEL_FILES.csv"
TRACE = REPO / "03_results" / "diagnostics" / "sensor_correspondence" / "SENSOR_TRACE.csv"
MANIFEST = REPO / "06_audit_preparation" / "protocol2" / "CANDIDATE_MANIFEST_V03.csv"
SCOPE = "SIMULATION_GENERATION:V2_NORMAL_SUPPORT_DEV_AND_CONFIRMATION"
PACKAGE = "v2"
SIGMA = {"PS": 0.0005, "MFS": 0.25}
LIMITS = {"p_min": 0.09, "p_max": 9.5, "drift_ps": 7.5e-4, "drift_mfs": 2.75e-3, "osc_ps": 0.053, "osc_mfs": 0.163,
          "steady": (1000, 19000), "noise_rel_tol": 0.05}
FILES = ("clean_solver_grid.csv", "clean.csv", "noise_added.csv", "provenance.json")


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


def expected_columns(logged):
    key = lambda s: (not s.startswith("pressure"), int(s.rsplit("sensor", 1)[1]))  # noqa: E731
    return ["Timestamp"] + [("PS" if v.startswith("pressure") else "MFS") + v.rsplit("sensor", 1)[1]
                            for v in sorted(logged, key=key)]


def physical_checks(df: pd.DataFrame) -> dict:
    """P1-P5 as booleans plus the measured values (values are reported for development runs only)."""
    L = LIMITS
    ps = [c for c in df.columns if c.startswith("PS")]
    mf = [c for c in df.columns if c.startswith("MFS")]
    t = df.Timestamp.to_numpy(float)
    vals = {"grid_ok": bool(len(df) == 20000 and np.array_equal(t, np.arange(20000.0))),
            "finite": bool(np.isfinite(df.to_numpy(float)).all())}
    vals["p_min"], vals["p_max"] = float(df[ps].min().min()), float(df[ps].max().max())
    late = df[df.Timestamp >= 1000]
    vals["withdrawal_min"] = float(late[["MFS1", "MFS3"]].min().min()) if {"MFS1", "MFS3"} <= set(df.columns) else np.nan
    st = df[(df.Timestamp >= L["steady"][0]) & (df.Timestamp < L["steady"][1])]
    w = st.groupby((st.Timestamp // 60).astype(int)).mean()
    slope = w.diff().abs() / 60
    osc = (w - w.rolling(11, center=True).mean()).abs()
    vals.update({"drift_ps": float(slope[ps].max().max()), "drift_mfs": float(slope[mf].max().max()),
                 "osc_ps": float(osc[ps].max().max()), "osc_mfs": float(osc[mf].max().max())})
    checks = {"P1_grid": vals["grid_ok"] and vals["finite"],
              "P2_pressure": L["p_min"] <= vals["p_min"] and vals["p_max"] <= L["p_max"],
              "P3_withdrawal": bool(vals["withdrawal_min"] > 0),
              "P4_drift": vals["drift_ps"] <= L["drift_ps"] and vals["drift_mfs"] <= L["drift_mfs"],
              "P5_oscillation": vals["osc_ps"] <= L["osc_ps"] and vals["osc_mfs"] <= L["osc_mfs"]}
    return checks, vals


def check(out_dir: Path, design: Path) -> dict:
    D = pd.read_csv(design)
    rel, logged = released_hashes(), expected_logged()
    existing_groups = set(pd.read_csv(MANIFEST).independence_group)
    problems, dev_rows, seal, runs = [], [], [], []
    failed = sorted(out_dir.rglob("*_FAILED.json"))
    if failed:
        problems.append(f"{len(failed)} failed run record(s) present: follow the failure procedure")
    clash = set(D.independence_group) & existing_groups
    if clash:
        problems.append(f"new independence groups collide with existing ones: {sorted(clash)}")
    for r in D.itertuples():
        base = out_dir / r.partition / f"{r.scenario_id}_{r.model}"
        tag = base.name
        files = {k: Path(f"{base}_{k}") for k in FILES}
        missing = [k for k, p in files.items() if not p.exists()]
        if missing:
            problems.append(f"{tag}: missing {missing}")
            continue
        pv = json.loads(files["provenance.json"].read_text(encoding="utf-8"))
        exp = {"scenario_id": r.scenario_id, "independence_group": r.independence_group, "partition": r.partition,
               "model": r.model, "model_name": r.model_name, "authorization_scope": SCOPE, "solver": "ode14x",
               "package_version": PACKAGE}
        for k, v in exp.items():
            if str(pv.get(k)) != str(v):
                problems.append(f"{tag}: provenance {k}={pv.get(k)!r}, expected {v!r}")
        if pv.get("released_model_sha256") != rel.get(r.model):
            problems.append(f"{tag}: released model hash differs from the audited release")
        for k in ("ps_step_final_value_MPa", "ps_ramp_slope_MPa_per_s"):
            if not np.isclose(float(pv.get(k, np.nan)), getattr(r, k), rtol=1e-9, atol=1e-15):
                problems.append(f"{tag}: {k} read back {pv.get(k)}, design {getattr(r, k)}")
        areas = np.asarray(pv.get("withdrawal_restriction_area_m2", []), float)
        if areas.shape != (4,) or not np.allclose(areas, r.withdrawal_restriction_area_m2, rtol=1e-9):
            problems.append(f"{tag}: withdrawal areas {areas.tolist()} != {r.withdrawal_restriction_area_m2}")
        if not np.isclose(float(pv.get("fixed_step_s", np.nan)), r.fixed_step_s):
            problems.append(f"{tag}: fixed step {pv.get('fixed_step_s')} != {r.fixed_step_s}")
        if sorted(pv.get("logged_variables", [])) != logged[r.model]:
            problems.append(f"{tag}: logged sensors differ from the model's own list")
        for k, key in (("clean_solver_grid.csv", "clean_solver_grid_csv_sha256"), ("clean.csv", "clean_csv_sha256"),
                       ("noise_added.csv", "noise_added_csv_sha256")):
            if pv.get(key) != _sha(files[k]):
                problems.append(f"{tag}: {k} hash differs from provenance")
        if int(pv.get("noise", {}).get("seed", -1)) != int(r.noise_seed):
            problems.append(f"{tag}: noise seed differs from design")
        try:
            clean = pd.read_csv(files["clean.csv"])
            if list(clean.columns) != expected_columns(logged[r.model]):
                problems.append(f"{tag}: clean columns differ from the model's own sensor list")
            chk, vals = physical_checks(clean)
        except Exception as e:  # unreadable or malformed file
            problems.append(f"{tag}: clean file not usable ({type(e).__name__})")
            continue
        bad = [k for k, ok in chk.items() if not ok]
        if bad:
            problems.append(f"{tag}: physical checks failed {bad}")
        if r.partition == "confirmation":
            runs.append({"run": tag, "partition": "confirmation", **chk})          # PASS/FAIL only, no values
            seal += [(_sha(files[k]), f"{r.partition}/{tag}_{k}") for k in FILES]
            continue
        noisy = pd.read_csv(files["noise_added.csv"])
        for c in clean.columns[1:]:
            sd = float((noisy[c] - clean[c]).std())
            s0 = SIGMA["MFS" if c.startswith("MFS") else "PS"]
            if abs(sd / s0 - 1) > LIMITS["noise_rel_tol"]:
                problems.append(f"{tag}: noise SD on {c} is {sd:.3g}, specified {s0}")
        runs.append({"run": tag, "partition": "development", **chk, **{f"value_{k}": v for k, v in vals.items()}})
        dev_rows.append({"Scenario_ID": f"{r.scenario_id}_{r.model.upper()}", "independence_group": r.independence_group,
                         "label_mapped": "NORMAL", "topology_source_model": r.model, "partition": r.partition,
                         "file_clean": f"{r.partition}/{tag}_clean.csv", "sha256_clean": pv["clean_csv_sha256"],
                         "file_noise_added": f"{r.partition}/{tag}_noise_added.csv",
                         "sha256_noise_added": pv["noise_added_csv_sha256"]})
    return {"problems": problems, "dev_rows": dev_rows, "seal": seal, "runs": runs}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--design", type=Path, default=DESIGN)
    a = ap.parse_args(argv)
    from v2_normal_authorization import require_active
    require_active()                     # fail closed: no active, hash-bound authorization -> nothing is accepted
    res = check(a.out_dir, a.design)
    ok = not res["problems"]
    report = {"scope": SCOPE, "package_version": PACKAGE, "design_sha256": _sha(a.design), "limits": LIMITS,
              "status": "ACCEPTED_AND_SEALED" if ok else "REJECTED_NOT_SEALED", "n_problems": len(res["problems"]),
              "problems": res["problems"], "runs": res["runs"], "n_development_runs": len(res["dev_rows"]),
              "n_confirmation_files_sealed": len(res["seal"]) if ok else 0}
    if ok:
        lines = [f"{h}  {p}" for h, p in sorted(res["seal"], key=lambda x: x[1])]
        agg = hashlib.sha256("\n".join(lines).encode()).hexdigest()
        (a.out_dir / "CONFIRMATION_PARTITION.sha256").write_text("\n".join(lines) + f"\n# aggregate {agg}\n", encoding="utf-8")
        report["confirmation_aggregate_sha256"] = agg
        pd.DataFrame(res["dev_rows"]).to_csv(a.out_dir / "DEVELOPMENT_MANIFEST.csv", index=False, lineterminator="\n")
    (a.out_dir / "VALIDATION_REPORT.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"{report['status']}: {report['n_problems']} problem(s)")
    for p in res["problems"]:
        print(" -", p)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
