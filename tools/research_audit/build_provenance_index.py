#!/usr/bin/env python3
"""
H2-PRISM read-only provenance index builder (Task A12 / F13 step 125 support -- Ahmed).

STATUS: IMPLEMENTED + TESTED (fixture-based). Walks the given directories, hashes
every file, and records the F13 provenance columns. Fields that cannot be determined
from the artifact itself (config_hash, manifest_hash, folds_hash, seed, script,
execution_status) are read from an optional sidecar ``<file>.provenance.json`` and are
otherwise written as UNKNOWN -- never inferred or backfilled.

Usage:
  python tools/research_audit/build_provenance_index.py --dirs 01_dataset_audit 03_results \
      --out 06_audit_preparation/PROVENANCE_INDEX.csv
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_artifacts import sha256_file  # noqa: E402

COLUMNS = ["output_file", "sha256", "git_commit", "config_hash", "manifest_hash", "folds_hash", "seed",
           "timestamp", "script", "execution_status", "notes", "git_tracked", "git_modified"]
SIDE_KEYS = ["config_hash", "manifest_hash", "folds_hash", "seed", "timestamp", "script", "execution_status", "notes"]


def _git(root: Path, *args: str) -> Optional[str]:
    try:
        r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:  # noqa: BLE001
        return None


def build_index(root: Path, dirs: List[str]) -> pd.DataFrame:
    commit = _git(root, "rev-parse", "HEAD") or "UNKNOWN"
    tracked = set((_git(root, "ls-files") or "").splitlines())
    modified = set((_git(root, "diff", "--name-only", "HEAD") or "").splitlines())
    rows = []
    for d in dirs:
        base = root / d
        if not base.exists():
            rows.append({**{c: "UNKNOWN" for c in COLUMNS}, "output_file": d, "sha256": "MISSING",
                         "notes": "directory not found"})
            continue
        for p in sorted(x for x in base.rglob("*") if x.is_file() and not x.name.endswith(".provenance.json")):
            rel = p.relative_to(root).as_posix()
            side = p.with_name(p.name + ".provenance.json")
            meta = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
            rec = {"output_file": rel, "sha256": sha256_file(p), "git_commit": commit,
                   "git_tracked": rel in tracked, "git_modified": rel in modified}
            for k in SIDE_KEYS:
                rec[k] = meta.get(k, "UNKNOWN")
            if not side.exists():
                rec["notes"] = "no provenance sidecar; generating run not recorded"
            rows.append(rec)
    return pd.DataFrame(rows, columns=COLUMNS)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", nargs="+", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--root", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    out = a.out.resolve()
    for d in a.dirs:
        if str(out).startswith(str((a.root / d).resolve())):
            raise SystemExit("refusing: output would be written inside an indexed directory")
    df = build_index(a.root, a.dirs)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, lineterminator="\n")
    print(f"indexed {len(df)} files -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
