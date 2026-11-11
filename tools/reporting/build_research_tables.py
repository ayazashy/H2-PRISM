#!/usr/bin/env python3
"""
H2-PRISM research table exporter (Task A13 -- Ahmed).

STATUS: IMPLEMENTED + TESTED (fixture-based). Selects and renames columns of saved
result tables; numeric values are copied unchanged into the CSV output (the Markdown
rendering only formats for display). Same routing and manifest rules as
build_research_figures.py. selective_risk without coverage is rejected.

Usage:
  python tools/reporting/build_research_tables.py --config configs/reporting_figures.yaml --out-dir 05_documentation/tables
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_research_figures as brf  # noqa: E402  (shared provenance helpers; one manifest mechanism)
from _common import ReportingInputError, classify, load_config, load_input, sha256_path  # noqa: E402


def to_markdown(df: pd.DataFrame, watermark: str, caption: str = "") -> str:
    """Display rendering only (the CSV keeps every value unchanged). Empty cells are distinguished:
    'n.e.' = row NOT_ESTIMABLE (no value exists), '—' = value undefined (e.g. risk with no SPECIFIC decision)."""
    head = [f"> **{watermark}**", ""] if watermark else []
    if caption:
        head += [f"*{caption}*", ""]
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        ne = "status" in df.columns and str(r.get("status")) not in ("ESTIMABLE", "nan", "None")
        cells = []
        for v in r.tolist():
            if pd.isna(v):
                cells.append("n.e." if ne else "—")
            elif isinstance(v, float):
                cells.append(f"{v:.3f}" if abs(v) < 1000 else f"{v:.0f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(head + lines) + "\n"


def build(config_path: Path, out_dir: Path, root: Path) -> pd.DataFrame:
    cfg, cfg_hash = load_config(config_path)
    rows: List[Dict] = []
    errors: List[str] = []
    commit = brf._git_commit(root)
    cmd = f"python tools/reporting/build_research_tables.py --config {brf._rel(config_path, root)} --out-dir {brf._rel(out_dir, root)}"
    for spec in cfg.get("tables", []):
        try:
            df = load_input(root, spec)
        except ReportingInputError as exc:
            errors.append(str(exc))
            rows.append({"table_id": spec.get("id"), "status": "NOT_BUILT_MISSING_EVIDENCE", "reason": str(exc)})
            continue
        cols = spec.get("columns") or list(df.columns)
        miss = [c for c in cols if c not in df.columns]
        if miss:
            errors.append(f"[{spec['id']}] columns not in input: {miss}")
            continue
        if "selective_risk" in cols and "coverage" not in cols:
            errors.append(f"[{spec['id']}] selective_risk selected without coverage (prohibited)")
            continue
        out = df[cols].rename(columns=spec.get("rename", {}))
        prov = brf._run_provenance(root / spec["input"])
        if "artifact_class" not in df.columns and prov["artifact_class"] != "UNKNOWN":
            df = df.assign(artifact_class=prov["artifact_class"])
        dest, wm = classify(spec, df)
        if brf._is_official(out_dir) and dest == "illustrative":
            errors.append(f"[{spec['id']}] synthetic/illustrative input refused for official output directory")
            rows.append({"table_id": spec["id"], "status": "REFUSED_SYNTHETIC_IN_OFFICIAL_RESULTS"})
            continue
        if brf._is_official(out_dir) and (prov.get("run_status") != "COMPLETED" or
                                         (prov.get("artifact_class") in brf.EXPERIMENT_CLASSES and not prov.get("run_authorized"))):
            errors.append(f"[{spec['id']}] incomplete or unauthorized source run refused for official output directory")
            rows.append({"table_id": spec["id"], "status": "REFUSED_INCOMPLETE_OR_UNAUTHORIZED_RUN"})
            continue
        d = out_dir / dest
        d.mkdir(parents=True, exist_ok=True)
        csv_p, md_p = d / f"{spec['id']}.csv", d / f"{spec['id']}.md"
        out.to_csv(csv_p, index=False, lineterminator="\n", float_format=None)
        md_p.write_bytes(to_markdown(out, wm, spec.get("caption", "")).encode("utf-8"))
        for p in (csv_p, md_p):
            rows.append({"table_id": spec["id"], "status": f"BUILT_{dest.upper()}", "reason": wm,
                         "output_file": brf._rel(p, root), "output_sha256": sha256_path(p),
                         "input_file": spec["input"], "input_sha256": sha256_path(root / spec["input"]),
                         "config_sha256": cfg_hash, "source_experiment": spec.get("source_experiment", "UNSPECIFIED"),
                         "evidence_status": spec.get("evidence_status", "UNDECLARED"), "caption": spec.get("caption", ""),
                         "n_rows": len(out), "n_rows_not_estimable": int((df["status"] != "ESTIMABLE").sum()) if "status" in df.columns else 0,
                         "script": "tools/reporting/build_research_tables.py", "command": cmd, "build_git_commit": commit, **prov})
    man = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in ("TABLE_BUILD_MANIFEST.csv", "TABLE_MANIFEST.csv"):
        man.to_csv(out_dir / name, index=False, lineterminator="\n")
    if errors and cfg.get("fail_on_missing", True):
        raise ReportingInputError("; ".join(errors))
    return man


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    try:
        build(a.config, a.out_dir, a.root)
    except ReportingInputError as exc:
        print(f"FAILED (mandatory evidence absent or invalid): {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
