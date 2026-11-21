"""Append one authorized post-baseline change to POST_BASELINE_CHANGE_REGISTER.csv.

Hashes are computed, never typed: baseline_sha256 from the scope's baseline commit, authorized_sha256 from the STAGED
content (git index), so stage the change first. Existing rows are never recomputed or overwritten; a path that changes
again needs an explicit --supersede, which keeps the old row and marks it superseded.
Usage (repository root):
  python 03_results/maintenance/register_change.py KIND SCOPE PATH --issue L21 --rationale "..." [--supersede]
  KIND: ADD_PREFIX | ADD | MODIFY | DELETE    SCOPE: outside_v1 | v1
"""
import argparse
import hashlib
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "03_results/integrated_validation_v1/publication_q1/scripts"))
import scope_check  # noqa: E402

COLS = ["kind", "scope", "path", "baseline_commit", "baseline_sha256", "authorized_sha256", "issue", "rationale",
        "recorded", "superseded"]


def content_sha(spec):
    return hashlib.sha256(subprocess.run(["git", "show", spec], cwd=REPO, capture_output=True, check=True).stdout).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["ADD_PREFIX", "ADD", "MODIFY", "DELETE"])
    ap.add_argument("scope", choices=list(scope_check.SCOPES))
    ap.add_argument("path")
    ap.add_argument("--issue", required=True)
    ap.add_argument("--rationale", required=True)
    ap.add_argument("--supersede", action="store_true")
    a = ap.parse_args()
    reg_path = REPO / scope_check.REGISTER
    reg = pd.read_csv(reg_path, dtype=str).fillna("") if reg_path.exists() else pd.DataFrame(columns=COLS)
    live = reg[(reg.path == a.path) & (reg.scope == a.scope) & (reg.kind == a.kind) & (reg.superseded == "")]
    if len(live) and not a.supersede:
        sys.exit(f"{a.kind} {a.path} already registered; use --supersede to record a new authorized version")
    base = scope_check.SCOPES[a.scope]["base"]
    row = dict(kind=a.kind, scope=a.scope, path=a.path, baseline_commit=base, baseline_sha256="", authorized_sha256="",
               issue=a.issue, rationale=a.rationale, recorded=date.today().isoformat(), superseded="")
    if a.kind in ("MODIFY", "DELETE"):
        row["baseline_sha256"] = content_sha(f"{base}:{a.path}")
    if a.kind in ("MODIFY", "ADD"):
        row["authorized_sha256"] = content_sha(f":{a.path}")
    if len(live):
        reg.loc[live.index, "superseded"] = f"superseded {date.today().isoformat()}"
    reg = pd.concat([reg, pd.DataFrame([row])], ignore_index=True)[COLS]
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg.to_csv(reg_path, index=False, lineterminator="\n")
    print(row)


if __name__ == "__main__":
    main()
