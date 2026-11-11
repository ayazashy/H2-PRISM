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
                need = set(cols)
                if "status" in df.columns and (df["status"] != "ESTIMABLE").all():  # numeric columns cannot exist
                    need = {c for c in cols if c in df.columns or c in ("variant", "target", "mode", "status")}
                chk(f"columns:{name}", need <= set(df.columns), sorted(need - set(df.columns))[:5])
    if (d / "rq2.csv").exists() and (d / "rq2.csv").stat().st_size > 1:
        r = pd.read_csv(d / "rq2.csv")
        chk("rq2_shares_sum_to_one", ((r.specific + r.ambiguity_set + r.unresolved - 1).abs() < 1e-9).all())
    if (d / "rq1.csv").exists():
        r = pd.read_csv(d / "rq1.csv")
        rm = r[(r["mode"] == "rank_matched") & (r.status == "ESTIMABLE")]
        chk("rank_matched_coverage_matched", rm.empty or (rm.realized_coverage_a == rm.realized_coverage_b).all(),
            f"{len(rm)} estimable rank-matched comparisons")
    if (d / "predictions.parquet").exists():
        chk("unique_window_ids", pd.read_parquet(d / "predictions.parquet", columns=["window_id"]).window_id.is_unique)
    ok = all(c["ok"] for c in checks)
    # analysis name: the registered sensitivity name; a ROBUSTNESS_<realization> run is the clean_realization analysis
    analysis = (m.get("sensitivity") or {}).get("name") or (
        f"{d.name.split('_', 1)[1]}_realization" if d.name.startswith("ROBUSTNESS_") else "primary")
    # an executed run that stopped (manifest not COMPLETED) is INCOMPLETE, not a run whose outputs failed validation
    integrity = [c for c in checks if c["check"] in ("execution_class", "authorization_recorded", "protocol_config_is_pinned")]
    legit_stop = m.get("status") != "COMPLETED" and all(c["ok"] for c in integrity)
    status = "VALID" if ok else ("INCOMPLETE" if legit_stop else "INVALID")
    return {"run_dir": d.name, "run_key": m.get("run_key"), "artifact_class": cls, "analysis": analysis,
            "config_sha256": m.get("config_sha256"), "effective_config_sha256": m.get("effective_config_sha256"),
            "git_commit": m.get("git_commit"), "status": status,
            "n_checks": len(checks), "n_failed": sum(not c["ok"] for c in checks), "checks": checks}


def results_provenance(runs: Path, root: Path, vals: List[Dict]) -> pd.DataFrame:
    """F13 RESULTS_PROVENANCE: one row per file of every recorded run (validated runs and archived invalid runs),
    with the F13 provenance columns filled from that run's manifest (never inferred)."""
    sys.path.insert(0, str(REPO / "tools" / "research_audit"))
    from build_provenance_index import COLUMNS  # noqa: E402
    status = {v["run_dir"]: v["status"] for v in vals}
    try:
        import subprocess
        tracked = set(subprocess.run(["git", "ls-files", "03_results"], cwd=root, capture_output=True, text=True).stdout.split())
    except Exception:  # noqa: BLE001
        tracked = set()
    rows = []
    for man_p in sorted(runs.rglob("run_manifest.json")):
        d = man_p.parent
        if d.name == "SENSITIVITY_SUMMARY" or "folds" in d.parts:
            continue
        m = json.loads(man_p.read_text(encoding="utf-8"))
        ins = m.get("input_sha256") or {}
        archived = "archive" in d.relative_to(runs).parts
        ex = (f"{m.get('status')}|ARCHIVED_INVALID" if archived else f"{m.get('status')}|{status.get(d.name, 'NOT_VALIDATED')}")
        for f in sorted(p for p in d.rglob("*") if p.is_file()):
            rel = f.relative_to(root).as_posix()
            rows.append({"output_file": rel, "sha256": _sha(f), "git_commit": m.get("git_commit"),
                         "config_hash": m.get("config_sha256"), "manifest_hash": ins.get("manifest"),
                         "folds_hash": ins.get("outer_folds"), "seed": m.get("seed"), "timestamp": "UNKNOWN",
                         "script": "tools/experiments/run_primary_protocol.py", "execution_status": ex,
                         "notes": f"{m.get('artifact_class')}|{(m.get('sensitivity') or {}).get('name', 'primary')}|run_key {str(m.get('run_key'))[:12]}"
                                  f"|code {str(m.get('code_sha256'))[:12]}|effective_config {str(m.get('effective_config_sha256'))[:12]}",
                         "git_tracked": rel in tracked, "git_modified": False})
    return pd.DataFrame(rows, columns=COLUMNS)


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
    results_provenance(runs, root, vals).to_csv(out_root / "RESULTS_PROVENANCE.csv", index=False, lineterminator="\n")
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
    others = sorted(str(v["run_key"]) for v in vals if v["status"] == "VALID" and v["run_dir"] != "PRIMARY")
    if others:  # a new set of validated secondary runs is a new version (earlier versions are kept unchanged)
        key += "_s" + hashlib.sha256("|".join(others).encode()).hexdigest()[:8]
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
