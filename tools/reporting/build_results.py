#!/usr/bin/env python3
"""
H2-PRISM results lifecycle command (A13/F13): validated runs -> tables -> selected figures -> provenance.

One explicit command (no background jobs). It reuses the existing builders and adds only what was missing:
  1. DISCOVER   run directories under <root>/03_results/primary_protocol/ (PRIMARY, ROBUSTNESS_clean, SENSITIVITY_*)
  2. VALIDATE   each run: COMPLETED status; execution class with a recorded authorization (synthetic only with
                --allow-synthetic); protocol config hash = the pinned FINAL_EXPERIMENT_CONFIG; every aggregate
                table present with the contracted columns; RQ2 shares sum to 1; rank-matched coverage matched;
                unique window ids. Writes 03_results/validation/<run>_<key12>.json (never edits the run).
  3. REGISTER   one row per run in <out-root>/RESULTS_INDEX.csv (a run registry; figure/table provenance stays in
                the builders' FIGURE_MANIFEST / TABLE_MANIFEST).
  4. BUILD      sensitivity summary from VALIDATED runs only, then the registered tables and figures into
                versioned directories <out-root>/{tables,figures}/primary/<run_key12>/. An existing version is
                never overwritten (history preserved); a new PRIMARY run gets a new directory.
Evidence status stays as configured (PENDING -> preliminary/ with watermark) unless a person passes
--evidence-status VALIDATED after PRIMARY_RESULTS_VALIDATION; the config actually used is saved next to the outputs.

Usage:
  python tools/reporting/build_results.py                       # official tree (refuses synthetic / unauthorized runs)
  python tools/reporting/build_results.py --root <tmp> --out-root <tmp>/qa --allow-synthetic   # QA only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_research_figures as brf  # noqa: E402
import build_research_tables as brt  # noqa: E402
import build_sensitivity_summary as bss  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
PINNED_CONFIG = REPO / "06_audit_preparation" / "FINAL_EXPERIMENT_CONFIG.yaml"
CONTRACT = REPO / "configs" / "interface_contracts.yaml"
RESULTS_CFG = REPO / "configs" / "reporting_figures.yaml"
RUN_DIRS = ("PRIMARY", "ROBUSTNESS_clean")


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _contract_tables() -> Dict[str, List[str]]:
    agg = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))["contracts"]["aggregate_outputs"]
    return {k: v for k, v in agg.items() if k.endswith(".csv") and isinstance(v, list) and " " not in k}


def validate_run(d: Path, allow_synthetic: bool, pinned_sha: str) -> Dict:
    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)})
        return bool(ok)

    man_p = d / "run_manifest.json"
    if not chk("run_manifest_present", man_p.exists()):
        return {"run_dir": d.name, "status": "INVALID", "checks": checks}
    m = json.loads(man_p.read_text(encoding="utf-8"))
    cls = m.get("artifact_class")
    chk("status_completed", m.get("status") == "COMPLETED", m.get("status"))
    real = cls in brf.EXPERIMENT_CLASSES
    chk("execution_class", real or (allow_synthetic and cls == "SYNTHETIC_TEST"), cls)
    if real:
        chk("authorization_recorded", bool(m.get("authorization")), "")
        chk("protocol_config_is_pinned", m.get("config_sha256") == pinned_sha, m.get("config_sha256"))
    for name, cols in _contract_tables().items():
        p = d / name
        if chk(f"present:{name}", p.exists()):
            try:
                df = pd.read_csv(p)
            except pd.errors.EmptyDataError:
                df = pd.DataFrame()
            if len(df):  # an empty table (e.g. tie_sensitivity with nothing estimable) is valid
                chk(f"columns:{name}", set(cols) <= set(df.columns), sorted(set(cols) - set(df.columns))[:5])
    if (d / "rq2.csv").exists() and (d / "rq2.csv").stat().st_size > 1:
        r = pd.read_csv(d / "rq2.csv")
        chk("rq2_shares_sum_to_one", ((r.specific + r.ambiguity_set + r.unresolved - 1).abs() < 1e-9).all())
    if (d / "rq1.csv").exists():
        r = pd.read_csv(d / "rq1.csv")
        rm = r[(r["mode"] == "rank_matched") & (r.status == "ESTIMABLE")]
        chk("rank_matched_coverage_matched", (rm.realized_coverage_a == rm.realized_coverage_b).all())
    if (d / "predictions.parquet").exists():
        chk("unique_window_ids", pd.read_parquet(d / "predictions.parquet", columns=["window_id"]).window_id.is_unique)
    ok = all(c["ok"] for c in checks)
    return {"run_dir": d.name, "run_key": m.get("run_key"), "artifact_class": cls, "analysis": (m.get("sensitivity") or {}).get("name", "primary"),
            "config_sha256": m.get("config_sha256"), "effective_config_sha256": m.get("effective_config_sha256"),
            "git_commit": m.get("git_commit"), "status": "VALID" if ok else "INVALID",
            "n_checks": len(checks), "n_failed": sum(not c["ok"] for c in checks), "checks": checks}


def run(root: Path, out_root: Path, allow_synthetic: bool = False, evidence_status: str = None) -> Dict:
    runs = root / "03_results" / "primary_protocol"
    if not runs.exists():
        raise SystemExit(f"REFUSED: no recorded runs under {brf._rel(runs, root)} (no authorized experiment has been executed)")
    official = brf._is_official(out_root)
    if official and allow_synthetic:
        raise SystemExit("REFUSED: --allow-synthetic cannot write into the official results tree")
    pinned = _sha(PINNED_CONFIG)
    dirs = [p for p in sorted(runs.iterdir()) if p.is_dir() and (p.name in RUN_DIRS or (p.name.startswith("SENSITIVITY_") and p.name != "SENSITIVITY_SUMMARY"))]
    vals = [validate_run(d, allow_synthetic, pinned) for d in dirs]
    vdir = out_root / "validation"
    vdir.mkdir(parents=True, exist_ok=True)
    for v in vals:
        (vdir / f"{v['run_dir']}_{str(v.get('run_key'))[:12]}.json").write_text(json.dumps(v, indent=2) + "\n", encoding="utf-8")
    index = pd.DataFrame([{k: v.get(k) for k in ("run_dir", "run_key", "artifact_class", "analysis", "status", "n_checks", "n_failed",
                                                   "config_sha256", "effective_config_sha256", "git_commit")} for v in vals])
    index["validation_file"] = [f"validation/{v['run_dir']}_{str(v.get('run_key'))[:12]}.json" for v in vals]
    index.to_csv(out_root / "RESULTS_INDEX.csv", index=False, lineterminator="\n")
    primary = next((v for v in vals if v["run_dir"] == "PRIMARY"), None)
    if primary is None or primary["status"] != "VALID":
        raise SystemExit("REFUSED: PRIMARY run missing or INVALID; see RESULTS_INDEX.csv / validation/")
    ok_dirs = {v["run_dir"] for v in vals if v["status"] == "VALID"}
    summ = runs / "SENSITIVITY_SUMMARY"
    summ.mkdir(exist_ok=True)
    s = bss.collect(runs, allow_synthetic, include=ok_dirs)
    s.to_csv(summ / "sensitivity_summary.csv", index=False, lineterminator="\n", float_format="%.10g")
    (summ / "run_manifest.json").write_text(json.dumps({"artifact_class": "SYNTHETIC_TEST" if allow_synthetic else "SENSITIVITY_SUMMARY",
                                                          "status": "COMPLETED", "run_key": "sensitivity_summary",
                                                          "config_sha256": "see source run manifests", "sources": sorted(ok_dirs)},
                                                         indent=2) + "\n", encoding="utf-8")
    key = str(primary["run_key"])[:12]
    fig_dir, tab_dir = out_root / "figures" / "primary" / key, out_root / "tables" / "primary" / key
    if fig_dir.exists() or tab_dir.exists():  # history preserved: an existing version is never overwritten
        return {"status": "UNCHANGED", "version": key, "index": index}
    cfg_used = yaml.safe_load(RESULTS_CFG.read_text(encoding="utf-8"))
    if evidence_status:
        for sec in ("figures", "tables"):
            for spec in cfg_used.get(sec, []):
                spec["evidence_status"] = evidence_status
    fig_dir.mkdir(parents=True)
    cfg_p = fig_dir / "reporting_config_used.yaml"
    cfg_p.write_text(yaml.safe_dump(cfg_used, sort_keys=False), encoding="utf-8")
    fm = brf.build(cfg_p, fig_dir, root)
    tm = brt.build(cfg_p, tab_dir, root)
    return {"status": "BUILT", "version": key, "index": index, "figures": fm, "tables": tm}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validated runs -> tables -> figures -> provenance")
    ap.add_argument("--root", type=Path, default=REPO)
    ap.add_argument("--out-root", type=Path, default=None, help="default <root>/03_results")
    ap.add_argument("--allow-synthetic", action="store_true", help="QA only; refused for the official tree")
    ap.add_argument("--evidence-status", choices=["VALIDATED", "FROZEN"], default=None,
                    help="set only by a person after PRIMARY_RESULTS_VALIDATION; otherwise outputs stay preliminary")
    a = ap.parse_args(argv)
    res = run(a.root, a.out_root or a.root / "03_results", a.allow_synthetic, a.evidence_status)
    print(json.dumps({"status": res["status"], "version": res["version"],
                      "runs": res["index"][["run_dir", "status"]].to_dict("records")}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
