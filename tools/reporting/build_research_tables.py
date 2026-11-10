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
from _common import ReportingInputError, classify, load_config, load_input, sha256_path  # noqa: E402


def to_markdown(df: pd.DataFrame, watermark: str) -> str:
    head = [f"> **{watermark}**", ""] if watermark else []
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join("" if pd.isna(v) else (f"{v:.4g}" if isinstance(v, float) else str(v))
                                       for v in r.tolist()) + " |")
    return "\n".join(head + lines) + "\n"


def build(config_path: Path, out_dir: Path, root: Path) -> pd.DataFrame:
    cfg, cfg_hash = load_config(config_path)
    rows: List[Dict] = []
    errors: List[str] = []
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
        dest, wm = classify(spec, df)
        d = out_dir / dest
        d.mkdir(parents=True, exist_ok=True)
        csv_p, md_p = d / f"{spec['id']}.csv", d / f"{spec['id']}.md"
        out.to_csv(csv_p, index=False, lineterminator="\n", float_format=None)
        md_p.write_text(to_markdown(out, wm), encoding="utf-8")
        for p in (csv_p, md_p):
            rows.append({"table_id": spec["id"], "status": f"BUILT_{dest.upper()}", "reason": wm,
                         "output_file": p.as_posix(), "output_sha256": sha256_path(p),
                         "input_file": spec["input"], "input_sha256": sha256_path(root / spec["input"]),
                         "config_sha256": cfg_hash, "source_experiment": spec.get("source_experiment", "UNSPECIFIED"),
                         "evidence_status": spec.get("evidence_status", "UNDECLARED")})
    man = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    man.to_csv(out_dir / "TABLE_BUILD_MANIFEST.csv", index=False, lineterminator="\n")
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
