"""L22 repair: record the rename of quality_control/FIGURE_MANIFEST.csv -> Q1_FIGURE_MANIFEST.csv and refresh SHA256SUMS.

Why: tests/test_figure_system.py treats every 03_results/**/FIGURE_MANIFEST.csv as a figure-system manifest (status and
artifact_class columns). This package's Q1 QA manifest (added in e944e1b) used that file name with a different schema.
The file is renamed with its bytes unchanged; no figure, table or result is regenerated.

Writes (quality_control/):
  MANIFEST_RENAME_RECORD.csv   old and new path, SHA-256 and git blob before/after, byte counts, identity flag
  CHECKSUM_CHANGES_L22.csv     every SHA256SUMS.csv row that differs from the pre-repair commit (path, old, new, change)
and rewrites SHA256SUMS.csv with the same algorithm as verify_package.py. NUMERICAL_VERIFICATION.csv is not touched.
Usage (repository root): python .../migrate_l22_manifest_name.py --base <pre-repair commit>
"""
import argparse
import hashlib
import io
import subprocess
from pathlib import Path

import pandas as pd

Q1 = Path(__file__).resolve().parents[1]
ROOT = Q1.parent
REPO = ROOT.parents[1]
OLD = "03_results/integrated_validation_v1/publication_q1/quality_control/FIGURE_MANIFEST.csv"
NEW = "03_results/integrated_validation_v1/publication_q1/quality_control/Q1_FIGURE_MANIFEST.csv"
SELF = "publication_q1/quality_control/CHECKSUM_CHANGES_L22.csv"


def git_bytes(spec):
    return subprocess.run(["git", "show", spec], cwd=REPO, capture_output=True, check=True).stdout


def git(*a):
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="commit before the repair")
    a = ap.parse_args()
    base = git("rev-parse", "--short", a.base)
    old_b, new_b = git_bytes(f"{a.base}:{OLD}"), (REPO / NEW).read_bytes()
    assert old_b == new_b, "renamed manifest must be byte-identical to the original"
    qc = Q1 / "quality_control"
    pd.DataFrame([dict(old_path=OLD, new_path=NEW, old_sha256=sha(old_b), new_sha256=sha(new_b), bytes_old=len(old_b),
                       bytes_new=len(new_b), byte_identical=old_b == new_b, old_git_blob=git("rev-parse", f"{a.base}:{OLD}"),
                       new_git_blob=git("hash-object", NEW), introduced_in="e944e1b", repaired_from=base,
                       reason="figure-system test globs FIGURE_MANIFEST.csv and requires status/artifact_class; Q1 QA "
                              "manifest has another schema (risk register L22)",
                       scientific_content_changed=False)]).to_csv(qc / "MANIFEST_RENAME_RECORD.csv", index=False, lineterminator="\n")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv" and "__pycache__" not in p.parts)
    old_sums = pd.read_csv(io.BytesIO(git_bytes(f"{a.base}:03_results/integrated_validation_v1/SHA256SUMS.csv"))).set_index("path")
    new_sums = {p.relative_to(ROOT).as_posix(): (sha(p.read_bytes()), p.stat().st_size) for p in files}
    rows = []
    for path in sorted(set(old_sums.index) | set(new_sums)):
        if path == SELF:
            continue
        o = old_sums.sha256.get(path)
        n = new_sums.get(path, (None,))[0]
        if o != n:
            kind = "renamed from" if path.endswith("Q1_FIGURE_MANIFEST.csv") else "renamed to" if path.endswith("/FIGURE_MANIFEST.csv") \
                else "added" if o is None else "removed" if n is None else "content changed"
            rows.append(dict(path=path, old_sha256=o or "", new_sha256=n or "", change=kind))
    pd.DataFrame(rows).to_csv(qc / "CHECKSUM_CHANGES_L22.csv", index=False, lineterminator="\n")
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.csv" and "__pycache__" not in p.parts)
    pd.DataFrame({"path": [p.relative_to(ROOT).as_posix() for p in files], "sha256": [sha(p.read_bytes()) for p in files],
                  "bytes": [p.stat().st_size for p in files]}).to_csv(ROOT / "SHA256SUMS.csv", index=False, lineterminator="\n")
    print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
