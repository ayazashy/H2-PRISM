#!/usr/bin/env python3
"""
Dataset and experimental-design source tables for figure group A (A5/A13; data from Y-tasks).

READ-ONLY and STRUCTURAL: reads the pinned manifest v0.2, the pinned LOTO folds and the eligible window
table built by the primary runner's own feature builder (no model fitting, no labels beyond the run
classes, no outer-test scoring). Every table is a count or a quantile of window start times.

Outputs (default 03_results/dataset_design/):
  class_distribution.csv   class x topology: runs, families, windows (plus topology = ALL)
  inclusion_exclusion.csv  eligible and excluded runs by reason
  loto_folds.csv           outer fold x topology: role, runs, families
  window_timing.csv        per class: window-start quantiles (s)
  provenance.json          config / manifest / folds / feature-table hashes, git commit, artifact_class

Usage:
  python tools/reporting/build_dataset_design_tables.py --config 06_audit_preparation/FINAL_EXPERIMENT_CONFIG.yaml --out 03_results/dataset_design
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from h2prism.experiments import primary_protocol as pp  # noqa: E402


def _write(df: pd.DataFrame, p: Path) -> None:
    p.write_bytes(df.to_csv(index=False, lineterminator="\n", float_format="%.6g").encode("utf-8"))


def build(config: Path, root: Path, raw_parent: Path, out: Path) -> dict:
    cfg = yaml.safe_load(Path(config).read_text(encoding="utf-8"))
    status = pp.SYNTH_STATUS if cfg.get("status") == pp.SYNTH_STATUS else pp.REAL_STATUS
    real = cfg["dataset"]["realization_primary"]
    pre = pp.preflight(cfg, root, raw_parent, real, status)  # fail closed on any hash/schema/fold problem
    man = pd.read_csv(root / cfg["dataset"]["manifest"]["file"])
    fam = cfg["dataset"].get("family_column", "Scenario_Family_ID")
    el = man[man.eligible_primary.astype(bool)]
    ft, fsum = pp.build_features(cfg, root, raw_parent, real)
    out.mkdir(parents=True, exist_ok=True)

    wins = ft.groupby(["label_mapped", "topology"]).size().rename("n_windows")
    runs = el.groupby(["label_mapped", "topology"]).agg(n_runs=("Scenario_ID", "nunique"), n_families=(fam, "nunique"))
    cd = runs.join(wins).reset_index().rename(columns={"label_mapped": "class"})
    tot = el.groupby("label_mapped").agg(n_runs=("Scenario_ID", "nunique"), n_families=(fam, "nunique")).join(
        ft.groupby("label_mapped").size().rename("n_windows")).reset_index().rename(columns={"label_mapped": "class"}).assign(topology="ALL")
    order = {c: i for i, c in enumerate(cfg["dataset"]["classes"])}
    cd = pd.concat([cd, tot], ignore_index=True)[["class", "topology", "n_runs", "n_families", "n_windows"]]
    cd = cd.sort_values(["topology", "class"], key=lambda s: s.map(order) if s.name == "class" else s, kind="mergesort")
    _write(cd, out / "class_distribution.csv")

    ex = man[~man.eligible_primary.astype(bool)].groupby("exclusion_reason").Scenario_ID.nunique().rename("n_runs").reset_index()
    ie = pd.concat([pd.DataFrame([{"category": "eligible (primary 4-class task)", "n_runs": len(el)}]),
                    ex.rename(columns={"exclusion_reason": "category"}).assign(category=lambda d: "excluded: " + d.category)],
                   ignore_index=True)
    _write(ie, out / "inclusion_exclusion.csv")

    folds = pd.read_csv(root / cfg["splits"]["outer"]["file"])
    f2 = folds.merge(el[["Scenario_ID", "topology", fam]].rename(columns={fam: "_fam"}), on="Scenario_ID", suffixes=("_f", ""))
    lf = (f2.groupby(["outer_fold_id", "topology", "split_role"]).agg(n_runs=("Scenario_ID", "nunique"), n_families=("_fam", "nunique"))
          .reset_index().sort_values(["outer_fold_id", "topology"]))
    _write(lf, out / "loto_folds.csv")

    q = ft.groupby("label_mapped").start_time.describe(percentiles=[0.25, 0.5, 0.75])
    wt = pd.DataFrame({"class": q.index, "n_windows": q["count"].astype(int), "min_s": q["min"], "q25_s": q["25%"],
                       "median_s": q["50%"], "q75_s": q["75%"], "max_s": q["max"]})
    wt = wt.sort_values("class", key=lambda s: s.map(order))
    _write(wt, out / "window_timing.csv")

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        commit = "UNKNOWN"
    prov = {"artifact_class": "DATASET_DESCRIPTIVE" if status == pp.REAL_STATUS else "SYNTHETIC_TEST",
            "run_id": f"dataset_design_{fsum['feature_table_sha256'][:12]}", "status": "COMPLETED",
            "config_sha256": pp.sha256_file(Path(config)), "realization": real,
            "input_sha256": {"manifest": cfg["dataset"]["manifest"]["sha256"], "outer_folds": cfg["splits"]["outer"]["sha256"]},
            "feature_table_sha256": fsum["feature_table_sha256"], "n_windows": fsum["n_windows"],
            "preflight_checks_passed": sum(c["ok"] for c in pre["checks"]), "preflight_checks": len(pre["checks"]),
            "git_commit": commit, "script": "tools/reporting/build_dataset_design_tables.py",
            "note": "structural description only; no model fitting, no outer-test scoring",
            "generated_at_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    (out / "provenance.json").write_bytes((json.dumps(prov, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return prov


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="dataset-design source tables (structural, read-only)")
    ap.add_argument("--config", type=Path, default=REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml")
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--raw-parent", type=Path, default=REPO / "data" / "raw")
    ap.add_argument("--out", type=Path, default=REPO / "03_results" / "dataset_design")
    a = ap.parse_args(argv)
    try:
        p = build(a.config, a.root, a.raw_parent, a.out)
    except pp.PreflightError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({k: p[k] for k in ("artifact_class", "run_id", "n_windows", "preflight_checks_passed")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
