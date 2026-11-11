#!/usr/bin/env python3
"""
Collect the primary RQ1 contrast (s_C vs s_C-D, rank-matched PA-1) from every recorded analysis run into one
table for figure E1. Read-only: values are copied from each run's rq1.csv, never recomputed.

Sources (under --runs, default 03_results/primary_protocol/):
  PRIMARY/                      analysis = primary; plus its embedded warning-only variant (policy_warning_only)
  ROBUSTNESS_clean/             analysis = clean_realization (if run via --execute-robustness)
  SENSITIVITY_<name>/           analysis = <name>
Only COMPLETED runs whose artifact_class is a real execution class are accepted (synthetic runs refused unless
--allow-synthetic, used by tests writing outside 03_results/). Missing analyses are listed as NOT_RUN.

Usage:
  python tools/reporting/build_sensitivity_summary.py --runs 03_results/primary_protocol --out 03_results/primary_protocol/SENSITIVITY_SUMMARY
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
REAL = {"PRIMARY_EXPERIMENT", "ROBUSTNESS_EXPERIMENT", "SENSITIVITY_EXPERIMENT"}
REGISTERED = ["clean_realization", "windows_60_60", "pre_event_label_normal", "offset_invariant_features", "k_10", "k_50",
              "prior_correction", "extended_family_map", "policy_warning_only"]
POPULATION = {  # what each analysis evaluates relative to the primary population (for honest comparison)
    "primary": "same windows (primary population)",
    "policy_warning_only": "same windows; different policy",
    "clean_realization": "same windows; clean realization of the same runs",
    "k_10": "same windows; D(x) k=10", "k_50": "same windows; D(x) k=50",
    "prior_correction": "same windows; prior-corrected D(x)",
    "offset_invariant_features": "same windows; 80 offset-invariant features",
    "extended_family_map": "same windows; different independence units (32 families)",
    "windows_60_60": "different population: non-overlapping 60 s windows",
    "pre_event_label_normal": "different population: pre-event windows added as NORMAL",
}
COLS = ["analysis", "population_note", "target", "status", "realized_coverage_a", "realized_coverage_b", "difference", "ci_low", "ci_high", "n_units",
        "run_id", "artifact_class", "source_file", "source_sha256"]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def collect(runs: Path, allow_synthetic: bool = False, include=None) -> pd.DataFrame:
    """include: optional set of run directory names (e.g. the runs that passed validation); others are skipped."""
    rows = []
    found = {}
    attempted = {}  # analysis -> run_key of a recorded run that did not complete or did not pass validation
    for d in sorted(p for p in runs.iterdir() if p.is_dir()):
        if d.name == "PRIMARY":
            names = [("primary", "primary"), ("policy_warning_only", "warning_only")]
        elif d.name == "ROBUSTNESS_clean":
            names = [("clean_realization", "primary")]
        elif d.name.startswith("SENSITIVITY_") and d.name != "SENSITIVITY_SUMMARY":
            names = [(d.name[len("SENSITIVITY_"):], "primary")]
        else:
            continue
        man = d / "run_manifest.json"
        rq1 = d / "rq1.csv"
        m = json.loads(man.read_text(encoding="utf-8")) if man.exists() else {}
        if (include is not None and d.name not in include) or not rq1.exists() or m.get("status") != "COMPLETED":
            if m:  # executed but incomplete / invalid: never reported as NOT_RUN
                for analysis, _ in names:
                    attempted[analysis] = m.get("run_key")
            continue
        if m.get("artifact_class") not in REAL and not allow_synthetic:
            raise ValueError(f"{d.name}: artifact_class {m.get('artifact_class')} is not a real execution class")
        r = pd.read_csv(rq1)
        for analysis, variant in names:
            sel = r[(r.variant == variant) & (r["mode"] == "rank_matched") & (r.comparison_b == "s_C_minus_D")]
            for _, x in sel.iterrows():
                rows.append({**{c: x.get(c) for c in ("target", "status", "realized_coverage_a", "realized_coverage_b", "difference",
                                                      "ci_low", "ci_high", "n_units")},
                             "analysis": analysis, "run_id": m.get("run_key"), "artifact_class": m.get("artifact_class"),
                             "source_file": rq1.relative_to(runs).as_posix(), "source_sha256": _sha(rq1)})
            found[analysis] = True
    for a in ["primary"] + REGISTERED:
        if a not in found:
            rows.append({"analysis": a, "status": "RUN_INCOMPLETE" if a in attempted else "NOT_RUN",
                         "run_id": attempted.get(a)})
    out = pd.DataFrame(rows)
    out["population_note"] = out["analysis"].map(POPULATION)
    return out.reindex(columns=COLS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=REPO / "03_results" / "primary_protocol")
    ap.add_argument("--out", type=Path, default=REPO / "03_results" / "primary_protocol" / "SENSITIVITY_SUMMARY")
    ap.add_argument("--allow-synthetic", action="store_true")
    a = ap.parse_args(argv)
    if not a.runs.exists():
        print(f"REFUSED: no recorded runs under {a.runs}", file=sys.stderr)
        return 2
    df = collect(a.runs, a.allow_synthetic)
    a.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out / "sensitivity_summary.csv", index=False, lineterminator="\n", float_format="%.10g")
    prim = df[(df.analysis == "primary") & df.run_id.notna()]
    prov = {"artifact_class": "SENSITIVITY_SUMMARY" if not a.allow_synthetic else "SYNTHETIC_TEST", "status": "COMPLETED",
            "run_key": "sensitivity_summary", "config_sha256": "see source run manifests",
            "sources": sorted(set(df.source_file.dropna())), "primary_run_id": prim.run_id.iloc[0] if len(prim) else None,
            "script": "tools/reporting/build_sensitivity_summary.py"}
    (a.out / "run_manifest.json").write_text(json.dumps(prov, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(df.groupby("status").size().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
